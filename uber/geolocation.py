import requests


class GeolocationExcetion(Exception):
    pass


def geolocate(address, bounds=None, country=None, administrative_area=None, sensor=False):
    """
    Resolves address using Google Maps API, and performs some massaging to the output result.
    Provided for convenience, as Uber relies on this heavily, and the desire to give a simple 'batteries included' experience.

    See https://developers.google.com/maps/documentation/geocoding/ for more details
    """
    params = {
        'address': address,
        'sensor': str(sensor).lower()
    }

    components = []
    if country:
        components.append('country:' + country)

    if administrative_area:
        components.append('administrative_area:' + administrative_area)

    if bounds:
        params['bounds'] = '|'.join(['{},{}'.format(x.latitude, x.longitude) for x in bounds])

    if components:
        params['components'] = '|'.join(components)

    response = requests.get('http://maps.googleapis.com/maps/api/geocode/json', params=params)
    if not response.ok:
        raise GeolocationExcetion(response.text)

    data = response.json()

    if data['status'] not in ['OK', 'ZERO_RESULTS']:
        raise GeolocationExcetion(data)

    all_results = data.get('results', [])
    for result in all_results:
        coords = result.get('geometry', {}).get('location')
        if coords:
            result['latitude'] = coords['lat']
            result['longitude'] = coords['lng']

    return all_results
