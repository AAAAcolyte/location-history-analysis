import requests
import json
import os

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
    params = {'client_id': os.environ['FOUR_SQUARE_ID'],
              'client_secret': os.environ['FOUR_SQUARE_SECRET'] ,
              'v': '20190613',
              'll': ll,
              'radius': '5',
              'limit': '1'
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
    if venues and len(venues) != 0:
        venue = venues[0]
        venueLocationLat = venue['location']['lat']
        venueName = venue['name']
        places = queryHeroku(venueName)

        if places:
            for place in places:
                errorValue = place['lat'] - venueLocationLat
                # Allow error in lat/long
                if errorValue <= 0.002:
                    place['name'] = venueName
                    return place
        else:
            return None

