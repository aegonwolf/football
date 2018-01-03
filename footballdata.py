# -*- coding: utf-8 -*-
"""
Created on Thu Dec 28 19:05:38 2017

@author: Oliver
"""

import pandas as pd
import os
from datetime import datetime as dt
import itertools

team_and_goals = ["Date", "AwayTeam", "HomeTeam", "FTHG", "FTAG", "FTR"]
team_game_stats = ["Date", "AwayTeam", "HomeTeam", "FTR", "HS", "AS", "HST", "AST", "HC", "AC", "HF", "AF", "HO", "AO"]
game_odds = ["Date", "IWH", "IWD", "IWA", "LBH", "LBD", "LBA", "WHH", "WHD", "WHA"]

def parse_date(date):
    if date == '':
        return None
    else:
        try:
            return dt.strptime(date, '%d/%m/%y').date()
        except:
            return dt.strptime(date, '%d/%m/%Y').date()


#read all files in folder

def read_files(folder):
    files = os.listdir(folder)
    #leave the latest season
    files = files[:-1]
    allfiles = []
    for file in files:
        try:
            allfiles.append(pd.read_csv(folder+ file)[team_and_goals])
        except:
            try:
                allfiles.append(pd.read_csv(folder + file, sep='delimiter', encoding='Latin1')[team_and_goals])
                #if this can't solve just skip the file, the data is season by season anyway
                #whole point of this was quickly get as much data as possible
            except:
                pass
    
    #unify dates
    for file in allfiles:
        try:
            file.Date = file.Date.apply(parse_date)
        except:
            print("Fix csv file: " +  file) #I found that the files have some invisible lines or just errors, opening them in libre office and resaving fixes this error
    return allfiles

def read_odds(folder):
    files = os.listdir(folder)
    #leave the latest season
    files = files[:-1]
    allfiles = []
    for file in files:
        try:
            allfiles.append(pd.read_csv(folder+ file)[game_odds])
        except:
            allfiles.append(pd.read_csv(folder + file, encoding='Latin1')[game_odds])
    
    #unify dates
    for file in allfiles:
        file.Date = file.Date.apply(parse_date)
    return allfiles

def get_data_by_teams(data, matchweek, teams):
    #create a dictionary with teams
    teams_gs = dict()
    teams_gc = dict()
    for i in data.groupby("HomeTeam").mean().T.columns:
        teams_gs[i] = [] #goals scored
        teams_gc[i] = [] #goals conceded
        
    for i in range(len(data)):
        home_goals = data.iloc[i]['FTHG']
        away_goals = data.iloc[i]['FTAG']
        teams_gs[data.iloc[i].HomeTeam].append(home_goals)
        teams_gc[data.iloc[i].HomeTeam].append(away_goals)
        teams_gs[data.iloc[i].AwayTeam].append(away_goals)
        teams_gc[data.iloc[i].AwayTeam].append(home_goals)
        
    goals_scored = pd.DataFrame(data=teams_gs, index = [i for i in range(1, matchweek)]).T
    gs = pd.DataFrame(data=teams_gs, index = [i for i in range(1, matchweek)]).T
    gs[0] = 0
    goals_scored[0] = 0
    goals_conceded = pd.DataFrame(data=teams_gc, index = [i for i in range(1, matchweek)]).T   
    gc = pd.DataFrame(data=teams_gc, index = [i for i in range(1, matchweek)]).T
    gc[0] = 0
    goals_conceded[0] = 0
    #Total Goals Scored, Conceded
    for i in range(2, matchweek):
        goals_scored[i] = goals_scored[i] + goals_scored[i-1]
        goals_conceded[i] = goals_conceded[i] + goals_conceded[i-1]
        
    #3 Game Average
    three_game_gscored = pd.DataFrame(data=teams_gs, index = [i for i in range(1, matchweek)]).T
    three_game_gscored[0] = 0
    three_game_gscored[2] += gs[1] 
    three_game_goals_conceded = pd.DataFrame(data=teams_gc, index = [i for i in range(1, matchweek)]).T
    three_game_goals_conceded[0] = 0
    three_game_goals_conceded[2] += gc[1] 
    #print(gs[1] + gs[2] + gs[0])
    for i in range(3, matchweek):
        three_game_gscored[i] = (gs[i-1] + gs[i-2]+ gs[i-3])
        three_game_goals_conceded[i] = (gc[i-1] + gc[i-2] + gc[i-3])
           
    j = 0
    HTGS = []
    ATGS = []
    HTGC = []
    ATGC = []
    HomeTGAGS = []
    AwayTGAGS = []
    HomeTGAGC = []
    AwayTGAGC = []

    for i in range(len(data)):
        ht = data.iloc[i].HomeTeam
        at = data.iloc[i].AwayTeam
        HTGS.append(goals_scored.loc[ht][j])
        ATGS.append(goals_scored.loc[at][j])
        HTGC.append(goals_conceded.loc[ht][j])
        ATGC.append(goals_conceded.loc[at][j])
        HomeTGAGS.append(three_game_gscored.loc[ht][j])
        AwayTGAGS.append(three_game_gscored.loc[at][j])
        HomeTGAGC.append(three_game_goals_conceded.loc[ht][j])
        AwayTGAGC.append(three_game_goals_conceded.loc[at][j])
        
        
        if ((i + 1)% (teams / 2)) == 0: #1 Matchday two teams
            j = j + 1
        
    data['HTGS'] = HTGS
    data['ATGS'] = ATGS
    data['HTGC'] = HTGC
    data['ATGC'] = ATGC
    data['HomeTGAGS'] = HomeTGAGS
    data['AwayTGAGS'] = AwayTGAGS
    data['HomeTGAGC'] = HomeTGAGC
    data['AwayTGAGC'] = AwayTGAGC
    
    return data


        
        
def get_points(result):
    if result == 'W':
        return 3
    elif result == 'D':
        return 1
    else:
        return 0
    

def get_cuml_points(matchres, matchweeks, teams):
    matchres_points = matchres.applymap(get_points)
    for i in range(2, matchweeks):
        matchres_points[i] = matchres_points[i] + matchres_points[i-1]
        
    matchres_points.insert(column =0, loc = 0, value = [0*i for i in range(teams)])
    return matchres_points


def get_matchres(playing_stat, matchweeks):
    # Create a dictionary with team names as keys
    teams = {}
    for i in playing_stat.groupby('HomeTeam').mean().T.columns:
        teams[i] = []

    # the value corresponding to keys is a list containing the match result
    for i in range(len(playing_stat)):
        if playing_stat.iloc[i].FTR == 'H':
            teams[playing_stat.iloc[i].HomeTeam].append('W')
            teams[playing_stat.iloc[i].AwayTeam].append('L')
        elif playing_stat.iloc[i].FTR == 'A':
            teams[playing_stat.iloc[i].AwayTeam].append('W')
            teams[playing_stat.iloc[i].HomeTeam].append('L')
        else:
            teams[playing_stat.iloc[i].AwayTeam].append('D')
            teams[playing_stat.iloc[i].HomeTeam].append('D')
            
    return pd.DataFrame(data=teams, index = [i for i in range(1,matchweeks)]).T

def get_agg_points(playing_stat, matchweeks, teams):
    matchres = get_matchres(playing_stat, matchweeks)
    cum_pts = get_cuml_points(matchres, matchweeks, teams)
    HTP = []
    ATP = []
    j = 0
    for i in range(len(playing_stat)):
        ht = playing_stat.iloc[i].HomeTeam
        at = playing_stat.iloc[i].AwayTeam
        HTP.append(cum_pts.loc[ht][j])
        ATP.append(cum_pts.loc[at][j])

        if ((i + 1)% (teams/2)) == 0: #all teams played once, hence one matchweek is teams / 2
            j = j + 1
            
    playing_stat['HTP'] = HTP
    playing_stat['ATP'] = ATP
    return playing_stat

def get_form(playing_stat,num, matchweeks):
    form = get_matchres(playing_stat, matchweeks)
    form_final = form.copy()
    for i in range(num,matchweeks):
        form_final[i] = ''
        j = 0
        while j < num:
            form_final[i] += form[i-j]
            j += 1           
    return form_final

def add_form(playing_stat,num, matchweeks):
    form = get_form(playing_stat,num, matchweeks)
    h = ['M' for i in range(num * 10)]  # since form is not available for n MW (n*10)
    a = ['M' for i in range(num * 10)]
    
    j = num
    for i in range((num*10),len(playing_stat)):
        ht = playing_stat.iloc[i].HomeTeam
        at = playing_stat.iloc[i].AwayTeam
        
        past = form.loc[ht][j]               # get past n results
        h.append(past[num-1])                    # 0 index is most recent
        
        past = form.loc[at][j]               # get past n results.
        a.append(past[num-1])                   # 0 index is most recent
        
        if ((i + 1)% 10) == 0:
            j = j + 1

    playing_stat['HM' + str(num)] = h                 
    playing_stat['AM' + str(num)] = a

    
    return playing_stat


def add_form_df(playing_statistics, matchweeks):
    for i in range(1, 6):
        playing_statistics = add_form(playing_statistics, i, matchweeks)
    return playing_statistics    
    
Standings = pd.read_csv("Football/data/Datasets/EPLStandings.csv")

def get_last(playing_stat, Standings, year, teams):
    Standings = pd.read_csv(Standings)
    Standings.set_index(['Team'], inplace=True)
    Standings = Standings.fillna(teams)

    HomeTeamLP = []
    AwayTeamLP = []
    for i in range(len(playing_stat)):
        ht = playing_stat.iloc[i].HomeTeam
        at = playing_stat.iloc[i].AwayTeam
        HomeTeamLP.append(Standings.loc[ht][year])
        AwayTeamLP.append(Standings.loc[at][year])
    playing_stat['HomeTeamLP'] = HomeTeamLP
    playing_stat['AwayTeamLP'] = AwayTeamLP
    return playing_stat

def get_mw(playing_stat):
    j = 1
    MatchWeek = []
    for i in range(len(playing_stat)):
        MatchWeek.append(j)
        if ((i + 1)% 10) == 0:
            j = j + 1
    playing_stat['MW'] = MatchWeek
    return playing_stat

        
        
        
# Get Goal Difference
def get_goal_diff(playing_stat):
    

    playing_stat['HTGD'] = playing_stat['HTGS'] - playing_stat['HTGC']
    playing_stat['ATGD'] = playing_stat['ATGS'] - playing_stat['ATGC']

    return playing_stat

def get_diff_pts(playing_stat):
    playing_stat['DiffPts'] = playing_stat['HTP'] - playing_stat['ATP']
    #playing_stat['DiffFormPts'] = playing_stat['HTFormPts'] - playing_stat['ATFormPts']
    return playing_stat
    

#Scale by Matchweek

def scale_by_mw(playing_stat):
    cols = ['HTGD','ATGD','DiffPts','HTP','ATP']
    scale_by_three = ['HomeTGAGS', 'AwayTGAGS', 'HomeTGAGC', 'AwayTGAGC']
    playing_stat.MW = playing_stat.MW.astype(float)
    
    for col in cols:
        playing_stat[col] = playing_stat[col] / playing_stat.MW
    for col in scale_by_three:
        playing_stat[col] = playing_stat[col] / 3.0
    return playing_stat



def replace_nan_odds(dataset):
    dataset = dataset.fillna(0)
    row = []
    index = 0 
    #Find missing odds
    for i in dataset.IWH:
        if i == 0:
            row.append(index)
        index += 1
    #replace missing odds
    for i in row:
        if dataset.LBH.iloc[i] != 0:
            dataset.IWH.iloc[i] = dataset.LBH.iloc[i]
        else:
            if dataset.WHH.iloc[i] != 0:
                
                dataset.IWH.iloc[i] = dataset.WHH.iloc[i]
            else:
                print('This one is missing', i)
    return dataset



def get_data(folder, matchweeks, teams, standings):
    allfiles = read_files(folder)
    i = 0
    for file in allfiles:
        file = get_data_by_teams(file, matchweeks, teams)
        file = get_agg_points(file, matchweeks, teams)
        file = get_goal_diff(file)
        file = add_form_df(file, matchweeks)
        file = get_diff_pts(file)
        file = get_mw(file)
        file = scale_by_mw(file)
        file = get_last(file, standings, i, teams)
        i += 1
    complete = pd.concat(allfiles)
    return complete


#create a csv file with all teams and their standings in those years.
#note that for that data that you have year-1 has to be added manually if you need for the last years position as those will not be in the data
# or you remove the first file after running it through this function
# or you figure something else out entirely :-D
def create_standings(folder, savefile):
    allfiles = read_files(folder)
    tables = []
    for file in allfiles:
        teams = dict()
        for team in file.HomeTeam.unique():
            teams[team] = 0
    
        for i in range(len(file)):
            if file.FTR.iloc[i] == 'H':
                teams[file.HomeTeam.iloc[i]] += 3
            if file.FTR.iloc[i] == 'A':
                teams[file.AwayTeam.iloc[i]] += 3
            elif file.FTR.iloc[i] == 'D':
                teams[file.HomeTeam.iloc[i]] += 1
                teams[file.AwayTeam.iloc[i]] += 1
        standings = pd.DataFrame.from_dict(teams, orient='index')
        standings.columns = ['Pts']
        standings = standings.sort_values('Pts', ascending=False)
        standings['Position'] = 0
        
        for i in range(len(standings)):
            standings.Position.iloc[i] = i+1
        table = pd.DataFrame(index=standings.index)
        table[file.Date.iloc[-1].year] = standings.Position
        tables.append(table)
    complete_standings = pd.concat(tables, axis=1)
    complete_standings.to_csv(savefile)
    return pd.concat(tables, axis=1)
            

def get_odds_data(folder):
    allfiles = read_odds(folder)
    data = pd.concat(allfiles)
    data = replace_nan_odds(data)
    return data
        
    
