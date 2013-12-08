"""
Client for Uber.
"""

import json
from time import time
import requests
import random
from uber import settings
from uber import geolocation
from uber.models import AppState, PaymentProfile, VehicleView, Place, SimpleLocation


class UberClient(object):
    ENDPOINT = 'https://cn{}.uber.com'.format(random.randint(1, 10))

    def __init__(self, username, token):
        self._email = username
        self._token = token
        self._headers = {
            'Content-Type': 'application/json',
            'User-Agent': settings.USER_AGENT,
            'Accept-Language': 'en-US',
        }

        self._session = requests.session()

    def _validate_message_response(self, data):
        """
        checks the message response for errors and raise exceptions accordingly
        """
        if data['messageType'] == 'Error':
            raise UberException(data['description'], error_code=data.get('errorCode'))

    def _validate_http_response(self, response):
        """
        checks http response for errors and raise exceptions accordingly
        """
        if not response.ok:
            raise UberException(response.text, response.status_code)

    @classmethod
    def login(cls, email, password):
        """
        Login into Uber

        Returns:
            - a token string
        """
        uber_client = UberClient(email, None)

        data = {
            "password": hash_password(password),
            "email": email,
        }

        response = uber_client._send_message(MessageTypes.LOGIN, params=data)
        return response['token']

    def _post(self, endpoint, data):
        """
        posts a json to the given endpoint
        """
        response = self._session.post(endpoint, json.dumps(data), headers=self._headers)
        self._validate_http_response(response)

        return response

    def _send_message(self, message_type, params=None, location=None):
        """
        sends a message to uber.

        Args:
            - message_type: string of the message
            - location: (optional) GPSLocation or any object that has longitude & latitude attributes
        """

        data = {
            'messageType': message_type,
            'epoch': get_epoch(),
            'version': settings.UBER_VERSION,
            'language': 'en',
            'app': 'client',
            'email': self._email,
            'deviceModel': settings.DEVICE_MODEL,
            'deviceOS': settings.DEVICE_OS,
            'device': settings.DEVICE_NAME
        }

        if self._token:
            data['token'] = self._token

        self._copy_location_for_message(location, data)

        if params:
            data.update(params)

        response = self._post(self.ENDPOINT, data)

        data = response.json()
        self._validate_message_response(data)

        return data

    def _send_event(self, event_name, location, params):
        """
        Feeds Uber's event system and keeps Uber happy.
        Currently unused :P
        """
        data = {
            'epoch': get_epoch(),
            'version': settings.UBER_VERSION,
            'language': 'en',
            'app': 'client',
            'email': self._email,
            'deviceModel': settings.DEVICE_MODEL,
            'deviceOS': settings.DEVICE_OS,
            'device': settings.DEVICE_NAME,
            'parameters': params,
            'eventName': event_name,
        }

        self._post('http://events.uber.com/mobile/event/', data=data)

    @classmethod
    def _copy_location_for_message(cls, location, data):
        """
        Copies a location to the given data dict, as per the message specs
        """
        if location:
            if isinstance(location, dict):
                location = SimpleLocation(location)

            data['latitude'] = location.latitude
            data['longitude'] = location.longitude

            if getattr(location, 'altitude', None):
                data['altitude'] = location.altitude

            if getattr(location, 'vertical_accuracy', None):
                data['verticalAccuracy'] = location.vertical_accuracy

            if getattr(location, 'horizontal_accuracy', None):
                data['horizontalAccuracy'] = location.horizontal_accuracy

    def _api_command(self, api_method, api_url, api_params):
        params = {
            'apiMethod': api_method,
            'apiParameters': api_params,
            'apiUrl': api_url
        }

        result = self._send_message(MessageTypes.API_COMMAND, params)
        self._validate_api_call_response(result)

        return AppState(result)

    def _validate_api_call_response(self, result):
        error = result['apiResponse'].get('error')
        if error:
            raise UberException(error['message'], error['statusCode'])

    def delete_payment_profile(self, payment_profile):
        """
        deletes a payment profile
        """
        if isinstance(payment_profile, PaymentProfile):
            payment_profile = payment_profile.id

        url = '/payment_profiles/{}'.format(payment_profile)
        params = {
            'token': self._token,
            '_LOCALE_': 'en',
            'epoch': get_epoch(),
        }

        return self._api_command(ApiMethods.DELETE, url, params)

    def add_payment(self, card_number, expiration_month, expiration_year, cvv, zipcode, billing_country_iso2="US"):
        """
        add a credit card to Uber.

        """

        import braintree
        bt = braintree.Braintree(settings.BRAINTREE_PRODUCTION_KEY)

        url = '/payment_profiles'
        params = {
            'card_number': bt.encrypt(card_number),

            # interestingly enough, these 3 are available unencrypted in the payments_profiles
            'card_expiration_month': bt.encrypt(expiration_month),
            'card_expiration_year': bt.encrypt(expiration_year),
            'billing_zip': str(zipcode),

            'card_code': bt.encrypt(str(cvv)),
            'billing_country_iso2': billing_country_iso2,
            'use_case': 'personal',
            'token': self._token,
            '_LOCALE_': 'en',
            'epoch': get_epoch(),
        }

        return self._api_command(ApiMethods.POST, url, params)

    def nearby_places(self, query, location):
        """
        queries uber for nearby locations. Currently powered by foursquare
        """
        params = {
            'searchTypes': ['places'],
            'query': query
        }

        response = self._send_message(MessageTypes.LOCATION_SEARCH, params=params, location=location)
        return [Place(x) for x in response['places']]

    def ping(self, location):
        """
        'pings' uber and returns the state of the world. (nearby cars, pricing etc)
        """
        return AppState(self._send_message(MessageTypes.PING_CLIENT, location=location))

    def request_pickup(self, vehicle_type, pickup_address, gps_location=None, payment_profile=None, use_credits=True):
        """
        request an uber pickup.

        Args:
            - vehicle_type: an id or a VehicleView instance of the ride you want
            - pickup_address: geo-coded location or a string (if you're feeling frisky!)
            - current_location: gps coords
            - payment_profile: (optional) a payment profile id or an instance of PaymentProfile

        Returns:
            - app_state

        To examine ride status, check the following:
        """
        if isinstance(vehicle_type, VehicleView):
            vehicle_type = vehicle_type.id

        if isinstance(payment_profile, PaymentProfile):
            payment_profile = payment_profile.id

        if isinstance(pickup_address, basestring):
            search_result = geolocation.geolocate(pickup_address)
            if not search_result:
                raise UberLocationNotFound(u"Can't find location " + unicode(pickup_address))

            pickup_address = search_result[0]

        params = {
            'pickupLocation': pickup_address,
            'useCredits': use_credits,
            'vehicleViewId': int(vehicle_type),
        }

        if payment_profile:
            params['paymentProfileId'] = int(payment_profile)

        response = self._send_message('Pickup', params=params, location=gps_location)
        return AppState(response)

    def cancel_pickup(self, location=None):
        """
        cancels current ride
        """
        return AppState(self._send_message('PickupCanceledClient', location=location))


def hash_password(password):
    """
    hash the password, Uber-style.

    How it works:
        - for each character, calculate its md5 and hexify it.
        - concat all of hexified hashes together
        - lowercase it
        - calculate md5 on the concatted buffer.
        - lowercase it
    """
    from hashlib import md5

    password = password.encode('utf8')
    buff = ''.join([md5(x).hexdigest() for x in password])
    return md5(buff).hexdigest()


class Events(object):
    """
    event types that get submitted to Uber's analytics system
    """

    # "locationAltitude": 11.05551147460938,
    # "locationVerticalAccuracy": 8,
    # "requestGuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    # "locationHorizontalAccuracy": 5
    SIGNIN_REQUEST = 'SignInRequest'

    # "clientId": 123456,
    # "vehicleViewIds": [8],
    # "reason": "ping",
    # "vehicleViewId": 8,
    # "locationAltitude": 12.00814819335938,
    # "locationVerticalAccuracy": 8,
    # "requestGuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    # "locationHorizontalAccuracy": 10,
    # "sessionHash": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    NEAREST_CAB_REQUEST = 'NearestCabRequest'

    MESSAGE_DISMISS = 'MessageDismiss'
    CONFIRM_PAGE_VIEW = 'ConfirmPageView'
    REQUEST_VEHICLE_RESPONSE = 'RequestVehicleResponse'

    # "clientId": 1234567,
    # "locationHorizontalAccuracy": 10,
    # "locationVerticalAccuracy": 8,
    # "locationAltitude": 12.00814819335938,
    # "requestGuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    # "latency": 0.5161130428314209,
    # "statusCode": 200,
    # "sessionHash": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    CANCEL_TRIP_RESPONSE = 'CancelTripResponse'


class MessageTypes(object):
    LOCATION_SEARCH = 'LocationSearch'
    PING_CLIENT = 'PingClient'
    LOGIN = 'Login'
    API_COMMAND = 'ApiCommand'


class ApiMethods(object):
    DELETE = 'DELETE'
    POST = 'POST'


class UberException(Exception):
    def __init__(self, description, error_code=None, **kwargs):
        super(Exception, self).__init__(description)
        self.description = description
        self.error_code = error_code
        self.__dict__.update(kwargs)


def get_epoch():
    return int(time() * 1000)


class UberLocationNotFound(UberException):
    pass
