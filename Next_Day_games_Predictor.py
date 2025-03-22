import datetime
import pandas as pd
from datetime import datetime, timedelta, timezone
from basketball_reference_web_scraper import client
from Team_Score_Model import calculate_b2b_impact_factor, calculate_team_strength
import standings_tools

def fetch_future_games():
    """ 提取最新一天的未来赛程，并标记背靠背球队 """
    # 转换为美东时间
    now = datetime.now(timezone.utc) - timedelta(hours=4)
    today = now.date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    
    games = client.season_schedule(season_end_year=2025)
    
    # 获取昨天的比赛记录（用于检查背靠背）
    yesterday_games = [
        game for game in games
        if (game["start_time"] - timedelta(hours=4)).date() == yesterday
    ]
    
    # 记录昨天比赛的球队
    teams_played_yesterday = set()
    for game in yesterday_games:
        teams_played_yesterday.add(game["home_team"].value)
        teams_played_yesterday.add(game["away_team"].value)
    
    # 获取今天的比赛，并标记背靠背
    future_games = []
    for game in games:
        game_date = (game["start_time"] - timedelta(hours=4)).date()
        if game_date == today:
            
            home_team = game["home_team"].value
            away_team = game["away_team"].value
            
            # 标记背靠背情况
            game_info = {
                "game_time": game["start_time"],
                "home_team": home_team,
                "away_team": away_team,
                "home_b2b": home_team in teams_played_yesterday,
                "away_b2b": away_team in teams_played_yesterday
            }
            future_games.append(game_info)
    
    # 按时间排序
    if future_games:
        future_games.sort(key=lambda x: x["game_time"])
    
    return future_games

def predict_games(team_strength, h2h_matrix,b2b_standings):
    future_games = fetch_future_games()
    predictions = []
    for game in future_games:
        home_team = game["home_team"].replace("_", " ")
        away_team = game["away_team"].replace("_", " ")

        # 获取球队基本强度评分
        strength_home = team_strength.loc[team_strength["Team"] == home_team, "strength_score"].values
        strength_away = team_strength.loc[team_strength["Team"] == away_team, "strength_score"].values
        
        # 获取主客场战绩评分
        home_boost = team_strength.loc[team_strength["Team"] == home_team, "home_standings_score"].values
        away_boost = team_strength.loc[team_strength["Team"] == away_team, "away_standings_score"].values

        # 获取交手战绩评分（h2h_matrix）
        h2h_boost = h2h_matrix.loc[home_team, away_team] if home_team in h2h_matrix.index and away_team in h2h_matrix.columns else 0

        # 获取背靠背状态
        home_is_b2b = game["home_b2b"]
        away_is_b2b = game["away_b2b"]

        if len(strength_home) == 0 or len(strength_away) == 0:
            continue  # 防止数据缺失导致的错误
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

if __name__ == "__main__":
    """获取球队基础指标"""
    nba_standings = standings_tools.get_nba_standings(season_end_year=2025)
    recent_standings = standings_tools.get_recent_games_standings(season_end_year=2025, recent_games=10)
    home_standings = standings_tools.get_home_record_standings(season_end_year=2025)
    away_standings = standings_tools.get_away_record_standings(season_end_year=2025)
    net_rating_standings = standings_tools.get_team_net_rating(season_end_year=2025)
    h2h_matrix = standings_tools.get_head_to_head_matrix(season_end_year=2025)
    b2b_standings = standings_tools.get_back_to_back_records(season_end_year=2025)

    """获取球队强度评分"""
    team_strength = calculate_team_strength(nba_standings, recent_standings, net_rating_standings, home_standings, away_standings)
    predictions_df = predict_games(team_strength, h2h_matrix,b2b_standings)

    # 打印预测结果
    print("预测结果:")
    print(predictions_df)

