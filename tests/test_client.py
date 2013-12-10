import json
import unittest
from tests import DictPartialMatcher
from uber import UberClient, GPSLocation, UberException, Place, VehicleView, SimpleLocation, UberLocationNotFound, PaymentProfile
from flexmock import flexmock
import uber.client
from uber import settings
from tests import mocked_response
from uber import geolocation
class TestUberClient(unittest.TestCase):
    mock_location = GPSLocation(1, 2)

    def setUp(self):
        self._client = UberClient('test@test.org', '12345')

    def test_post(self):
        data = {'a': 'b'}

        (flexmock(self._client._session)
         .should_receive('post')
         .with_args('http://www.boo.org', json.dumps(data), headers=self._client._headers)
         .and_return(mocked_response({'aaa': 'bbb'}))
         .times(1)
        )

        self.assertEqual(self._client._post('http://www.boo.org', data=data).json(), {'aaa': 'bbb'})

    def test_message_error_handling(self):
        error_data = {
            'messageType': 'Error',
            'description': 'something bad',
            'errorCode': 12345,
        }

        (flexmock(self._client._session)
         .should_receive('post')
         .and_return(mocked_response(error_data))
         .times(1)
        )

        with self.assertRaises(UberException) as expected_exception:
            self._client._send_message('crap')

        self.assertEqual(expected_exception.exception.description, 'something bad')
        self.assertEqual(expected_exception.exception.error_code, 12345)

    def test_http_error_handling(self):
        (flexmock(self._client._session)
         .should_receive('post')
         .and_return(mocked_response('error!', 401))
         .times(1)
        )

        with self.assertRaises(UberException) as expected_exception:
            self._client._post('http://www.test.org', {'nobody': 'cares'})

        self.assertEqual(expected_exception.exception.error_code, 401)
        self.assertEqual(expected_exception.exception.description, 'error!')

    def test_send_message(self):
        client = UberClient('test@test.org', '12345')
        response = mocked_response('omg')
        expected_data = {
            'email': 'test@test.org',
            'deviceOS': settings.DEVICE_OS,
            'language': 'en',
            'deviceModel': settings.DEVICE_MODEL,
            'app': 'client',
            'messageType': '111',
            'token': '12345',
            'version': settings.UBER_VERSION,
            'device': settings.DEVICE_NAME,
            'aaa': 'bbb',
        }

        (flexmock(UberClient)
         .should_receive('_copy_location_for_message')
         .with_args(self.mock_location, dict)
         .times(1)
        )

        (flexmock(UberClient)
         .should_receive('_post')
         .with_args(UberClient.ENDPOINT, data=DictPartialMatcher(expected_data))
         .times(1)
         .and_return(response))

        (flexmock(UberClient)
         .should_receive('_validate_message_response')
         .with_args(response.json())
         .times(1)
        )

        params = {
            'aaa': 'bbb'
        }

        self.assertEqual('omg', client._send_message('111', params, self.mock_location))

    def test_login(self):
        (flexmock(uber.client)
            .should_receive('hash_password')
            .and_return('1122334455')
        )

        (flexmock(UberClient)
            .should_receive('_send_message')
            .with_args('Login', params={'password': '1122334455', 'email': 'aaa'})
            .and_return({
                'token': '12345'
            })
        )


        token = UberClient.login('aaa', 'bbb')
        self.assertEqual(token, '12345')

    def test_hash_password(self):
        from uber.client import hash_password
        self.assertEqual(hash_password('12345'), 'e186e4e7a446d1b451e8e985c8db4a21')


    def test_nearby_places(self):
        params = {
            'searchTypes': ['places'],
            'query': 'huge potato'
        }

        expected_places = [1,2,3,4,5]

        (flexmock(self._client)
            .should_receive('_send_message')
            .with_args('LocationSearch', params=params, location='test_location')
            .and_return({'places': expected_places})
        )


        result = self._client.nearby_places('huge potato', 'test_location')
        self.assertEqual([x.raw for x in result], expected_places)
        for item in result:
            self.assertEqual(type(item), Place)

    def test_copy_location_for_message(self):
        data = {}
        self._client._copy_location_for_message({'longitude': 1, 'latitude': 0.5}, data)
        self.assertEqual(data, {'longitude': 1, 'latitude': 0.5})

        data = {}
        self._client._copy_location_for_message(GPSLocation(latitude=0.5, longitude=1), data)
        self.assertEqual(data, {'longitude': 1, 'latitude': 0.5})

        data = {}
        self._client._copy_location_for_message(GPSLocation(
            latitude=0.5,
            longitude=1,
            vertical_accuracy=0.1,
            horizontal_accuracy=0.2,
            altitude=0.3), data)

        self.assertEqual(data, {
            'latitude': 0.5,
            'longitude': 1,
            'verticalAccuracy': 0.1,
            'horizontalAccuracy': 0.2,
            'altitude': 0.3,
            })


    def test_request_pickup(self):
        (flexmock(UberClient)
            .should_receive('_send_message')
            .with_args('Pickup',
                       params={'vehicleViewId': 1, 'useCredits': True, 'pickupLocation': {'some_geo_field': '12345'}},
                       location=self.mock_location)
        )

        self._client.request_pickup(
            vehicle_type=VehicleView({'id': 1}),
            pickup_address={'some_geo_field': '12345'},
            gps_location=self.mock_location)

    def test_request_pickup_with_string_address(self):
        (flexmock(geolocation)
            .should_receive('geolocate')
            .with_args('some address')
            .and_return([{'some_geo_field': '12345'}])
        )

        (flexmock(UberClient)
            .should_receive('_send_message')
            .with_args('Pickup',
                       params={'vehicleViewId': 1, 'useCredits': True, 'pickupLocation': {'some_geo_field': '12345'}},
                       location=self.mock_location)
        )

        self._client.request_pickup(
            vehicle_type=VehicleView({'id': 1}),
            pickup_address='some address',
            gps_location=self.mock_location)

    def test_request_pickup_with_bad_string_address(self):
        (flexmock(geolocation)
            .should_receive('geolocate')
            .with_args('some address')
            .and_return([])
        )

        with self.assertRaises(UberLocationNotFound):
            self._client.request_pickup(
                vehicle_type=VehicleView({'id': 1}),
                pickup_address='some address',
                gps_location=self.mock_location)

    def test_request_pickup_int_args(self):
        (flexmock(geolocation)
            .should_receive('geolocate')
            .with_args('some address')
            .and_return([{'some_geo_field': '12345'}])
        )

        (flexmock(UberClient)
            .should_receive('_send_message')
            .with_args('Pickup',
                       params={'vehicleViewId': 111,
                               'useCredits': True,
                               'paymentProfileId': 555,
                               'pickupLocation': {'some_geo_field': '12345'}
                       },
                       location=self.mock_location)
        )

        self._client.request_pickup(
            vehicle_type=111,
            pickup_address='some address',
            payment_profile=555,
            gps_location=self.mock_location)

    def test_request_pickup_model_args(self):
        (flexmock(geolocation)
            .should_receive('geolocate')
            .with_args('some address')
            .and_return([{'some_geo_field': '12345'}])
        )

        (flexmock(UberClient)
            .should_receive('_send_message')
            .with_args('Pickup',
                       params={'vehicleViewId': 111,
                               'useCredits': True,
                               'paymentProfileId': 555,
                               'pickupLocation': {'some_geo_field': '12345'}
                       },
                       location=self.mock_location)
        )

        self._client.request_pickup(
            vehicle_type=VehicleView({'id': 111}),
            pickup_address='some address',
            payment_profile=PaymentProfile({'id': 555}),
            gps_location=self.mock_location)


    def test_ping(self):
        (flexmock(UberClient)
            .should_receive('_send_message')
            .with_args('PingClient',
                       location=self.mock_location)
        )

        self._client.ping(self.mock_location)

if __name__ == '__main__':
    unittest.main()