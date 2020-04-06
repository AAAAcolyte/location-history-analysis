import geopy.distance
import httprequests
import datetime
import csv
import json
from pyclustering.cluster.kmedoids import kmedoids
distance_dict = dict()


def preprocess_location_history(file_path):
    with open(file_path) as json_file:
        data = json.load(json_file)
        locations = data['locations']
        filtered_locations = []
        for location in locations:
            timestamp = int(location['timestampMs'])
            location['latitude'] = location['latitudeE7'] / (10 ** 7)
            location['longitude'] = location['longitudeE7'] / (10 ** 7)
            date_time = datetime.datetime.fromtimestamp(
                timestamp // 1000.0)
            # This filter is applied because I wasn't in the US before 5 July
            if datetime.datetime(2019, 7, 5) <= date_time:
                filtered_locations.append(location)
        return filtered_locations


def get_places(stays):
    place_stay = dict()
    for stay in stays:
        lat = stay[0][0] / (10 ** 7)
        long = stay[0][1] / (10 ** 7)
        print(lat, long)
        found_places = httprequests.getLocation(lat, long)
        if found_places:
            place_name = found_places[0]['name']
            start = datetime.datetime.fromtimestamp(stay[1] / 1000.0)
            end = datetime.datetime.fromtimestamp(stay[2] / 1000.0)
            duration = end - start

            if place_name not in place_stay:
                place_stay[place_name] = duration
            else:
                place_stay[place_name] = place_stay[place_name] + duration

    sorted_by_stay = sorted(
        place_stay.items(), key=lambda kv: kv[1], reverse=True)
    print(len(sorted_by_stay))
    with open('stay.csv', 'w') as f:
        csv_out = csv.writer(f)
        for row in sorted_by_stay:
            csv_out.writerow(row)

    for place, stay in place_stay.items():
        print("%s at %s" % (stay, place))


def time_diff(R, i, j) -> int:
    ms_diff = int(R[j]['timestampMs']) - int(R[i]['timestampMs'])
    return ms_diff / (6 * (10 ** 4))


def diameter(R, i, j):
    # print (j)
    global distance_dict
    max_distance = 0
    for tmp1 in range(i, j + 1):
        l1 = R[tmp1]
        for tmp2 in range(tmp1, j + 1):
            l2 = R[tmp2]
            if (tmp1, tmp2) in distance_dict:
                distance = distance_dict[(tmp1, tmp2)]
            else:
                latlong1 = (l1['latitude'],
                            l1['longitude'])
                latlong2 = (l2['latitude'],
                            l2['longitude'])
                distance = distance_between_two(latlong1, latlong2)
                distance_dict[(tmp1, tmp2)] = distance
            max_distance = max(max_distance, distance)
    return max_distance


def medoid(R, i, j):
    sum_x = 0
    sum_y = 0
    for tmp in range(i, j + 1):
        sum_x += R[tmp]['latitude']
        sum_y += R[tmp]['longitude']
    return sum_x / (j - i + 1), sum_y / (j - i + 1)


def distance_between_two(location1, location2):
    return geopy.distance.distance(location1, location2).meters
