from cmd import Cmd
import json
from os import path
import shlex
import signal
import time
from uber import UberClient, geolocate, ClientStatus, UberException
from uber.model_base import Model, StringField
import sys


def exempt_login(func):
    """
    marks a command as login-free
    """
    func.exempt_login = True
    return func


class UberCli(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self._state = CliState()
        self._client = None
        self.setup_client()

        if self._client:
            print 'logged in as ' + self._state.username

    def setup_client(self):
        if self._state.token:
            self._client = UberClient(self._state.username, self._state.token)

    @exempt_login
    def do_login(self, username, password):
        """
        Logs into Uber.
        usage: login <email> <password>
        """
        try:
            token = UberClient.login(username, password)
            self._state.username = username
            self._state.token = token
            self._state.save()

            self.setup_client()
            print 'login ok'
        except UberException as e:
            print e.description

    @exempt_login
    def do_logout(self):
        """
        Log out of Uber (just deletes the token)

        usage: logout
        """
        self._state.token = None
        self._state.save()
        self._state = None
        print 'Cleared access token'

    @exempt_login
    def do_lookup(self, address):
        """
        Looks up an address
        usage: lookup <address>
        """
        result = geolocate(address)
        for entry in result:
            print entry['formatted_address']

    def do_add_credit_card(self, creditcard, month, year, cvv, zipcode):
        """
        Adds a credit card to Uber
        usage: add_credit_card <creditcard> <month> <year> <cvv> <zipcode>
        """
        result = self._client.add_payment(creditcard, month, year, cvv, zipcode)
        print result

    def do_ping(self, address_str):
        """
        shows you what taxis are close to you.
        Usage: ping <address>
        """
        if not address_str:
            print

        results = geolocate(address_str)
        if not results:
            print 'address not found :('
            return

        geodecoded_address = results[0]

        print 'pinging: ' + geodecoded_address['formatted_address']
        app_state = self._client.ping(geodecoded_address)
        city = app_state.city
        vehicle_views = city.vehicle_views
        for key in city.vehicle_views_order:
            nearby_info = app_state.nearby_vehicles.get(key)
            view = vehicle_views[key]
            count = len(nearby_info.vehicle_paths)

            if count:
                additional_info = ''
                if view.surge:
                    additional_info = 'Warning - x{multiplier} surge pricing is active!'.format(multiplier=view.surge.multiplier)

                print '{name} has {count} cars near by (eta {eta}). {additional_info}'.format(
                    name=view.description,
                    count=len(nearby_info.vehicle_paths),
                    eta=nearby_info.eta_string,
                    additional_info=additional_info
                    )
            else:
                print '{name} has no vehicles nearby :('.format(name=view.description)

    def do_pickup(self, address):
        """
        Have an UberX pick you up
        Usage: pickup <address>
        """
        results = geolocate(address)
        if not results:
            print 'address not found :('
            return

        if len(results) == 1:
            geo_address = results[0]
        else:
            for i in xrange(len(results)):
                entry = results[i]
                print '{index}) {entry}'.format(
                    index=i + 1,
                    entry=entry['formatted_address']
                )

            print ''

            selection_num = int(raw_input('choose address# (0 to abort)> ') or 0)
            if not selection_num:
                return

            geo_address = results[selection_num - 1]

        print 'booking UberX for {}...'.format(geo_address['formatted_address'])
        self._book_ride(geo_address)

    def _book_ride(self, location):
        abort_signal = []

        def handle_abort(*args):
            abort_signal.append(None)
            print ''
            print 'cancelling ride...'
            self._client.cancel_pickup()
            print 'ride cancelled.'
            signal.signal(signal.SIGINT, signal.SIG_DFL)

        signal.signal(signal.SIGINT, handle_abort)
        self._client.request_pickup(location)

        print_state = True
        last_status = None
        print 'waiting for ride (ctrl+c at any time to cancel ride)'

        while print_state and not abort_signal:
            state = self._client.ping(None)
            status = state.client.status
            if status != last_status:
                print 'status: ' + status
                last_status = status

            if status == ClientStatus.LOOKING:
                print state.client.last_request_note
                break

            if status == ClientStatus.WAITING_FOR_PICKUP:
                trip = state.trip
                vehicle = trip.vehicle
                sys.stdout.write("\r{driver} will pick you up in {eta} with a {color} {make} {model}.".format(
                    driver=trip.driver.name,
                    eta=trip.eta_string_short,
                    color=vehicle.exterior_color,
                    make=vehicle.vehicle_type.make,
                    model=vehicle.vehicle_type.model,
                ))
                sys.stdout.flush()

            time.sleep(1)

    def do_experiments(self):
        """
        print uber's running experiments
        """
        state = self._client.ping(None)
        for experiment in state.client.active_experiments.values():
            print '{name} ({group})'.format(name=experiment.name, group=experiment.treatment_group_name)

    @exempt_login
    def do_exit(self):
        exit()

    do_bye = do_exit

    def onecmd(self, line):
        """
        Interpret the argument as though it had been typed in response
        to the prompt.
        """
        if line == 'EOF':
            exit()

        built_in_functions = ['help']
        cmd, arg, line = self.parseline(line)

        if not line:
            return self.emptyline()

        if cmd is None:
            return self.default(line)

        self.lastcmd = line
        if cmd == '':
            return self.default(line)

        try:
            func = getattr(self, 'do_' + cmd)
        except AttributeError:
            return self.default(line)

        if cmd in built_in_functions:
            return func(arg)

        if getattr(func, 'exempt_login', False) is False and not self._client:
            print '''login required. type 'login <user> <password>' to login'''
            return

        arg_count = func.func_code.co_argcount - 1

        # if one arg, just give the string as-is
        if arg_count == 1:
            if not arg:
                print get_usage(func)
                return

            return func(arg)

        else:
            # split to various args
            split_args = shlex.split(arg)
            if len(split_args) != arg_count:
                print get_usage(func)
                return

            return func(*split_args)


class CliState(Model):
    """
    keeps track of username & token
    """
    FILENAME = path.join(path.expanduser('~'), '.ubercli.json')

    username = StringField('username', writeable=True)
    token = StringField('token', writeable=True, optional=True)

    def __init__(self):
        super(CliState, self).__init__()
        self.load()

    def load(self):
        if path.exists(self.FILENAME):
            self._data = json.load(open(self.FILENAME))
        else:
            self._data = {}

    def save(self):
        json.dump(self._data, open(self.FILENAME, 'w'))


def get_usage(func):
    if not func.__doc__:
        return ''

    all_lines = [x.strip() for x in func.__doc__.split('\n')]
    for i in xrange(len(all_lines)):
        if all_lines[i].lower().startswith('usage:'):
            return '\n'.join(all_lines[i:])

    return '\n'.join(all_lines)


def main():
    print "Welcome to UberCLI! Type 'help' for help"
    cli = UberCli()
    cli.cmdloop()

if __name__ == '__main__':
    main()
