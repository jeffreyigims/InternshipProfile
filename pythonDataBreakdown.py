import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
import decimal
import math
from datetime import datetime
from pathlib import Path
import timeit

# Adjusts main file to make it more simple
def adjust_main(file):
    all_categories = pd.read_csv(file)
    simple = all_categories[['Team', 'Name', 'Date', 'Stats', 'Injured?', 'Played in Game?']]
    simple['Date'] = pd.to_datetime(simple['Date'])
    simple = simple[pd.notnull(simple['Name'])]
    return simple

# Creates and writes a main player file
def create_player_file(file, player):
    player_file = file[file['Name'] == player].sort_values(by = 'Date').reset_index(drop = True)
    # path = Path('P:/NBA Injuries Python Breakdown/Player Files/' + player + '/Main.csv')
    # player_file.to_csv(path)
    return player_file

# Creates and writes a specific injury file to a players folder
def injury_mask(injury, player_file, player):
    injury_file = player_file
    injury_file['Claim Count'] = injury_file['Stats'].apply(lambda x: 'Yes' if x == injury else 'No')
    injury_file['Against Claim'] = injury_file['Injured?'].apply(lambda x: 'Yes' if x == 0 else 'No')
    injury_file = injury_file.sort_values(by = 'Date').reset_index(drop = True)
    # path = Path('P:/NBA Injuries Python Breakdown/Player Files/' + player + '/' + injury + '.csv')
    # injury_file.to_csv(path)
    return injury_file

# Checks if a claim is possible from a certain starting index
def possible_claim(injury_file, index, player_information):
    start_end = []
    test = injury_file.iloc[index:index + player_information[0]]
    played_sum_index = pd.Index((test['Against Claim'] == 'Yes').cumsum())
    claim_sum_index = pd.Index((test['Claim Count'] == 'Yes').cumsum())
    played_sum_index_first = played_sum_index.searchsorted(player_information[2])
    claim_sum_index_first = claim_sum_index.searchsorted(player_information[1])
    # Claim is not possible because claim days are not met
    if(claim_sum_index_first >= len(claim_sum_index)): return [-1] # return False
    # Claim days are met and are less than healthy games played
    elif(claim_sum_index_first < played_sum_index_first):
        start_end = [injury_file.iloc[index]['Date'], injury_file.iloc[index + claim_sum_index_first]['Date']]
        find_recurrent = injury_file.iloc[index:]
        recurrent_sum_index = pd.Index(((find_recurrent['Against Claim'] == 'Yes') | (find_recurrent['Injured?'] == 0)).cumsum())
        recurrent_index = recurrent_sum_index.searchsorted(player_information[2])
        if(recurrent_index >= len(recurrent_sum_index)):
            # Creates frame after index to the end of the file and sums the number of claim games
            claim_games_test = injury_file.iloc[index + claim_sum_index_first + 1:]
            claim_games = len(claim_games_test[claim_games_test['Claim Count'] == 'Yes'])
            start_end.append(np.nan)
            start_end.append(claim_games)
        else:
            # Creates frame from first index to index of recurrent goal, sums all claim games, and subtracts those covered by team
            claim_games_test = find_recurrent.iloc[:recurrent_index]
            claim_games = len(claim_games_test[claim_games_test['Claim Count'] == 'Yes']) - player_information[1]
            start_end.append(find_recurrent.iloc[recurrent_index]['Date'])
            start_end.append(claim_games)
        return start_end
    else: return [-1]

# Calculates and checks each possible index where a claim may start
def get_claim_indicies(injury_file, player_information):
    claims = []
    indicies = injury_file.index[injury_file['Claim Count'] == 'Yes']
    index_file = injury_file[injury_file['Claim Count'] == 'Yes']
    while(not index_file.empty):
        index = index_file.index[0]
        value = possible_claim(injury_file, index, player_information)
        if(value[0] == -1): index_file = index_file[1:]
        else:
            if(pd.isna(value[2])):
                value.append(injury_file.copy(deep = True))
                claims.append(value)
                break
            else:
                index_file = index_file[index_file['Date'] > value[2]]
                value.append(injury_file.copy(deep = True))
                claims.append(value)
        index_file = index_file[index_file['Claim Count'] == 'Yes']
    return claims

# Checks one player file for all possible injuries
def check_player(player_file, player, player_information):
    all_injuries = dict()
    player_injuries = player_file[player_file['Injured?'] == 1]
    unique_injuries = player_injuries['Stats'].unique()
    for injury in unique_injuries:
        injury_file = injury_mask(injury, player_file, player)
        all_injuries[injury] = get_claim_indicies(injury_file, player_information)
    dates = pd.date_range(start = '10/27/2015', end = pd.to_datetime('today'))
    all_injury_file = dates.to_frame(name = 'Dates')
    for injury in unique_injuries:
        all_injury_file[injury] = np.nan
        for dates in all_injuries[injury]:
            all_injury_file.at[dates[1], injury] = dates[0]
    # path = Path('P:\NBA Injuries Python Breakdown/Player Files/' + player + '/All Injury File.csv')
    # all_injury_file.to_csv(path)
    return(all_injuries)

# Formats player dictionary so it can be added to the result frames
def format_player(player, injury_dates):
    result = dict()
    counter = 0
    for injury in injury_dates:
        for item in injury_dates[injury]:
            result[counter] = [player, injury, item[0], item[1], item[2], item[3]] # , item[4]]
            counter += 1
    return result

# Checks all players for all of the possible injuries
def check_all_players(simple_file, players, player_information):
    result_frame = pd.DataFrame(columns = ['Name', 'Injury', 'Start Date', 'Eligible Date', 'Recurrent Met Date', 'Claim Games'])
    players = set(simple_file['Name'].tolist())
    print(players)
    print(len(players))
    for player in players:
        player_file = create_player_file(simple_file, player)
        format = format_player(player, check_player(player_file, player, player_information))
        temporary = pd.DataFrame.from_dict(format, orient = 'index', columns = ['Name', 'Injury', 'Start Date', 'Eligible Date', 'Recurrent Met Date', 'Claim Games'])
        result_frame = result_frame.append(temporary, ignore_index = True)
    path = Path('P:/NBA Injuries Python Breakdown/Player Files/Result.csv')
    # result_frame.to_csv(path)
    return format

# Main file to execute program
def main(players, claim_type):
    path = Path('P:/NBA Injuries Python Breakdown/Categories.csv')
    simple = adjust_main(path)
    if(claim_type == 'Half Season'): player_information = [164, 41, 41]
    elif(claim_type == 'Third Season'): player_information = [164, 27, 41]
    elif(claim_type == 'Standard Season'): player_information = [164, 20, 41]
    else: player_information = [164, 20, 41]
    value = check_all_players(simple, players, player_information)
    return value

main(['CHANDLER PARSONS',
], 'Half Season')
