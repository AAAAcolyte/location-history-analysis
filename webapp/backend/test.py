from census import Census
from us import states
import csv
import pandas as pd

c = Census("04cfdf7360e9e83ba2c2e502fe3372fb75dd578e")

stateCodes = states.mapping("fips", "name")

# print (stateCodes)
countyCodes = []
for state in stateCodes:
    temp = c.acs5.state_county("NAME", state, Census.ALL)
    countyCodes.append({state : temp})

# temp = c.acs5.state_county("NAME", 25, Census.ALL)
# countyCodes.append({25: temp})

censusBlockGroups = []
for state in countyCodes:
    for key, value in state.items():
        for element in value:
            # print (element["state"], element["county"])
            blockgroup = c.acs5.state_county_blockgroup("NAME", element["state"], element["county"], Census.ALL)
            censusBlockGroups.append(blockgroup)

censusBlockGroups = [item for sublist in censusBlockGroups for item in sublist]
# print (censusBlockGroups)
print (type(censusBlockGroups))

keys = censusBlockGroups[0].keys()
print (censusBlockGroups[0])
with open('blockgroup.csv', 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(censusBlockGroups)