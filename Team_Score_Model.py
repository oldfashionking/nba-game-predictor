def calculate_team_strength(nba_standings, recent_standings, net_rating_standings, home_standings, away_standings):
    """ 计算球队强度评分，加入主客场战绩影响 """
    
    # 计算排名
    nba_standings["nba_standings_rank"] = nba_standings["Win %"].rank(ascending=False, method="min")
    recent_standings["recent_standings_rank"] = recent_standings["Win % (Last 10)"].rank(ascending=False, method="min")
    net_rating_standings["net_rating_standings_rank"] = net_rating_standings["Net Rating"].rank(ascending=False, method="min")
    home_standings["home_standings_rank"] = home_standings["Home Win"].rank(ascending=False, method="min")
    away_standings["away_standings_rank"] = away_standings["Away Win"].rank(ascending=False, method="min")

    # 合并数据表
    df = (
        nba_standings
        .merge(recent_standings, on="Team")
        .merge(net_rating_standings, on="Team")
        .merge(home_standings, on="Team")
        .merge(away_standings, on="Team")
    )

    # 分档评分
    df["nba_standings_score"] = df["nba_standings_rank"].apply(assign_tiered_score)
    df["recent_standings_score"] = df["recent_standings_rank"].apply(assign_tiered_score)
    df["net_rating_standings_score"] = df["net_rating_standings_rank"].apply(assign_tiered_score)
    df["home_standings_score"] = df["home_standings_rank"].apply(assign_tiered_score)
    df["away_standings_score"] = df["away_standings_rank"].apply(assign_tiered_score)

    # 计算最终强度评分
    df["strength_score"] = (
        0.4 * df["nba_standings_score"] +
        0.3 * df["recent_standings_score"] +
        0.3 * df["net_rating_standings_score"]
    )

    return df

def calculate_win_probability(strength_a, strength_b, factor=20):
    """ 使用 Elo 公式计算胜率 """
    prob_a = 1 / (1 + 10 ** ((strength_b - strength_a) / factor))
    prob_b = 1 - prob_a
    return prob_a, prob_b
def assign_tiered_score(rank):
    """ 根据排名分配分档评分 """
    if 1 <= rank <= 3:
        return 10
    elif 4 <= rank <= 6:
        return 9
    elif 7 <= rank <= 9:
        return 8
    elif 10 <= rank <= 12:
        return 7
    elif 13 <= rank <= 15:
        return 6
    elif 16 <= rank <= 18:
        return 5
    elif 19 <= rank <= 21:
        return 4
    elif 22 <= rank <= 24:
        return 3
    elif 25 <= rank <= 27:
        return 2
    else:
        return 1

def calculate_b2b_impact_factor(b2b_win_percentage):
    """
    根据背靠背胜率计算影响系数
    胜率越高,影响系数越接近1(影响越小)
    胜率越低,影响系数越小(影响越大)
    """
    # 设置最小和最大影响系数
    MIN_FACTOR = 0.7  # 背靠背表现最差时的影响
    MAX_FACTOR = 0.95  # 背靠背表现最好时的影响
    
    # 线性映射胜率到影响系数
    factor = MIN_FACTOR + (MAX_FACTOR - MIN_FACTOR) * b2b_win_percentage
    return factor