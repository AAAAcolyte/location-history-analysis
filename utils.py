import geopy.distance
import httprequests
import datetime
import csv
from pyclustering.cluster.kmedoids import kmedoids
distance_dict = dict()

def extract_stays(locations, t_dur=5, l_roam=5):
    # The same algorithm as in LNCS 3234
    i = 0
    s = []
    while i < len(locations) - 1:
        print(i)
        j = i + 1
        if j < len(locations):
            time_i = int(locations[i]['timestampMs'])
            while j < len(locations) and time_diff(locations, i, j) < 5: 
              # Find the next record with time difference larger than t_dur
                j += 1
            if j >= len(locations):
              j -= 1
            if i == j:
              i = i + 1
              continue            
            if time_diff(locations, i, j) > 60:
              # The difference is too big, we consider it as a new stay
                i = j
                continue
            if diameter(locations, i, j) > l_roam:
                i = i + 1
            else:
                while j < len(locations) and diameter(locations, i, j) <= l_roam and           time_diff(locations,i,j) <= 24 * 60:
                    j += 1
                j -= 1
                time_j = int(locations[j]['timestampMs'])
                s.append((medoid(locations, i, j), time_i, time_j))
                i = j + 1
        else:
            break
    print(s)
    get_places(s)

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

    sorted_by_stay = sorted(place_stay.items(), key=lambda kv:kv[1], reverse=True)
    print (len(sorted_by_stay))
    with open('stay.csv', 'w') as f:
      csv_out = csv.writer(f)
      for row in sorted_by_stay:
        csv_out.writerow(row)

    for place, stay in place_stay.items():
      print ("%s at %s" % (stay, place))

def time_diff(R, i, j)->int:
  ms_diff = int(R[j]['timestampMs']) - int(R[i]['timestampMs'])
  return ms_diff /  (6 * (10 ** 4))

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
                latlong1 = (l1['latitudeE7'] / (10 ** 7), l1['longitudeE7'] / (10 ** 7))
                latlong2 = (l2['latitudeE7'] / (10 ** 7), l2['longitudeE7'] / (10 ** 7))
                distance = distance_between_two(latlong1, latlong2)
                distance_dict[(tmp1, tmp2)] = distance
            max_distance = max(max_distance, distance)
    return max_distance

def medoid(R, i, j):
    sum_x = 0
    sum_y = 0
    for tmp in range(i, j + 1):
        sum_x += R[tmp]['latitudeE7']
        sum_y += R[tmp]['longitudeE7']
    return sum_x / (j - i + 1), sum_y / (j - i + 1)

def distance_between_two(location1, location2):
    return geopy.distance.distance(location1, location2).meters
