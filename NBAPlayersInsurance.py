import pythonDataBreakdown as mb
import pandas as pd
from pathlib import Path
import numpy as np

################################################################################
files = {2016 : 'P:/NBA Injuries Python Breakdown/2016 Fixed.csv',
         2017 : 'P:/NBA Injuries Python Breakdown/2017 Fixed.csv',
         2018 : 'P:/NBA Injuries Python Breakdown/2018 Fixed.csv'}
years = [2016, 2017, 2018]
claim_types = ['Half Season', 'Third Season']
season_days = {2016 : 169, 2017 : 169, 2018 : 176}
start_end_dates = {2016 : [pd.Timestamp(2015, 10, 27), pd.Timestamp(2016, 4, 13)],
                   2017 : [pd.Timestamp(2016, 10, 25), pd.Timestamp(2017, 4, 12)],
                   2018 : [pd.Timestamp(2017, 10, 17), pd.Timestamp(2018, 4, 11)]}

years_set = set(years)
players_2016 = pd.read_csv(Path(files[2016]))
players_2016_set = set(players_2016['Name'].unique())
players_2016 = players_2016.set_index(['Name'], drop = False)
players_2016 = players_2016[~players_2016.index.duplicated()]
players_2017 = pd.read_csv(Path(files[2017]))
players_2017_set = set(players_2017['Name'].unique())
players_2017 = players_2017.set_index(['Name'], drop = False)
players_2017 = players_2017[~players_2017.index.duplicated()]
players_2018 = pd.read_csv(Path(files[2018]))
players_2018_set = set(players_2018['Name'].unique())
players_2018 = players_2018.set_index(['Name'], drop = False)
players_2018 = players_2018[~players_2018.index.duplicated()]
# all_players_set = players_2016_set | players_2017_set | players_2018_set

claim_values = {'Standard Season' : ['Claim Games Standard', 'Payout Standard'], 'Half Season' : ['Claim Games Half', 'Payout Half'], 'Third Season' : ['Claim Games Third', 'Payout Third']}
################################################################################

def get_claim_days(player, year, report):
    claim_days = 0
    season_start, season_end = start_end_dates[year]
    for item in report:
        player, injury, start, eligible, recurrent, games, player_file = report[item]
        if(pd.isna(recurrent)): recurrent = pd.to_datetime('today')
        player_file['Possible'] = player_file['Date'].apply(lambda x: 1 if (x > eligible) & (x < recurrent) else 0)
        player_file['Year'] = player_file['Date'].apply(lambda x: 1 if (x >= season_start) & (x <= season_end) else 0)
        player_file['Count'] = player_file[['Possible', 'Year', 'Claim Count']].apply(lambda x: 1 if (x[0] == 1) & (x[1] == 1) & (x[2] == 'Yes') else 0, axis = 1)
        claim_days += player_file['Count'].sum()
        # player_file.to_csv(Path('P:/TEST.csv'))
    return claim_days

# Adjusts main file to make it more simple
def adjust_main(file):
    all_categories = pd.read_csv(file)
    simple = all_categories[['Team', 'Name', 'Date', 'Stats', 'Injured?', 'Played in Game?']]
    simple['Date'] = pd.to_datetime(simple['Date'])
    simple = simple[pd.notnull(simple['Name'])]
    return simple

def format(year):
    main = adjust_main(Path('P:/NBA Injuries Python Breakdown/Categories.csv'))
    possible_years = pd.date_range(start = start_end_dates[year][0], end = start_end_dates[year][1])
    main['Possible'] = main['Date'].apply(lambda x: True if x in possible_years else False)
    file = main[main['Possible'] == True]
    file = file[['Team', 'Name']]
    '''file['Claim Games Standard'] = 0
    file['Payout Standard'] = 0'''
    file['Claim Games Half'] = 0
    file['Payout Half'] = 0
    file['Claim Games Third'] = 0
    file['Payout Third'] = 0
    new = file.groupby(by = ['Name'])
    print(new.head())
    new.to_csv(Path('P:/NBA Injuries Python Breakdown/' + str(year) + ' Fixed.csv'))
    return file

def calculate_players(years):
    all_players_set = players_2016_set | players_2017_set | players_2018_set

    count = 0
    #print(len(all_players_set))
    # all_players_set = set(['MICHAEL KIDD-GILCHRIST'])
    all_players_set = all_players_set.difference(passed)
    for player in all_players_set:
        print(count, player)
        count += 1
        for claim_type in claim_types:
            report = mb.main([player], claim_type)
            claim_days_2016 = get_claim_days(player, 2016, report)
            if(player in players_2016.index.tolist()):
                players_2016.at[player, claim_values[claim_type][0]] = claim_days_2016
                players_2016.at[player, claim_values[claim_type][1]] = 1000000000
                #players_2016.to_csv(Path(files[2016]), index = False)
            claim_days_2017 = get_claim_days(player, 2017, report)
            if(player in players_2017.index.tolist()):
                players_2017.at[player, claim_values[claim_type][0]] = claim_days_2017
                players_2017.at[player, claim_values[claim_type][1]] = 1000000000
                #players_2017.to_csv(Path(files[2017]), index = False)
            claim_days_2018 = get_claim_days(player, 2018, report)
            if(player in players_2018.index.tolist()):
                players_2018.at[player, claim_values[claim_type][0]] = claim_days_2018
                players_2018.at[player, claim_values[claim_type][1]] = 1000000000
                #players_2018.to_csv(Path(files[2018]), index = False)
            if(count % 10 == 0):
                players_2016.to_csv(Path(files[2016]), index = False)
                players_2017.to_csv(Path(files[2017]), index = False)
                players_2018.to_csv(Path(files[2018]), index = False)
    players_2016.to_csv(Path(files[2016]), index = False)
    players_2017.to_csv(Path(files[2017]), index = False)
    players_2018.to_csv(Path(files[2018]), index = False)
    return

def main(years):
    #format(2016)
    #format(2017)
    #format(2018)
    calculate_players(years)
    return

main(years)
