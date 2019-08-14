import json
import httprequests
import datetime
import sys


def calculate_seg_score(place_time_dict, place_info_dict):
    total_stays = 0
    p1a_sum = 0
    p2a_sum = 0
    p3a_sum = 0
    p4a_sum = 0
    seg_sum = 0

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

    avg_p1a = p1a_sum / total_stays
    avg_p2a = p2a_sum / total_stays
    avg_p3a = p3a_sum / total_stays
    avg_p4a = p4a_sum / total_stays
    avg_seg = seg_sum / total_stays

    print('P1A Score %f P2A Score %f P3A Score %f P4A Score %f Seg Score %f' % (
        avg_p1a, avg_p2a, avg_p3a, avg_p4a, avg_seg))


def is_stay(location):
    # If the velocity is 0 or Google feels confident the user is still, we consider it to be a 'stay'
    if 'velocity' in location and location['velocity'] == 0:
        return True
    if 'activity' in location:
        for outer_activity in location['activity']:
            for activity in outer_activity['activity']:
                if activity['type'] == 'STILL' and activity['confidence'] > 50:
                    return True


def analyse_location_history(file_path):
    last_location_name = ""
    last_location_recorded = False
    # A 'total' dict, the key is the place ID and the value is the number of visits
    place_time_dict = dict()
    # A dict for each day
    place_time_dict_by_date = dict()
    place_info_dict = dict()

    # Only consider the last 30 days
    time_threshold = datetime.datetime.today() - datetime.timedelta(days=30)

    with open(file_path) as json_file:
        data = json.load(json_file)
        for location in data['locations']:
            # Only consider it if it's a stay
            if is_stay(location):
                timestamp = int(location['timestampMs'])
                date_time = datetime.datetime.fromtimestamp(
                    timestamp // 1000.0)
                if date_time > time_threshold:
                    date = date_time.date()
                    if not (date in place_time_dict_by_date):
                        place_time_dict_by_date[date] = dict()
                    lat = location['latitudeE7'] / (10**7)
                    long = location['longitudeE7'] / (10**7)
                    found_place = httprequests.getLocation(lat, long)
                    if found_place:
                        found_place_name = found_place['name']
                        found_place_id = found_place['_id']
                        if not (found_place_id in place_info_dict):
                            place_info_dict[found_place_id] = found_place
                        if (found_place_name == last_location_name) and (last_location_recorded == False):
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
                            if (found_place_name != last_location_name):
                                last_location_recorded = False
                        last_location_name = found_place['name']


        # Sort the places by the degree of segregation
        sorted_places = sorted(place_info_dict.items(),
                               key=lambda x: x[1]['segregation'])

        for (place_id, place_info) in sorted_places:
            if (place_id in place_time_dict):
                place_name = place_info['name']
                place_segscore = place_info['segregation']
                visit_times = place_time_dict[place_id]
                print('You visited %s %d times, it has a segregation score of %f' % (
                    place_name, visit_times, place_segscore))

        calculate_seg_score(place_time_dict, place_info_dict)

        for date, place_time_dict_on_date in place_time_dict_by_date.items():
            if place_time_dict_on_date:
                print(date)
                calculate_seg_score(place_time_dict_on_date, place_info_dict)


if __name__ == "__main__":
    file_path = sys.argv[1]
    if (file_path):
        print(file_path)
        analyse_location_history(file_path)
