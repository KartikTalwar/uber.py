from datetime import datetime
import unittest
from dateutil.tz import tzutc
from uber import VehicleLocation, Image, Fare, Trip, TripState
from uber.client import *


class TestModels(unittest.TestCase):
    def test_vehicle_location(self):
        location = VehicleLocation({"epoch": 1384233249575,
                                    "latitude": 37.76062,
                                    "longitude": -122.40647,
                                    "course": 180})
        self.assertEqual(location.epoch, datetime.utcfromtimestamp(1384233249575 / 1000.0))
        self.assertEqual(location.latitude, 37.76062)
        self.assertEqual(location.longitude, -122.40647)
        self.assertEqual(location.course, 180)

    def test_image(self):
        model = Image({
            "url": "http://d1a3f4spazzrp4.cloudfront.net/car-types/map/map-black.png",
            "width": 30,
            "height": 70
        })
        self.assertEqual(model.url, 'http://d1a3f4spazzrp4.cloudfront.net/car-types/map/map-black.png')
        self.assertEqual(model.width, 30)
        self.assertEqual(model.height, 70)

    def test_fare(self):
        d = {'speedThresholdMps': 5,
             'base': '$7',
             'perMinute': '$1.05',
             'perDistanceUnit': '$4',
             'distanceUnit': 'mile',
             'type': 'TimeOrDistance',
             'minimum': '$15',
             'id': 33,
             'cancellation': '$10'
        }

        model = Fare(d)
        self.assertEquals(model.speed_threshold_mps, 5)
        self.assertEquals(model.base, '$7')
        self.assertEquals(model.per_minute, '$1.05')
        self.assertEquals(model.per_distance_unit, '$4')
        self.assertEquals(model.distance_unit, 'mile')
        self.assertEquals(model.type, 'TimeOrDistance')
        self.assertEquals(model.minimum, '$15')
        self.assertEquals(model.id, 33)
        self.assertEquals(model.cancellation, '$10')

    def test_vehicle_view(self):
        d = {"id": 1,
             "description": "Black Car",
             "capacity": 4,
             "maxFareSplits": 4,
             "mapImages": [{
                               "url": "http://d1a3f4spazzrp4.cloudfront.net/car-types/map/map-black.png",
                               "width": 30,
                               "height": 70
                           }],
             "monoImages": [{
                                "url": "http://d1a3f4spazzrp4.cloudfront.net/car-types/mono/mono-black.png",
                                "width": 114,
                                "height": 34
                            }],
             "pickupButtonString": "Set pickup location",
             "confirmPickupButtonString": "Request pickup here",
             "requestPickupButtonString": "Request {string}",
             "setPickupLocationString": "Set Pickup Location",
             "pickupEtaString": "Pickup time is approximately {string}",
             "fare": {
                 "id": 33,
                 "base": "$7",
                 "perDistanceUnit": "$4",
                 "distanceUnit": "mile",
                 "perMinute": "$1.05",
                 "speedThresholdMps": 5,
                 "minimum": "$15",
                 "cancellation": "$10",
                 "type": "TimeOrDistance"
             },
             "fareDetailsUrl": None,
             "allowFareEstimate": True,
             "noneAvailableString": "no black cars available"
        }

        model = VehicleView(d)
        self.assertEqual(model.id, 1)
        self.assertEqual(model.description, "Black Car")
        self.assertEqual(model.capacity, 4)
        self.assertEqual(model.max_fare_splits, 4)
        self.assertEqual(model.allow_fare_estimate, True)
        self.assertEqual([x.raw for x in model.map_images], d['mapImages'])
        self.assertEqual([x.raw for x in model.mono_images], d['monoImages'])
        self.assertEqual(model.fare.raw, d['fare'])

    def test_payment_profile(self):
        d = {
            u'accountName': 'lol',
            u'billingCountryIso2': 'US',
            u'cardExpiration': u'2016-02-01T00:00:00+00:00',
            u'cardNumber': u'1111',
            u'cardType': u'Visa',
            u'id': 11223344,
            u'tokenType': 'braintree',
            u'useCase': u'personal'
        }

        model = PaymentProfile(d)
        self.assertEquals(model.billing_country_iso2, 'US')
        self.assertEquals(model.card_type, 'Visa')
        self.assertEquals(model.card_number, '1111')
        self.assertEquals(model.token_type, 'braintree')
        self.assertEquals(model.card_expiration, datetime(2016, 2, 1, 0, 0, tzinfo=tzutc()))
        self.assertEquals(model.id, 11223344)
        self.assertEquals(model.use_case, 'personal')
        self.assertEquals(model.account_name, 'lol')

    def test_trip(self):
        d = {
            'dispatchPercent': 0.1,
            'paymentProfileId': 1252863,
            'pickupLocation': {'aaa': 'bbb'},
            'useCredits': True
        }

        model = Trip(d)
        self.assertEqual(model.dispatch_percent, 0.1)
        self.assertEqual(model.pickup_location, {'aaa': 'bbb'})
        self.assertEqual(model.state, TripState.DISPATCHING)

        d = {
            'driver': {'a': 'b'},
            'eta': 5
        }
        model = Trip(d)
        self.assertEqual(model.state, TripState.DRIVING_TO_PICKUP)
        self.assertEqual(model.eta, 5)
        self.assertEqual(model.driver.raw, {'a': 'b'})

if __name__ == '__main__':
    unittest.main()
