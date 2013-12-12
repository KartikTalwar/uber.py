
uber.py - a Python client for [Uber]
------------------------------------
[![ubercli](http://tals.github.io/uber.py/images/ubercli.gif)](https://github.com/tals/uber.py/blob/master/examples/ubercli.py)


[![Build Status](https://secure.travis-ci.org/tals/uber.py.png?branch=master)](http://travis-ci.org/tals/uber.py)


Usage example:
```python
from uber import UberClient
token = UberClient.login('tal@test.org', 'my_password')
client = UberClient('tal@test.org', token)

app_state = client.request_pickup('182 Howard St, San Francisco')
```

Rationale
---------
Right now we're in this weird stage where we have services that are insanely popular, yet lack even the most
basic of APIs.

That kinda sucks. Let's change that.

This library strives to act as a reference for other libraries, and expose as much functionality of the API as possible.

Design
------
Uber's clients are mostly stateless - for every request done against the server, Uber always returns the FULL STATE of the
app, with things like "what to put in the bottom bar", "is there a ride in progress" etc.

Since this is a Python library, and will typically be used in server/CLI environments, things that would normally be
queried by external systems (GPS location) are passed EXPLICITLY as arguments, rather than being queried via some callback.
Sadly it makes the API less convenient to use.

It would be really cool to have a "pleasant" client on top of this low-level one (e.g. have add_credit_card() return the payment
profile rather than the whole state, etc). Pull-requests are welcome :)

Supported features
----------------------------
- Order and cancel a ride
- Add/remove credit/debit cards
- See the drivers in the area


Support
-------
- Python 2.7
- PyPy

Installation
-------------
```
$ pip install uber.py
```

Usage
=====

Examples
--------
- examples/ubercli.py: a fairly complete example that shows you how to ping, get a ride and cancel it.


Authenticating a user
--------------------------
```python
from uber import UberClient
token = UberClient.login('tal@test.org', 'my_password')
>> token
'my_token'
```

Getting the app state
---------------------
```python
client = UberClient('tal@test.org', 'my_token')
app_state = client.ping()

>>> print app_state.nearby_vehicles[UberCarType.UBERX]
<class 'uber.models.NearbyVehicles'>
    vehicle_paths: {
        d2c0de3b-907f-49a4-8be8-756b8a2049bd:	[
            <class 'uber.models.VehicleLocation'>
                course: -140
                epoch: 2013-12-06 04:49:46.996000,
            <class 'uber.models.VehicleLocation'>
                course: -140
                epoch: 2013-12-06 04:50:00.995000,
            ...
        ]
        4b035b27-1544-44d5-93ea-7b3d6d33717a:	[
            <class 'uber.models.VehicleLocation'>
                course: 170
                epoch: 2013-12-06 04:49:34.148000,
            ...
        ]
    ...
    }
    min_eta: 1
    eta_string: u'1 minute'
    eta_string_short: u'1 min'

```

Getting a ride
--------------
```python
from uber import geolocate, UberVehicleType
geo_address = geolocate('182 Howard St, San Francisco')
app_state = client.request_pickup(geo_address, UberVehicleType.UBERX)
```

Canceling
---------
```python
client.cancel_pickup()
```

Payments
--------
```python
state = client.add_payment('1111222233334444', '01', '99', '123', '94111', 'US')
>>> state.client.payment_profiles
[
    <class 'uber.models.PaymentProfile'>
        card_type: u'Visa'
        id: 123456
        card_expiration: 2099-01-01 00:00:00+00:00
        use_case: u'personal'
        card_number: u'4444'
]

client.delete_payment_profile(123456)
```

Checking for surge rates
------------------------
```python
for view in state.city.vehicle_views.values():
    if view.surge:
        print '{name} has x{multiplier} surge rate'.format(
            name=view.description,
            multiplier=view.surge.multiplier)
```

FAQ
===
Q: What?  
A: I was told by someone that I should have some projects on my Github account, so I figured that I might as well make
something cool

Q: Will I get banned for using this?  
A: Maybe! I hope not. As it stands right now, Uber *CAN* tell this library apart from their official apps, as it makes
no effort to look the same as them (It omits some fields, does not implement the caching mechanism etc).

Q: What's missing?  
A: bunch of stuff:
- Feeding events to Uber's analytics system (see ```UberClient.Events``` & ```UberClient._send_event```)
- Driver's side
- Leaving feedback
- PayPal integration

Q: What about Lyft/Sidecar/Flywheel/omg there are so many of these  
A: I've written a library for Lyft, but I'm sitting on it for now as I want to gauge interest first (plus I don't want
to get banned from Lyft).
About the others - I honestly don't use them at all, but we'll see!

Q: Anything else?  
A: I'll buy a cookie to the first person who will write a Twilio-Uber mashup that lets people order Uber with a text.
What's cool about it is that it will allow people with feature phones to use Uber.
I was thinking of something like:
```
>> Pickup UberX 182 Howard St, San Francisco
<< Scheduling a pickup to 182 Howard Street, San Francisco, CA 94105, USA
<< John will pick you up in 5 mins with a green Toyota Prius.
>> ping
<< John will pick you up in 2 mins with a green Toyota Prius.
>> cancel
<< ride has been cancelled.
```

[Uber]: https://www.uber.com/
