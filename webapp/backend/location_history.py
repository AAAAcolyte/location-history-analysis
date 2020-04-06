import json
import httprequests
import datetime
import utils
import sys
from tzwhere import tzwhere
import pytz
import pandas as pd
from geopy.distance import great_circle
from sklearn.cluster import DBSCAN
import numpy as np
import csv
from shapely.geometry import MultiPoint
import utils


number_name_dict = {}

blockgroup_stays_dict = {}
total_stays = 0
p1a_sum = 0
p2a_sum = 0
p3a_sum = 0
p4a_sum = 0
seg_sum = 0


def calculate_seg_score(place_time_dict, place_info_dict):
    for place_id, times in place_time_dict.items():
        place_info = place_info_dict[place_id]
        place_name = place_info['name']
        p1a = place_info['p1a']
        p2a = place_info['p2a']
        p3a = place_info['p3a']
        p4a = place_info['p4a']
        seg = place_info['segregation']

        total_stays += times
        p1a_sum += p1a * times
        p2a_sum += p2a * times
        p3a_sum += p3a * times
        p4a_sum += p4a * times
        seg_sum += seg * times

        print('Place %s %d times' % (place_name, times))

    if total_stays > 0:
        avg_p1a = p1a_sum / total_stays
        avg_p2a = p2a_sum / total_stays
        avg_p3a = p3a_sum / total_stays
        avg_p4a = p4a_sum / total_stays
        avg_seg = seg_sum / total_stays

        print('P1A Score %f P2A Score %f P3A Score %f P4A Score %f Seg Score %f' % (
            avg_p1a, avg_p2a, avg_p3a, avg_p4a, avg_seg))

# Extract stays from location history data point
# stay is of type ((lat, long), start_time, end_time)


def extract_stays(locations, t_dur=5, l_roam=5):
    # The same algorithm as in LNCS 3234
    i = 0
    s = []
    while i < len(locations) - 1:
        # print(i)
        j = i + 1
        if j < len(locations):
            time_i = int(locations[i]['timestampMs'])
            while j < len(locations) and utils.time_diff(locations, i, j) < 5:
              # Find the next record with time difference larger than t_dur
                j += 1
            if j >= len(locations):
                j -= 1
            if i == j:
                i = i + 1
                continue
            if utils.time_diff(locations, i, j) > 60:
                # The difference is too big, we consider it as a new stay
                i = j
                continue
            if utils.diameter(locations, i, j) > l_roam:
                i = i + 1
            else:
                while j < len(locations) and utils.diameter(locations, i, j) <= l_roam and utils.time_diff(locations, i, j) <= 24 * 60:
                    j += 1
                j -= 1
                time_j = int(locations[j]['timestampMs'])
                s.append((utils.medoid(locations, i, j), time_i, time_j))
                i = j + 1
        else:
            break
    # extract_home_from_stays(s)
    get_places(s)


def is_stay_overnight(stay):
    start_of_stay = datetime.datetime.fromtimestamp(
        stay[1] / 1000, tz=pytz.timezone('America/New_York'))
    cond = start_of_stay.hour <= 6 or start_of_stay.hour >= 20
    return cond


def extract_home_from_stays(stays):
    home_stays = dict()
    number_name_dict = dict()
    with open('blockgroup.csv') as block_group_data:
        rows = csv.DictReader(block_group_data)
        for row in rows:
            group_number = row['state'] + row['county'] + \
                row['tract'] + row['block group']
            name = row['NAME']
            number_name_dict[group_number] = name
    for stay in stays:
        if is_stay_overnight(stay):
            (lat, long) = stay[0]
            census_block = httprequests.getCensusBlock(lat, long)
            census_block_group = census_block[:12]
            block_group_name = number_name_dict[census_block_group]
            if block_group_name in home_stays:
                home_stays[block_group_name] += 1
            else:
                home_stays[block_group_name] = 1

    for name, stay in home_stays.items():
        print('The home is in %s, you spent %d nights there' %
              (name, stay))

        # location = httprequests.getLocation(lat / (10 ** 7), long / (10 ** 7))
        # if location:
        #   print (location[0]['name'])
        # length_of_stay = (stay[2] - stay[1]) / 60000 / 60
        # if (length_of_stay > 5):
        #     (lat, long) = stay[0]
        #     print (httprequests.getLocation(lat / (10 ** 7), long / (10 ** 7)))


def get_places(stays):
    place_stay = dict()
    fsq_info = dict()
    for stay in stays:
        (lat, long) = stay[0]
        found_places = httprequests.getLocation(lat, long)
        if found_places:
            most_likely_place = found_places[0]
            place_info = {'lat': most_likely_place['lat'], 'long': most_likely_place['lon'],
                          'id': most_likely_place['_id'], 'name': most_likely_place['name']}
            place_id = found_places[0]['_id']
            fsq_info[place_id] = place_info
            start = datetime.datetime.fromtimestamp(
                stay[1] / 1000.0, tz=pytz.timezone('America/New_York'))
            end = datetime.datetime.fromtimestamp(
                stay[2] / 1000.0, tz=pytz.timezone('America/New_York'))
            duration = end - start
            if place_id not in place_stay:
                place_stay[place_id] = duration
            else:
                place_stay[place_id] = place_stay[place_id] + duration

    sorted_by_stay = sorted(
        place_stay.items(), key=lambda kv: kv[1], reverse=True)
    with open('stay.csv', 'w') as f:
        filed_names = ['id', 'lat', 'long', 'name', 'time']
        writer = csv.DictWriter(f=f, fieldnames=filed_names)
        writer.writeheader()
        for row in sorted_by_stay:
            id = row[0]
            time = row[1]
            place_info = fsq_info[id]
            place_info['time'] = time
            writer.writerow(place_info)

    for place, stay in place_stay.items():
        print("%s at %s" % (stay, place))


def is_stay(location):
    # If the velocity is 0 or Google feels confident the user is still, we consider it to be a 'stay'
    if 'velocity' in location and location['velocity'] == 0:
        return True
    if 'activity' in location:
        for outer_activity in location['activity']:
            for activity in outer_activity['activity']:
                if activity['type'] == 'STILL' and activity['confidence'] > 50:
                    return True


def analyse_location_history(json_file):
    print ('Analysis started!')
    last_location_name = ""
    last_location_recorded = False
    # A 'total' dict, the key is the place ID and the value is the number of visits
    place_time_dict = dict()
    place_stay_length_dict = dict()
    # A dict for each day
    place_time_dict_by_date = dict()
    place_stay_length_dict_by_date = dict()
    place_info_dict = dict()

    # Only consider the last 30 days
    # time_threshold = datetime.datetime.today() - datetime.timedelta(days=30)

    time_threshold = datetime.datetime(2019, 7, 1)
    time_upper_limit = datetime.datetime(2019, 7, 30)
    last_timestamp = None
    data = json.load(json_file)
    for location in data['locations']:
        # Only consider it if it's a stay
        if is_stay(location):
            timestamp = int(location['timestampMs'])
            if not last_timestamp:
                last_timestamp = timestamp
            date_time = datetime.datetime.fromtimestamp(
                timestamp // 1000.0)
            if date_time > time_threshold and date_time < time_upper_limit:
                date = date_time.date()
                if not (date in place_time_dict_by_date):
                    place_time_dict_by_date[date] = dict()
                    place_stay_length_dict_by_date[date] = dict()
                lat = location['latitudeE7'] / (10 ** 7)
                long = location['longitudeE7'] / (10 ** 7)
                found_places = httprequests.getLocation(lat, long)
                if found_places:
                    most_confident_place = found_places[0]
                    print(most_confident_place['confidence'])
                    found_place_name = most_confident_place['name']
                    print(found_place_name)
                    found_place_id = most_confident_place['_id']
                    if not (found_place_id in place_info_dict):
                        place_info_dict[found_place_id] = most_confident_place
                    if (found_place_name == last_location_name):
                        if not last_location_recorded:
                            # The user is still at the same place and the place is not recorded yet
                            # so we consider the user stays there for a while
                            if found_place_id in place_time_dict:
                                place_time_dict[found_place_id] += 1
                            else:
                                place_time_dict[found_place_id] = 1
                            if found_place_id in place_time_dict_by_date[date]:
                                place_time_dict_by_date[date][found_place_id] += 1
                            else:
                                place_time_dict_by_date[date][found_place_id] = 1
                            last_location_recorded = True
                        else:
                            # The user spends more time at the place
                            duration = timestamp - last_timestamp
                            if found_place_id in place_stay_length_dict:
                                place_stay_length_dict[found_place_id] += duration
                            else:
                                place_stay_length_dict[found_place_id] = 0
                            if found_place_id in place_stay_length_dict_by_date[date]:
                                place_stay_length_dict_by_date[date][found_place_id] += duration
                            else:
                                place_stay_length_dict_by_date[date][found_place_id] = 0
                    else:
                        if found_place_name != last_location_name:
                            last_location_recorded = False
                    last_location_name = most_confident_place['name']
        last_timestamp = timestamp
        # for found_place in found_places:
        #     print (found_place['confidence'])
        #     found_place_name = found_place['name']
        #     print (found_place_name)
        #     found_place_id = found_place['_id']
        #     if not (found_place_id in place_info_dict):
        #         place_info_dict[found_place_id] = found_place
        #     if (found_place_name == last_location_name) and (last_location_recorded == False):
        #         # The user is still at the same place and the place is not recorded yet
        #         # so we consider the user stays there for a while
        #         if found_place_id in place_time_dict:
        #             place_time_dict[found_place_id] += 1
        #         else:
        #             place_time_dict[found_place_id] = 1
        #         if found_place_id in place_time_dict_by_date[date]:
        #             place_time_dict_by_date[date][found_place_id] += 1
        #         else:
        #             place_time_dict_by_date[date][found_place_id] = 1
        #         last_location_recorded = True
        #     else:
        #         if (found_place_name != last_location_name):
        #             last_location_recorded = False
        #     last_location_name = found_place['name']
        # return

        # Sort the places by the degree of segregation
        sorted_places = sorted(place_info_dict.items(),
                               key=lambda x: x[1]['segregation'])

        for (place_id, duration) in place_stay_length_dict.items():
            time = datetime.timedelta(milliseconds=duration)
            print("You spent %s time at %s" %
                  (time, place_info_dict[place_id]['name']))

        # for (place_id, place_info) in sorted_places:
        #     if (place_id in place_time_dict):
        #         place_name = place_info['name']
        #         place_segscore = place_info['segregation']
        #         visit_times = place_time_dict[place_id]
        #         print('You visited %s %d times, it has a segregation score of %f' % (
        #             place_name, visit_times, place_segscore))
        #
        # calculate_seg_score(place_time_dict, place_info_dict)
        #
        # for date, place_time_dict_on_date in place_time_dict_by_date.items():
        #     if place_time_dict_on_date:
        #         print(date)
        #         calculate_seg_score(place_time_dict_on_date, place_info_dict)


def analyse_location_history_ra(file_path):
    last_location_name = ""
    last_location_recorded = False
    # A 'total' dict, the key is the place ID and the value is the number of visits
    place_time_dict = dict()
    place_stay_length_dict = dict()
    # A dict for each day
    place_time_dict_by_date = dict()
    place_stay_length_dict_by_date = dict()
    place_info_dict = dict()

    # Only consider the last 30 days
    # time_threshold = datetime.datetime.today() - datetime.timedelta(days=30)

    time_threshold = datetime.datetime(2019, 7, 1)
    time_upper_limit = datetime.datetime(2019, 7, 30)
    last_timestamp = None
    with open(file_path) as json_file:
        data = json.load(json_file)
        for location in data['locations']:
            # Only consider it if it's a stay
            if is_stay(location):
                timestamp = int(location['timestampMs'])
                if not last_timestamp:
                    last_timestamp = timestamp
                date_time = datetime.datetime.fromtimestamp(
                    timestamp // 1000.0)
                if date_time > time_threshold and date_time < time_upper_limit:
                    date = date_time.date()
                    if not (date in place_time_dict_by_date):
                        place_time_dict_by_date[date] = dict()
                        place_stay_length_dict_by_date[date] = dict()
                    lat = location['latitudeE7'] / (10 ** 7)
                    long = location['longitudeE7'] / (10 ** 7)
                    found_places = httprequests.getLocation(lat, long)
                    if found_places:
                        most_confident_place = found_places[0]
                        print(most_confident_place['confidence'])
                        found_place_name = most_confident_place['name']
                        print(found_place_name)
                        found_place_id = most_confident_place['_id']
                        if not (found_place_id in place_info_dict):
                            place_info_dict[found_place_id] = most_confident_place
                        if (found_place_name == last_location_name):
                            if not last_location_recorded:
                                # The user is still at the same place and the place is not recorded yet
                                # so we consider the user stays there for a while
                                if found_place_id in place_time_dict:
                                    place_time_dict[found_place_id] += 1
                                else:
                                    place_time_dict[found_place_id] = 1
                                if found_place_id in place_time_dict_by_date[date]:
                                    place_time_dict_by_date[date][found_place_id] += 1
                                else:
                                    place_time_dict_by_date[date][found_place_id] = 1
                                last_location_recorded = True
                            else:
                                # The user spends more time at the place
                                duration = timestamp - last_timestamp
                                if found_place_id in place_stay_length_dict:
                                    place_stay_length_dict[found_place_id] += duration
                                else:
                                    place_stay_length_dict[found_place_id] = 0
                                if found_place_id in place_stay_length_dict_by_date[date]:
                                    place_stay_length_dict_by_date[date][found_place_id] += duration
                                else:
                                    place_stay_length_dict_by_date[date][found_place_id] = 0
                        else:
                            if found_place_name != last_location_name:
                                last_location_recorded = False
                        last_location_name = most_confident_place['name']
            last_timestamp = timestamp
            # for found_place in found_places:
            #     print (found_place['confidence'])
            #     found_place_name = found_place['name']
            #     print (found_place_name)
            #     found_place_id = found_place['_id']
            #     if not (found_place_id in place_info_dict):
            #         place_info_dict[found_place_id] = found_place
            #     if (found_place_name == last_location_name) and (last_location_recorded == False):
            #         # The user is still at the same place and the place is not recorded yet
            #         # so we consider the user stays there for a while
            #         if found_place_id in place_time_dict:
            #             place_time_dict[found_place_id] += 1
            #         else:
            #             place_time_dict[found_place_id] = 1
            #         if found_place_id in place_time_dict_by_date[date]:
            #             place_time_dict_by_date[date][found_place_id] += 1
            #         else:
            #             place_time_dict_by_date[date][found_place_id] = 1
            #         last_location_recorded = True
            #     else:
            #         if (found_place_name != last_location_name):
            #             last_location_recorded = False
            #     last_location_name = found_place['name']
            # return

        # Sort the places by the degree of segregation
        sorted_places = sorted(place_info_dict.items(),
                               key=lambda x: x[1]['segregation'])

        for (place_id, duration) in place_stay_length_dict.items():
            time = datetime.timedelta(milliseconds=duration)
            print("You spent %s time at %s" %
                  (time, place_info_dict[place_id]['name']))

        # for (place_id, place_info) in sorted_places:
        #     if (place_id in place_time_dict):
        #         place_name = place_info['name']
        #         place_segscore = place_info['segregation']
        #         visit_times = place_time_dict[place_id]
        #         print('You visited %s %d times, it has a segregation score of %f' % (
        #             place_name, visit_times, place_segscore))
        #
        # calculate_seg_score(place_time_dict, place_info_dict)
        #
        # for date, place_time_dict_on_date in place_time_dict_by_date.items():
        #     if place_time_dict_on_date:
        #         print(date)
        #         calculate_seg_score(place_time_dict_on_date, place_info_dict)


def is_night(date_time):
    # print (date_time.hour)
    return date_time.hour <= 6 or date_time.hour >= 20


def get_center_point(cluster):
    # print (cluster)
    MultiPoint(points=cluster)
    centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)
    centermost_point = min(
        cluster, key=lambda point: great_circle(point, centroid).m)
    # print (centermost_point)
    return tuple(centermost_point)


def cluster_location(coordinates_list):
    global number_name_dict
    global blockgroup_stays_dict
    print(len(number_name_dict))
    db = DBSCAN(eps=0.3, min_samples=5).fit(coordinates_list)
    cluster_labels = db.labels_
    num_clusters = len(set(cluster_labels)) - \
        (1 if -1 in cluster_labels else 0)
    clusters = pd.Series([coordinates_list[cluster_labels == n]
                          for n in range(num_clusters)])
    if num_clusters > 0:
        for cluster in clusters:
            lat, long = get_center_point(cluster)
            census_block = httprequests.getCensusBlock(lat, long)
            if census_block:
                # Not null
                census_block_group = census_block[:12]
                print(census_block)
                if str(census_block_group) in number_name_dict:
                    name = number_name_dict[census_block_group]
                    if name in blockgroup_stays_dict:
                        blockgroup_stays_dict[name] += 1
                    else:
                        blockgroup_stays_dict[name] = 1


def extract_home(file_path):
    global number_name_dict
    with open('blockgroup.csv') as block_group_data:
        rows = csv.DictReader(block_group_data)
        for row in rows:
            group_number = row['state'] + row['county'] + \
                row['tract'] + row['block group']
            name = row['NAME']
            number_name_dict[group_number] = name

    coordinates = []
    night_places = dict()
    with open(file_path) as json_file:
        data = json.load(json_file)
        locations = data['locations']
        for location in locations:
            lat = location['latitudeE7'] / (10 ** 7)
            long = location['longitudeE7'] / (10 ** 7)
            coordinates.append([lat, long])
            timestamp = int(location['timestampMs'])
            date_time = datetime.datetime.fromtimestamp(
                timestamp / 1000, tz=pytz.timezone('America/New_York'))
            if date_time < datetime.datetime(2019, 7, 5, tzinfo=pytz.timezone('America/New_York')):
                continue
            date = date_time.date()
            if is_night(date_time):
                if date not in night_places:
                    night_places[date] = [[lat, long]]
                else:
                    night_places[date].append([lat, long])
    for date, places in night_places.items():
        print(date)
        cluster_location(np.array(places))

    global blockgroup_stays_dict

    sorted_homes = sorted(blockgroup_stays_dict.items(),
                          key=lambda x: x[1], reverse=True)
    num = 0
    for blockgroup, stays in sorted_homes:
        if num < 5:
            print('The home is in %s, you spent %d nights there' %
                  (blockgroup, stays))
            num += 1

    with open('home.csv', 'w') as f:
        csv_out = csv.writer(f)
        for row in sorted_homes:
            csv_out.writerow(row)


def time_gap(file_path):
    with open(file_path) as json_file:
        data = json.load(json_file)
        locations = data['locations']
        gap = 0
        last_timestamp = int(locations[0]['timestampMs'])
        for location in locations:
            timestamp = int(location['timestampMs'])
            gap = max(gap, timestamp - last_timestamp)
        print(gap)


if __name__ == "__main__":
    file_path = sys.argv[1]
    if (file_path):
        location_history = utils.preprocess_location_history(file_path)
        extract_stays(location_history)
        # print("----------------")
        # extract_home(file_path)
