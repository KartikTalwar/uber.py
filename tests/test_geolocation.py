import unittest
import requests
from tests import mocked_response
from uber import geolocate, GPSLocation, GeolocationExcetion
from flexmock import flexmock

class TestGeoLocation(unittest.TestCase):
    def test_geolocation_no_results(self):
        expected_args = {
            'sensor': 'false',
            'address': 'my magic address'
        }
        (flexmock(requests)
            .should_receive('get')
            .with_args('http://maps.googleapis.com/maps/api/geocode/json', params=expected_args)
            .and_return(mocked_response({'status': 'ZERO_RESULTS'}))
        )

        results = geolocate('my magic address')
        self.assertEqual(results, [])

    def test_geolocation_multiple_results(self):
        expected_args = {
            'sensor': 'false',
            'address': 'my magic address'
        }

        expected_results = {
            'status': 'OK',
            'results': [{
                'address_components': 'lol1',
                'some_field': 'some_field1',
                'geometry': {
                    'location': {
                        'lat': 1,
                        'lng': 2,
                    }
                }

            },
            {
                'address_components': 'lol2',
                'some_field': 'some_field2',
                'geometry': {
                    'location': {
                        'lat': 3,
                        'lng': 4,
                    }
                }

            }]

        }
        (flexmock(requests)
            .should_receive('get')
            .with_args('http://maps.googleapis.com/maps/api/geocode/json', params=expected_args)
            .and_return(mocked_response(expected_results))
        )

        results = geolocate('my magic address')
        self.assertEqual(results, [
            {
                'address_components': 'lol1',
                'some_field': 'some_field1',
                'geometry': {'location': {'lat': 1, 'lng': 2}},
                'latitude': 1,
                'longitude': 2,
            },
            {
                'address_components': 'lol2',
                'some_field': 'some_field2',
                'geometry': {'location': {'lat': 3, 'lng': 4}},
                'latitude': 3,
                'longitude': 4,
            }
        ])

    def test_components(self):
        expected_args = {
            'sensor': 'false',
            'address': 'my magic address',
            'components': 'country:US|administrative_area:SF'
        }
        (flexmock(requests)
            .should_receive('get')
            .with_args('http://maps.googleapis.com/maps/api/geocode/json', params=expected_args)
            .and_return(mocked_response({'status': 'ZERO_RESULTS'}))
        )

        results = geolocate('my magic address', country='US', administrative_area='SF')

    def test_bounds(self):
        expected_args = {
            'sensor': 'false',
            'address': 'my magic address',
            'bounds': '1,2|3,4'
        }
        (flexmock(requests)
            .should_receive('get')
            .with_args('http://maps.googleapis.com/maps/api/geocode/json', params=expected_args)
            .and_return(mocked_response({'status': 'ZERO_RESULTS'}))
        )

        geolocate('my magic address', bounds=[GPSLocation(1, 2), GPSLocation(3, 4)])

    def test_error(self):
        expected_args = {
            'sensor': 'false',
            'address': 'my magic address'
        }
        (flexmock(requests)
            .should_receive('get')
            .with_args('http://maps.googleapis.com/maps/api/geocode/json', params=expected_args)
            .and_return(mocked_response({'status': 'ERROR'}))
        )

        with self.assertRaises(GeolocationExcetion) as expected_exception:
            geolocate('my magic address')

        self.assertEqual(expected_exception.exception.message, {'status': 'ERROR'})

        expected_args = {
            'sensor': 'false',
            'address': 'my magic address'
        }
        (flexmock(requests)
            .should_receive('get')
            .with_args('http://maps.googleapis.com/maps/api/geocode/json', params=expected_args)
            .and_return(mocked_response({'say': 'what'}, status_code=401))
        )

        with self.assertRaises(GeolocationExcetion) as expected_exception:
            geolocate('my magic address')

        self.assertEqual(expected_exception.exception.message, {'say': 'what'})


if __name__ == '__main__':
    unittest.main()
