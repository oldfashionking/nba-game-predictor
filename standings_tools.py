from basketball_reference_web_scraper import client

from basketball_reference_web_scraper import client
from collections import defaultdict
import pandas as pd
from datetime import datetime, timezone, timedelta
from itertools import product

"""获取NBA战绩（包括当前赛季的胜场、负场及胜率）"""
def get_nba_standings(season_end_year=2025):
    # 获取 2025 赛季赛程（包含已完成和未来比赛）
    schedule = client.season_schedule(season_end_year=season_end_year)
    
    # 获取当前时间（UTC）
    now = datetime.now(timezone.utc) - timedelta(hours=4)
    # 初始化字典存储战绩
    team_records = defaultdict(lambda: {"wins": 0, "losses": 0})

    # NBA 分区字典（手动设置每支球队的分区）
    team_conferences = {
        "ATLANTA HAWKS": "East", "BOSTON CELTICS": "East", "BROOKLYN NETS": "East", "CHARLOTTE HORNETS": "East", 
        "CHICAGO BULLS": "East", "CLEVELAND CAVALIERS": "East", "DETROIT PISTONS": "East", "INDIANA PACERS": "East", 
        "MIAMI HEAT": "East", "MILWAUKEE BUCKS": "East", "NEW YORK KNICKS": "East", "ORLANDO MAGIC": "East", 
        "PHILADELPHIA 76ERS": "East", "TORONTO RAPTORS": "East", "WASHINGTON WIZARDS": "East",
        "DALLAS MAVERICKS": "West", "DENVER NUGGETS": "West", "GOLDEN STATE WARRIORS": "West", "HOUSTON ROCKETS": "West",
        "LOS ANGELES CLIPPERS": "West", "LOS ANGELES LAKERS": "West", "MINNESOTA TIMBERWOLVES": "West", "NEW ORLEANS PELICANS": "West", 
        "OKLAHOMA CITY THUNDER": "West", "PHOENIX SUNS": "West", "PORTLAND TRAIL BLAZERS": "West", "SACRAMENTO KINGS": "West",
        "SAN ANTONIO SPURS": "West", "UTAH JAZZ": "West", "MEMPHIS GRIZZLIES": "West", "SACRAMENTO KINGS": "West",
        "PHOENIX SUNS": "West"
    }

    # 遍历赛程，统计战绩（仅统计已完成的比赛）
    for game in schedule:
        if game["start_time"] >= now:
            continue  # 跳过未来比赛
        
        home_team = game["home_team"]
        away_team = game["away_team"]
        home_score = game["home_team_score"]
        away_score = game["away_team_score"]

        # 判断胜负
        if home_score > away_score:  # 主队胜
            team_records[home_team]["wins"] += 1
            team_records[away_team]["losses"] += 1
        else:  # 客队胜
            team_records[away_team]["wins"] += 1
            team_records[home_team]["losses"] += 1

    # 转换为 DataFrame 并按胜率排序
    standings = pd.DataFrame([{
        "Team": team.name.replace("_", " "),  # 格式化球队名
        "Wins": record["wins"],
        "Losses": record["losses"],
        "Win %": record["wins"] / (record["wins"] + record["losses"]) if (record["wins"] + record["losses"]) > 0 else 0,
        "Conference": team_conferences.get(team.name.replace("_", " "), "Unknown")  # 添加分区信息
    } for team, record in team_records.items()]).sort_values(by="Win %", ascending=False)

    return standings

"""获取每支球队最近指定场次的战绩（默认为最近10场）"""
def get_recent_games_standings(season_end_year=2025, recent_games=10):
    # 获取 赛季赛程（包含已完成和未来比赛）
    schedule = client.season_schedule(season_end_year=season_end_year)
    
    now = datetime.now(timezone.utc) - timedelta(hours=4)
    
    # 按球队存储最近 10 场比赛结果（使用 deque 只保留最新 10 场）
    team_recent_games = defaultdict(lambda: deque(maxlen=recent_games))

    # 遍历赛程，统计战绩（仅统计已完成的比赛）
    for game in schedule:
        if game["start_time"] >= now:
            continue  # 跳过未来比赛

        home_team = game["home_team"]
        away_team = game["away_team"]
        home_score = game["home_team_score"]
        away_score = game["away_team_score"]

        # 判断胜负
        if home_score > away_score:  # 主队胜
            team_recent_games[home_team].append(1)  # 1 代表胜
            team_recent_games[away_team].append(0)  # 0 代表负
        else:  # 客队胜
            team_recent_games[away_team].append(1)
            team_recent_games[home_team].append(0)

    #for team, record in team_recent_games.items():
    #    print(team, record)
    # 计算每支球队最近 10 场比赛的胜率
    standings = pd.DataFrame([
        {"Team": team.name.replace("_", " "),  # 格式化球队名
         "Record": record,
         "Wins (Last 10)": sum(record),  # 最近 10 场的胜场数
         "Losses (Last 10)": len(record) - sum(record),  # 最近 10 场的负场数
         "Win % (Last 10)": sum(record) / len(record) if len(record) > 0 else 0}  # 胜率
        for team, record in team_recent_games.items()
    ]).sort_values(by="Win % (Last 10)", ascending=False)

    return standings

"""获取每支球队主场战绩"""
def get_home_record_standings(season_end_year=2025):
    # 获取赛季赛程（包含已完成和未来比赛）
    schedule = client.season_schedule(season_end_year=season_end_year)
    
    now = datetime.now(timezone.utc) - timedelta(hours=4)
    
    # 统计每支球队的主场战绩
    home_records = defaultdict(lambda: {"home_wins": 0, "home_losses": 0})

    # 遍历赛程，统计主场胜负情况（仅统计已完成的比赛）
    for game in schedule:
        if game["start_time"] >= now:
            continue  # 跳过未来比赛
        
        home_team = game["home_team"]
        away_team = game["away_team"]
        home_score = game["home_team_score"]
        away_score = game["away_team_score"]

        # 记录主场战绩
        if home_score > away_score:  # 主队赢
            home_records[home_team]["home_wins"] += 1
        else:  # 主队输
            home_records[home_team]["home_losses"] += 1

    # 转换为 DataFrame 并按主场胜率排序
    standings = pd.DataFrame([
        {"Team": team.name.replace("_", " "),  # 格式化球队名
         "Home Wins": record["home_wins"],
         "Home Losses": record["home_losses"],
         "Home Win": record["home_wins"] / (record["home_wins"] + record["home_losses"]) 
                        if (record["home_wins"] + record["home_losses"]) > 0 else 0}
        for team, record in home_records.items()
    ]).sort_values(by="Home Win", ascending=False)

    return standings

"""获取每支球队客场战绩"""
def get_away_record_standings(season_end_year=2025):
    # 获取赛季赛程（包含已完成和未来比赛）
    schedule = client.season_schedule(season_end_year=season_end_year)
    
    now = datetime.now(timezone.utc) - timedelta(hours=4)
    
    # 统计每支球队的客场战绩
    away_records = defaultdict(lambda: {"away_wins": 0, "away_losses": 0})

    # 遍历赛程，统计客场胜负情况（仅统计已完成的比赛）
    for game in schedule:
        if game["start_time"] >= now:
            continue  # 跳过未来比赛
        
        away_team = game["away_team"]
        home_team = game["home_team"]
        away_score = game["away_team_score"]
        home_score = game["home_team_score"]

        # 记录客场战绩
        if away_score > home_score:  # 客队赢
            away_records[away_team]["away_wins"] += 1
        else:  # 客队输
            away_records[away_team]["away_losses"] += 1

    # 转换为 DataFrame 并按客场胜率排序
    standings = pd.DataFrame([
        {"Team": team.name.replace("_", " "),  # 格式化球队名
         "Away Wins": record["away_wins"],
         "Away Losses": record["away_losses"],
         "Away Win": record["away_wins"] / (record["away_wins"] + record["away_losses"]) 
                        if (record["away_wins"] + record["away_losses"]) > 0 else 0}
        for team, record in away_records.items()
    ]).sort_values(by="Away Win", ascending=False)

    return standings

"""获取每支球队净效率"""
def get_team_net_rating(season_end_year=2025):
    # 获取赛季所有比赛
    schedule = client.season_schedule(season_end_year=season_end_year)
    
    now = datetime.now(timezone.utc) - timedelta(hours=4)
    
    # 统计每支球队的进攻/防守数据
    team_stats = defaultdict(lambda: {"points_scored": 0, "points_allowed": 0, "possessions": 0})

    # 遍历赛程，统计每场比赛数据（跳过未来比赛）
    for game in schedule:
        if game["start_time"] >= now:
            continue  # 跳过未来比赛

        home_team = game["home_team"]
        away_team = game["away_team"]
        home_score = game["home_team_score"]
        away_score = game["away_team_score"]

        # 更新球队得分数据
        team_stats[home_team]["points_scored"] += home_score
        team_stats[home_team]["points_allowed"] += away_score
        team_stats[away_team]["points_scored"] += away_score
        team_stats[away_team]["points_allowed"] += home_score

        # 这里我们没有详细的投篮、篮板和失误数据，暂时用一个固定回合数估算
        avg_possessions = (home_score + away_score) / 2  # 近似处理
        team_stats[home_team]["possessions"] += avg_possessions
        team_stats[away_team]["possessions"] += avg_possessions

    # 计算净效率（每 100 回合的得分 - 每 100 回合的失分）
    standings = pd.DataFrame([
        {
            "Team": team.name.replace("_", " "),  # 格式化球队名
            "Offensive Rating": (stats["points_scored"] / stats["possessions"]) * 100 if stats["possessions"] > 0 else 0,
            "Defensive Rating": (stats["points_allowed"] / stats["possessions"]) * 100 if stats["possessions"] > 0 else 0,
            "Net Rating": ((stats["points_scored"] - stats["points_allowed"]) / stats["possessions"]) * 100 if stats["possessions"] > 0 else 0
        }
        for team, stats in team_stats.items()
    ]).sort_values(by="Net Rating", ascending=False)

    return standings

"""获取球队交手战绩"""
def get_head_to_head_matrix(season_end_year=2025):
    # 获取赛季所有比赛
    schedule = client.season_schedule(season_end_year=season_end_year)
    
    now = datetime.now(timezone.utc) - timedelta(hours=4)
    
    # 统计球队交手战绩
    team_matchups = defaultdict(lambda: defaultdict(int))  # team_matchups[team1][team2] = X（胜场数 - 负场数）

    # 遍历赛程，统计战绩（跳过未来比赛）
    for game in schedule:
        if game["start_time"] >= now:
            continue  # 跳过未来比赛

        home_team = game["home_team"]
        away_team = game["away_team"]
        home_score = game["home_team_score"]
        away_score = game["away_team_score"]

        # 记录交手胜负
        if home_score > away_score:  # 主队赢
            team_matchups[home_team][away_team] += 1  # 主队 +1
            team_matchups[away_team][home_team] -= 1  # 客队 -1
        else:  # 客队赢
            team_matchups[away_team][home_team] += 1  # 客队 +1
            team_matchups[home_team][away_team] -= 1  # 主队 -1

    # 获取所有球队列表
    all_teams = sorted(team_matchups.keys(), key=lambda x: x.name)

    # 构建战绩矩阵
    matchup_matrix = pd.DataFrame(0, index=[t.name.replace("_", " ") for t in all_teams], 
                                     columns=[t.name.replace("_", " ") for t in all_teams])

    for team1, team2 in product(all_teams, repeat=2):
        if team1 != team2:
            matchup_matrix.at[team1.name.replace("_", " "), team2.name.replace("_", " ")] = team_matchups[team1][team2]

    return matchup_matrix

"""获取每支球队背靠背战绩"""
def get_back_to_back_records(season_end_year=2025):
    # 获取赛季赛程
    schedule = client.season_schedule(season_end_year=season_end_year)

    now = datetime.now(timezone.utc) - timedelta(hours=4)

    # 初始化 B2B 战绩字典
    b2b_records = defaultdict(lambda: {"wins": 0, "losses": 0, "games": []})
    
    # 按日期排序比赛
    schedule = sorted(schedule, key=lambda x: x["start_time"])

    # 记录每支球队的最近比赛日期（美东时间）
    last_game_date = {}

    for game in schedule:
        if game["start_time"] >= now:
            continue  # 只统计已完成的比赛

        # 转换到美东时间（UTC-4）
        game_time_et = game["start_time"] - timedelta(hours=4)
        game_date_et = game_time_et.date()
        
        home_team = game["home_team"]
        away_team = game["away_team"]
        home_score = game["home_team_score"]
        away_score = game["away_team_score"]
        #print(game_time_et, home_team, away_team, home_score, away_score)
        # 检查是否为背靠背
        for team in [home_team, away_team]:
            if team in last_game_date and (game_date_et - last_game_date[team]).days == 1:
                # 是背靠背比赛
                is_home = (team == home_team)
                won = (home_score > away_score) if is_home else (away_score > home_score)
                
                if won:
                    b2b_records[team]["wins"] += 1
                else:
                    b2b_records[team]["losses"] += 1

                # 记录比赛
                b2b_records[team]["games"].append((game_date_et, "Win" if won else "Loss"))

        # 更新最近比赛日期
        last_game_date[home_team] = game_date_et
        last_game_date[away_team] = game_date_et

    # 转换为 DataFrame
    b2b_standings = pd.DataFrame([
        {"Team": team.name.replace("_", " ").upper(),  # 变为大写球队名
         "B2B Wins": record["wins"],
         "B2B Losses": record["losses"],
         "B2B Win %": record["wins"] / (record["wins"] + record["losses"]) if (record["wins"] + record["losses"]) > 0 else 0}
        for team, record in b2b_records.items()
    ]).sort_values(by="B2B Win %", ascending=False)

    return b2b_standings


