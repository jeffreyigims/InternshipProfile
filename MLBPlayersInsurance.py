import MLBBreakdown as mb
import pandas as pd
from pathlib import Path
import numpy as np

files = {2016 : 'P:/League Wide Programs/MLB/Start of Year Rosters/All Clubs 2016.csv',
         2017 : 'P:/League Wide Programs/MLB/Start of Year Rosters/All Clubs 2017.csv',
         2018 : 'P:/League Wide Programs/MLB/Start of Year Rosters/All Clubs 2018.csv'}
years = [2016, 2017, 2018]
claim_types = ['60 Days', '90 Days', '120 Days', '186 Days']
season_days = {2016 : 183, 2017 : 183, 2018 : 186}
insurance_constant = .75

################################################################################
main_file = 'P:/MLB Python/CSV Files/MLB Entries.csv'
main = pd.read_csv(Path(main_file))
possible = set(np.array(main['Player ID']).tolist())

season_dates = pd.read_csv(Path('P:/MLB Python/CSV Files/MLB Season Dates.csv'))
season_dates['startDate'] = pd.to_datetime(season_dates['startDate'])
season_dates['endDate'] = pd.to_datetime(season_dates['endDate'])
start_end_dates = dict()
all_season_dates = []
for index, row in season_dates.iterrows():
    all_season_dates.extend(list(pd.date_range(start = row['startDate'], end = row['endDate'])))
    start_end_dates[row['yearOfSeason']] = [row['startDate'], row['endDate']]
################################################################################

def get_claim_days(player, year, claim_type):
    claim_days = 0
    if(player not in possible): return claim_days
    deductible = int(claim_type.split(' ')[0])
    player_claims = mb.player_claims(player, deductible)
    season_start, season_end = start_end_dates
    for claim in player_claims:
        player, injury, start, eligible, recurrent, games = player_claims[claim]
        if(eligible <= season_start and eligible >= season_end):
            # Player becomes eligible during season and does not meet recurrent in given season
            if(pd.isna(recurrent) or recurrent >= season_end): claim_days = season_end - eligible
            # Player becomes eligible during season and meets recurrent in same season
            else: claim_days = games
        elif(pd.isna(recurrent)):
            # Player was eligible before season and recurrent is not met in given season
            if(eligible <= season_start): return season_end - season_start
        elif(recurrent <= recurrent_end and recurrent >= season_start):
            # Player was eligible before season and meets recurrent during given season
            if(not pd.isna(recurrent)): claim_days = recurrent - season_start
    return claim_days

def format_sheet(main, claim_types):
    for claim_type in claim_types:
        main[claim_type] = 0
        main[claim_type.split(' ')[0] + ' ' + 'Payed'] = 0
    return main

def calculate_insurance(year, files, claim_types):
    # main = format_sheet(pd.read_csv(Path(files[year])), claim_types)
    main = pd.read_csv(Path(files[year]))
    for index, row in main[10:].iterrows():
        print(index)
        if(row['PlayerID'] not in possible): continue
        if(pd.isnull(row['Current Salary'])): continue
        for claim_type in claim_types:
            claim_days = get_claim_days(row['PlayerID'], year, claim_type)
            if(claim_days != 0):
                if(isinstance(claim_days, (int, float))): days = claim_days
                else: days = claim_days.days
                main.at[index, claim_type] = days
                main.at[index, claim_type.split(' ')[0] + ' ' + 'Payed'] = row['Current Salary'] / season_days[year] * insurance_constant * days
        main.to_csv(Path(files[year]), index = False)
    main.to_csv(Path(files[year]))
    return

def main(years, files, claim_types):
    calculate_insurance(2016, files, claim_types)
    return

main(years, files, claim_types)
