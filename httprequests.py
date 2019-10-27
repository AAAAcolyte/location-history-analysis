import requests
import json
import os


def getCensusBlock(lat, long):
    response = requests.get(
        "https://geo.fcc.gov/api/census/block/find?latitude=%s&longitude=%s&format=json&censusYear=2015" % (lat, long))
    try:
        r = response.json()
        return r['Block']['FIPS']
    except Exception:
        print("Exception")


def queryHeroku(placeName):
    response = requests.get(
        "https://social-capital-ml.herokuapp.com/findPlace?name=%s" % placeName)
    try:
        r = response.json()
        return r
    except json.decoder.JSONDecodeError:
        print(response)


def queryFourSquare(lat, long):
    ll = "%s, %s" % (lat, long)
    params = {
        # 'client_id': os.environ['FOUR_SQUARE_ID'],
        # 'client_secret': os.environ['FOUR_SQUARE_SECRET'] ,
        'client_id': 'TM4BB42XIBZV2RUL5LTWWALPACTV2Z5D2JXIRO5XB01VOPPF',
        'client_secret': 'ZAOQ0CBN2X2E22ICHZOTG0XLMOONNXX4QSBAVEN2XEJ21IN0',
        'v': '20190613',
        'll': ll,
        'radius': '5',
        'limit': '3'
    }
    response = requests.get(
        "https://api.foursquare.com/v2/venues/search", params=params)
    try:
        r = response.json()
        if 'response' in r:
            if 'venues' in r['response']:
                return r['response']['venues']
    except json.decoder.JSONDecodeError:
        print(response)


def getLocation(lat, long):
    venues = queryFourSquare(lat, long)
    sum_distance = 0
    found_places = list()
    if venues and len(venues) != 0:
        for venue in venues:
            sum_distance += venue['location']['distance']
        for venue in venues:
            venueLocationLat = venue['location']['lat']
            venueName = venue['name']
            distance = venue['location']['distance']
            confidence = 1.0 - distance / sum_distance
            places = queryHeroku(venueName)
            if places:
                place = places[0]
                for place in places:
                    place['name'] = venueName
                    place['confidence'] = confidence
                    found_places.append(place)
    return found_places
