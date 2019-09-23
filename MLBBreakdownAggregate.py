import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
import decimal
import math
from datetime import datetime as dt
from pathlib import Path
import timeit
import os
import MLBBreakdown as mb
import timeline

# List of players to be evaluated
input_players = [81849] #203729] # , 81849, 81350, 302128, 339696, 404748]
# Includes policy information on each player
players_information = {203729 : [60, 30, 45], 81849 : [60, 30, 45], 81350 : [60, 30, 45], 302128 : [60, 30, 45], 339696 : [60, 30, 45], 404748 : [60, 30, 45]}
# Main entries file
main_file = 'P:/MLB Python/MLB Entries.csv'
# Variable accounts for writing the player date to their individual folders
write_date = False
# Specifies if only the first eligible claim date should be kept
keep_first = True

# Data on season dates
season_dates = pd.read_csv(Path('P:/MLB Python/MLB Season Dates.csv'))
season_dates['startDate'] = pd.to_datetime(season_dates['startDate'])
season_dates['endDate'] = pd.to_datetime(season_dates['endDate'])
start_end_dates = []
all_season_dates = []
start_dates = []
end_dates = []

for index, row in season_dates.iterrows():
    all_season_dates.extend(list(pd.date_range(start = row['startDate'], end = row['endDate'])))
    start_end_dates.append([row['startDate'], row['endDate']])
    start_dates.append(row['startDate'])
    end_dates.append(row['endDate'])

# Main call to run program
def main(data, players):
    print('MAIN')
    main_file = pd.read_csv(Path(data))
    main_file['Placed On'] = pd.to_datetime(main_file['Placed On'])
    main_file['Reinstated On'] = pd.to_datetime(main_file['Reinstated On'])
    timeline_evaluate_all_players(main_file, players)
    return

def create_timeline(format, player_file):
    print('CREATETIMELINE')
    recurrent_met_dates = []
    eligible_dates = []
    injury_indicies = []
    claim_endpoints = []
    injury_endpoints = []

    for value in format:
        eligible_dates.append(str(format[value][3]).split(' ')[0])
        val = (str(format[value][4]).split(' ')[0], str(format[value][5]))
        recurrent_met_dates.append(val)
        if(type(format[value][1]) == list): injury_indicies.extend(format[value][1])
        else: injury_indicies.append(format[value][1])
        claim_endpoints.append([format[value][2], format[value][3], format[value][4]])

    injuries = []
    player_file = player_file.sort_values(by = ['Placed On'])
    print('HERE', injury_indicies)
    for index, row in player_file.iterrows():
        injury = player_file.loc[index]['Injury']
        sta = player_file.loc[index]['Placed On']
        en = player_file.loc[index]['Reinstated On']
        injuries.append([injury, pd.to_datetime(sta, format = '%Y %M %D'), pd.to_datetime(en, format = '%Y %M %D')])
        if(index not in injury_indicies):
            print('HERE', index)
            injury_endpoints.append([sta, en])
    print('HERE', injury_endpoints)

    for info in injuries:
        if(info[1] not in all_season_dates):
            year = info[1].year
            index = pd.Index(season_dates['yearOfSeason']).get_loc(year)
            info[1] = pd.to_datetime(season_dates.iloc[index]['startDate'], format = '%Y %M %D')
        if(info[2] not in all_season_dates):
            current_year = info[2].year
            current_index = pd.Index(season_dates['yearOfSeason']).get_loc(current_year)
            info[2] = pd.to_datetime(season_dates.iloc[current_index]['endDate'], format = '%Y %M %D')

    counter = 0
    while(counter != len(injuries) - 1):
        first = injuries[counter]
        second = injuries[counter + 1]
        if(first[2] in end_dates and second[1] in start_dates and first[0] == second[0]):
            injuries[counter] = [first[0], first[1], second[2]]
            injuries.pop(counter + 1)
        else: counter += 1
    print('PLOTSTEM')
    timeline.plot_stem(eligible_dates, recurrent_met_dates, injuries, str(player_file.iloc[0]['Player']) + ': Timeline', start_dates, end_dates, claim_endpoints, injury_endpoints)

def format_injury_set(injuries):
    result = []
    for item in injuries:
        result.append(item)
    return result

def aggregate_format_player(player, player_sheet):
    result = dict()
    counter = 0
    for item in player_sheet['All Injuries']:
        result[counter] = [player, format_injury_set(item[4]), item[0], item[1], item[2], item[3]]
        counter += 1
    return result

def compile_injuries(value, injury_file, player_file):
    injuries = set()
    injury_range = pd.DatetimeIndex(start = pd.to_datetime(value[0]), end = pd.to_datetime(value[2]), freq = 'D')
    for index, row in player_file.iterrows():
        if(not injury_range.intersection(pd.DatetimeIndex(start = row['Placed On'], end = row['Reinstated On'], freq = 'D')).empty): # != pd.DatetimeIndex([])):
            injuries.add(index)
    value.append(injuries)
    return value

def aggregate_evaluate_injuries(player_file, player_dates, player):
    claim_dates = []
    for index, row in player_file.iterrows():
        value = row['Reinstated On'] - pd.to_timedelta('24 Hours')
        for item in start_end_dates:
            if(row['Reinstated On'] >= item[1] and row['Reinstated On'] < item[0]): value = row['Reinstated On']
        claim_dates.extend(list(pd.date_range(start = row['Placed On'], end = value)))
    player_dates['Injured'] = player_dates['Dates'].apply(lambda x: 1 if x in claim_dates else 0)
    player_dates['Claim'] = player_dates[['Injured', 'Season']].apply(lambda x: 1 if (x[0] == 1) & (x[1] == 1) else 0, axis = 1)
    player_dates['Recurrent'] = player_dates[['Out', 'Season']].apply(lambda x: 1 if (x[0] == 0) & (x[1] == 1) else 0, axis = 1)
    injury_claims = get_claim_indicies(player_dates, player, player_file)
    return injury_claims
    player_dates.to_csv(Path('P:/MLB Python/Test.csv'))

# Creates folders for players if they are not yet present
def create_folder(player):
    if not os.path.exists('P:/MLB Python/' + str(player)):
        os.makedirs('P:/MLB Python/' + str(player))
    return

# Locates dates where recurrent days were met and calculates sum of claim days
def apply_recurrent(start_end, test, player):
    recurrent_sum_index = pd.Index((test['Recurrent'] == 1).cumsum())
    recurrent_index = recurrent_sum_index.searchsorted(players_information[player][2])
    if(recurrent_index >= len(recurrent_sum_index)):
        start_end.append(np.nan)
        start_end.append(len(test[test['Claim'] == 1]) - players_information[player][0])
    else:
        claim_games_test = test.iloc[:recurrent_index]
        claim_games = len(claim_games_test[claim_games_test['Claim'] == 1]) - players_information[player][0]
        start_end.append(test.iloc[recurrent_index]['Dates'])
        start_end.append(claim_games)
    return start_end

# Compiles list informaton into a player dictionary
def format_player(player, injury_dates):
    result = dict()
    counter = 0
    for injury in injury_dates:
        for item in injury_dates[injury]:
            result[counter] = [player, injury, item[0], item[1], item[2], item[3]]
            counter += 1
    return result

# Tests the recurrent day sum was not met before a player claim was eligible
def recurrent_sum(possible_window, player):
    recurrent_sum_index = pd.Index((possible_window['Recurrent'] == 1).cumsum())
    recurrent_sum_index_first = recurrent_sum_index.searchsorted(players_information[player][2])
    if(recurrent_sum_index_first >= len(recurrent_sum_index)): return True
    else: return False

# Tests that a certain number of days are consecutive according to policy
def consecutive(possible_window, player):
    consecutive = list(possible_window['Injured'])
    word = ''.join(str(num) for num in consecutive)
    word_test = '1' * players_information[player][1]
    if(word_test in word): return True
    else: return False

# Evaulates each index where a claim may have started
def possible_claim(injury_file, index, player):
    start_end = []
    test = injury_file[index:]
    claim_sum_index = pd.Index((test['Claim'] == 1).cumsum())
    claim_sum_index_first = claim_sum_index.searchsorted(players_information[player][0])
    if(claim_sum_index_first >= len(claim_sum_index)): return [-1]
    else:
        possible_window = test[:claim_sum_index_first]
        if(recurrent_sum(possible_window, player) and consecutive(possible_window, player)):
            start_end.append(test.iloc[0]['Dates'])
            start_end.append(test.iloc[claim_sum_index_first]['Dates'])
            start_end = apply_recurrent(start_end, test, player)
            return start_end
        else: return [-1]

# Gets all indicies where a claim may start
def get_claim_indicies(injury_file, player, player_file):
    claims = []
    indicies = injury_file.index[injury_file['Claim'] == 1]
    index_file = injury_file[injury_file['Claim'] == 1]
    while(not index_file.empty):
        index = index_file.index[0]
        value = possible_claim(injury_file, index, player)
        if(value[0] == -1):
            index_file = index_file[1:]
        else:
            value = compile_injuries(value, injury_file, player_file)
            index_file = index_file[index_file['Dates'] > value[2]]
            claims.append(value)
        index_file = index_file[index_file['Claim'] == 1]
    return claims

# Applies a mask to the players main injury file
def main_dates(player_file, player):
    dates = pd.date_range(start = player_file['Placed On'].min(), end = pd.to_datetime('today'))
    injury_dates = dates.to_frame(name = 'Dates')
    claim_dates = []
    for index, row in player_file.iterrows():
        claim_dates.extend(list(pd.date_range(start = row['Placed On'], end = row['Reinstated On'])))
    injury_dates['Out'] = injury_dates['Dates'].apply(lambda x: 1 if x in claim_dates else 0)
    injury_dates['Season'] = injury_dates['Dates'].apply(lambda x: 1 if x in all_season_dates else 0)
    if(write_date == True): injury_dates.to_csv(Path('P:/MLB Python/' + str(player) + '/Dates.csv'))
    return injury_dates

# Applies a mask to the individual injury files
def format_dates(injury_file, player_dates, injury, player):
    claim_dates = []
    for index, row in injury_file.iterrows():
        value = row['Reinstated On'] - pd.to_timedelta('24 Hours')
        for item in start_end_dates:
            if(row['Reinstated On'] >= item[1] and row['Reinstated On'] < item[0]): value = row['Reinstated On']
        claim_dates.extend(list(pd.date_range(start = row['Placed On'], end = value)))
    player_dates['Injured'] = player_dates['Dates'].apply(lambda x: 1 if x in claim_dates else 0)
    player_dates['Claim'] = player_dates[['Injured', 'Season']].apply(lambda x: 1 if (x[0] == 1) & (x[1] == 1) else 0, axis = 1)
    player_dates['Recurrent'] = player_dates[['Out', 'Season']].apply(lambda x: 1 if (x[0] == 0) & (x[1] == 1) else 0, axis = 1)
    if(write_date == True): player_dates.to_csv(Path('P:/MLB Python/' + str(player) + '/' + str(injury).replace('/', ' ') + ' Dates.csv'))
    return player_dates

# Called on each injury
def evaluate_injury(player_file, player_dates, injury, player):
    injury_file = player_file[player_file['Injury'] == injury]
    if(write_date == True): injury_file.to_csv(Path('P:/MLB Python/' + str(player) + '/' + str(injury).replace('/', ' ') + '.csv'))
    injury_dates = format_dates(injury_file, player_dates, injury, player)
    injury_claims = get_claim_indicies(injury_dates, player, player_file)
    return injury_claims

# Called on each player
def evaluate_player(player_file, player):
    injuries = dict()
    player_file['Injury'] = player_file['Body Side'] + ' ' + player_file['Body Part'] + ' ' + player_file['Detail']
    player_file['Injury'] = player_file['Injury'].apply(lambda x: x.replace('/', '-'))
    player_dates = main_dates(player_file, player)
    injuries['All Injuries'] = aggregate_evaluate_injuries(player_file, player_dates, player)
    return injuries

# Simplifies main entries to a player file
def create_player_file(main_file, player):
    player_file = main_file[main_file['Player ID'] == player]
    return player_file

# Loops through each player, compiling all evaulations into a result frame
def evaluate_all_players(main_file, players):
    result_frame = pd.DataFrame(columns = ['Name', 'Injury', 'Start Date', 'Eligible Date', 'Recurrent Met Date', 'Claim Games'])
    for player in players:
        create_folder(player)
        player_file = create_player_file(main_file, player)
        player_sheet = evaluate_player(player_file, player)
        format = aggregate_format_player(player, player_sheet)
        temporary = pd.DataFrame.from_dict(format, orient = 'index', columns = ['Name', 'Injury', 'Start Date', 'Eligible Date', 'Recurrent Met Date', 'Claim Games'])
        result_frame = result_frame.append(temporary, ignore_index = True)
    if(keep_first): result_frame = result_frame.drop_duplicates(subset = ['Name', 'Injury'], keep = 'first').sort_values(by = ['Name', 'Claim Games'], ascending = False).reset_index(drop = True)
    # Information is put in a comma separated values directory
    result_frame.to_csv(Path('P:/MLB Python/Result Aggregate.csv'))
    return

def timeline_evaluate_all_players(main_file, players):
    print('TIMELINEEVALALLPLAYERS')
    result_frame = pd.DataFrame(columns = ['Name', 'Injury', 'Start Date', 'Eligible Date', 'Recurrent Met Date', 'Claim Games'])
    for player in players:
        create_folder(player)
        player_file = create_player_file(main_file, player)
        player_sheet = evaluate_player(player_file, player)
        format = aggregate_format_player(player, player_sheet)
        create_timeline(format, player_file)
        temporary = pd.DataFrame.from_dict(format, orient = 'index', columns = ['Name', 'Injury', 'Start Date', 'Eligible Date', 'Recurrent Met Date', 'Claim Games'])
        result_frame = result_frame.append(temporary, ignore_index = True)
    if(keep_first): result_frame = result_frame.drop_duplicates(subset = ['Name', 'Injury'], keep = 'first').sort_values(by = ['Name', 'Claim Games'], ascending = False).reset_index(drop = True)
    # Information is put in a comma separated values directory
    result_frame.to_csv(Path('P:/MLB Python/Result Aggregate.csv'))
    return

main(main_file, input_players)
