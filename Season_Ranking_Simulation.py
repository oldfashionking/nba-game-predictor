import pandas as pd
import numpy as np

import standings_tools
from Team_Score_Model import calculate_b2b_impact_factor, calculate_team_strength
from datetime import datetime, timedelta, timezone
from basketball_reference_web_scraper import client
from collections import defaultdict


def predict_single_games(team_strength, h2h_matrix,b2b_standings,home_team,away_team,home_is_b2b,away_is_b2b):
    """ 预测单场比赛胜率 """
    predictions = []

    # 获取球队基本强度评分
    strength_home = team_strength.loc[team_strength["Team"] == home_team, "strength_score"].values
    strength_away = team_strength.loc[team_strength["Team"] == away_team, "strength_score"].values
    
    # 获取主客场战绩评分
    home_boost = team_strength.loc[team_strength["Team"] == home_team, "home_standings_score"].values
    away_boost = team_strength.loc[team_strength["Team"] == away_team, "away_standings_score"].values

    # 获取交手战绩评分（h2h_matrix）
    h2h_boost = h2h_matrix.loc[home_team, away_team] if home_team in h2h_matrix.index and away_team in h2h_matrix.columns else 0

    # 只在背靠背时应用影响系数
    home_b2b_factor = 1.0
    away_b2b_factor = 1.0
    if home_is_b2b:
        home_b2b_win_pct = b2b_standings.loc[b2b_standings["Team"] == home_team, "B2B Win %"].values[0]
        home_b2b_factor = calculate_b2b_impact_factor(home_b2b_win_pct)
        
    if away_is_b2b:
        away_b2b_win_pct = b2b_standings.loc[b2b_standings["Team"] == away_team, "B2B Win %"].values[0]
        away_b2b_factor = calculate_b2b_impact_factor(away_b2b_win_pct)

    
        # 计算总评分（加入背靠背影响）
    total_home_score = (strength_home[0] + home_boost[0] * 1.2 + h2h_boost * 0.8) * home_b2b_factor
    total_away_score = (strength_away[0] + away_boost[0] + (-h2h_boost) * 0.8) * away_b2b_factor

    # 计算胜率
    home_win_prob = total_home_score / (total_home_score + total_away_score)
    away_win_prob = 1 - home_win_prob

    predictions.append({
        "Home Team": home_team,
        "Away Team": away_team,
        "Home Win Probability": round(home_win_prob * 100, 2),
        "Away Win Probability": round(away_win_prob * 100, 2)
    })

    return pd.DataFrame(predictions)
def fetch_future_all_games():
    """ 提取所有的未来赛程，并标记每一天比赛的背靠背球队 """

        # 获取当前时间（美东时间）
    now = datetime.now(timezone.utc) - timedelta(hours=4)
    today = now.date()
    
    # 获取赛季赛程
    games = client.season_schedule(season_end_year=2025)
    
    # 按日期组织未来比赛
    future_games = []
    
    # 记录每支球队最近的比赛日期
    last_game_dates = {}
    
    # 首先获取已完成比赛的最后日期记录（用于判断第一天的背靠背）
    for game in games:
        game_date = (game["start_time"] - timedelta(hours=4)).date()
        if game_date >= today:
            continue
            
        home_team = game["home_team"].value
        away_team = game["away_team"].value
        
        last_game_dates[home_team] = game_date
        last_game_dates[away_team] = game_date
    
    # 处理未来比赛
    future_schedule = [
        game for game in games
        if (game["start_time"] - timedelta(hours=4)).date() >= today
    ]
    
    # 按日期排序
    future_schedule.sort(key=lambda x: x["start_time"])
    
    # 处理每场比赛
    for game in future_schedule:
        game_time = game["start_time"]
        game_date = (game_time - timedelta(hours=4)).date()
        home_team = game["home_team"].value
        away_team = game["away_team"].value
        
        # 检查背靠背情况
        home_b2b = False
        away_b2b = False
        
        if home_team in last_game_dates:
            last_date = last_game_dates[home_team]
            if (game_date - last_date).days == 1:
                home_b2b = True
                
        if away_team in last_game_dates:
            last_date = last_game_dates[away_team]
            if (game_date - last_date).days == 1:
                away_b2b = True
        
        # 记录比赛信息
        game_info = {
            "game_time": game_time,
            "game_date": game_date,
            "home_team": home_team,
            "away_team": away_team,
            "home_b2b": home_b2b,
            "away_b2b": away_b2b
        }
        future_games.append(game_info)
        
        # 更新最近比赛日期
        last_game_dates[home_team] = game_date
        last_game_dates[away_team] = game_date

    if future_games:
        future_games.sort(key=lambda x: x["game_time"])
    return future_games


def simulate_season(nba_standings, recent_standings, net_rating_standings, home_standings, away_standings, h2h_matrix, b2b_standings,num_simulations=10000):
    """ 模拟整个赛季 """
    team_records = defaultdict(lambda: [])  # 记录每支球队的战绩
    
    # 获取未来赛程
    future_schedule=fetch_future_all_games()

    for _ in range(num_simulations):
        # 复制数据，避免影响原始数据
        standings = nba_standings.copy()
        recent = recent_standings.copy()
        home = home_standings.copy()
        away = away_standings.copy()
        h2h = h2h_matrix.copy()
        b2b = b2b_standings.copy()
        
        recent_game_result = dict(zip(recent['Team'], recent['Record']))
        # 按天模拟剩余赛程
        for game in future_schedule:
            home_team = game["home_team"].replace("_", " ")
            away_team = game["away_team"].replace("_", " ")
                    # 获取背靠背状态
            home_is_b2b = game["home_b2b"]
            away_is_b2b = game["away_b2b"]
            # 计算当前球队强度评分
            team_strength = calculate_team_strength(standings, recent, net_rating_standings, home, away)
            predictions = predict_single_games(team_strength, h2h, b2b,home_team, away_team,home_is_b2b,away_is_b2b)
            
            home_win_prob = predictions.loc[(predictions["Home Team"] == home_team) & (predictions["Away Team"] == away_team), "Home Win Probability"].values
            if len(home_win_prob) == 0:
                continue  # 数据异常情况跳过
            
            home_win_prob = home_win_prob[0] / 100
            
            # 采样比赛胜负
            home_wins = np.random.rand() < home_win_prob

            if home_wins:
                # 更新球队胜负记录
                standings.loc[standings['Team'] == home_team, 'Wins'] += 1
                standings.loc[standings['Team'] == away_team, 'Losses'] += 1
                # 更新最近比赛记录
                recent_game_result[home_team].append(1)
                recent_game_result[away_team].append(0)
                # 更新主客场战绩
                home.loc[home["Team"] == home_team, "Home Wins"] += 1
                away.loc[away["Team"] == away_team, "Away Losses"] += 1
                # 更新交手战绩
                h2h.loc[home_team, away_team] += 1
                h2h.loc[away_team, home_team] -= 1

                if home_is_b2b:
                    b2b.loc[b2b['Team'] == home_team, 'B2B Wins'] += 1
                if away_is_b2b:
                    b2b.loc[b2b['Team'] == away_team, 'B2B Losses'] += 1
            else:
                # 更新球队胜负记录
                standings.loc[standings['Team'] == away_team, 'Wins'] += 1
                standings.loc[standings['Team'] == home_team, 'Losses'] += 1
                 # 更新最近比赛记录
                recent_game_result[home_team].append(0)
                recent_game_result[away_team].append(1)
                # 更新主客场战绩
                home.loc[home["Team"] == home_team, "Home Losses"] += 1
                away.loc[away["Team"] == away_team, "Away Wins"] += 1
                # 更新交手战绩
                h2h.loc[away_team, home_team] += 1
                h2h.loc[home_team, away_team] -= 1

                if home_is_b2b:
                    b2b.loc[b2b['Team'] == home_team, 'B2B Losses'] += 1
                if away_is_b2b:
                    b2b.loc[b2b['Team'] == away_team, 'B2B Wins'] += 1
            
            # 更新standings中的胜率
            standings.loc[standings['Team'] == home_team, 'Win %'] = standings.loc[standings['Team'] == home_team, 'Wins'] / (standings.loc[standings['Team'] == home_team, 'Wins'] + standings.loc[standings['Team'] == home_team, 'Losses'])
            standings.loc[standings['Team'] == away_team, 'Win %'] = standings.loc[standings['Team'] == away_team, 'Wins'] / (standings.loc[standings['Team'] == away_team, 'Wins'] + standings.loc[standings['Team'] == away_team, 'Losses'])

            # 更新recent standings中的胜率
            for team in [home_team, away_team]:
                recent_win_pct = sum(recent_game_result[team]) / 10
                recent.loc[recent["Team"] == team, "Win % (Last 10)"] = recent_win_pct
            
            # 更新home和away中的胜率
            home.loc[home["Team"] == home_team, "Win %"] = home.loc[home["Team"] == home_team, "Home Wins"] / (home.loc[home["Team"] == home_team, "Home Wins"] + home.loc[home["Team"] == home_team, "Home Losses"])
            away.loc[away["Team"] == away_team, "Win %"] = away.loc[away["Team"] == away_team, "Away Wins"] / (away.loc[away["Team"] == away_team, "Away Wins"] + away.loc[away["Team"] == away_team, "Away Losses"])
            
            # 更新b2b中的胜率
            if home_is_b2b:
                b2b.loc[b2b['Team'] == home_team, 'B2B Win %'] = b2b.loc[b2b['Team'] == home_team, 'B2B Wins'] / (b2b.loc[b2b['Team'] == home_team, 'B2B Wins'] + b2b.loc[b2b['Team'] == home_team, 'B2B Losses'])
            if away_is_b2b:
                b2b.loc[b2b['Team'] == away_team, 'B2B Win %'] = b2b.loc[b2b['Team'] == away_team, 'B2B Wins'] / (b2b.loc[b2b['Team'] == away_team, 'B2B Wins'] + b2b.loc[b2b['Team'] == away_team, 'B2B Losses'])
        # 记录模拟的最终战绩
        for team in standings["Team"]:
            team_records[team].append(standings.loc[standings['Team'] == team, 'Wins'].values[0])
    
    # 计算平均战绩
    final_records = {team: np.mean(wins) for team, wins in team_records.items()}
    
    # 将模拟的战绩加到现有战绩中
    #final_records = {team: current_team_wins[team] + avg_records[team] for team in nba_standings["Team"]}
    
    # 按照东部和西部分开排名
    east_teams = nba_standings[nba_standings["Conference"] == "East"]
    west_teams = nba_standings[nba_standings["Conference"] == "West"]
    
    east_teams["Final Wins"] = east_teams["Team"].map(final_records)
    west_teams["Final Wins"] = west_teams["Team"].map(final_records)
    
    east_ranked = east_teams.sort_values(by="Final Wins", ascending=False)
    west_ranked = west_teams.sort_values(by="Final Wins", ascending=False)
    
    return east_ranked, west_ranked

# 调用模拟
if __name__ == "__main__":
    """获取球队基础指标"""
    nba_standings = standings_tools.get_nba_standings(season_end_year=2025)
    recent_standings = standings_tools.get_recent_games_standings(season_end_year=2025, recent_games=10)
    home_standings = standings_tools.get_home_record_standings(season_end_year=2025)
    away_standings = standings_tools.get_away_record_standings(season_end_year=2025)
    net_rating_standings = standings_tools.get_team_net_rating(season_end_year=2025)
    h2h_matrix = standings_tools.get_head_to_head_matrix(season_end_year=2025)
    b2b_standings = standings_tools.get_back_to_back_records(season_end_year=2025)
    
    east_ranked, west_ranked = simulate_season(nba_standings, recent_standings, net_rating_standings, home_standings, away_standings,h2h_matrix,b2b_standings)

    # 假设 east_ranked 和 west_ranked 是已经计算好的东、西部排名 DataFrame
    east_ranked["Final Losses"] = 82 - east_ranked["Final Wins"]
    east_ranked["Final Win %"] = east_ranked["Final Wins"] / 82

    west_ranked["Final Losses"] = 82 - west_ranked["Final Wins"]
    west_ranked["Final Win %"] = west_ranked["Final Wins"] / 82

    # 格式化输出
    print("Eastern Conference Rankings:")
    print(east_ranked[["Team", "Final Wins", "Final Losses", "Win %"]])

    print("\nWestern Conference Rankings:")
    print(west_ranked[["Team", "Final Wins", "Final Losses", "Win %"]])

    # 导出到 Excel
    """
    with pd.ExcelWriter("NBA_Final_Standings.xlsx") as writer:
        east_ranked.to_excel(writer, sheet_name="Eastern Conference", index=False)
        west_ranked.to_excel(writer, sheet_name="Western Conference", index=False)

    print("\nExcel 文件已导出：NBA_Final_Standings.xlsx")
    """
