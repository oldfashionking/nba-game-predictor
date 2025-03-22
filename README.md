# nba-game-predictor
An advanced prediction tool designed to forecast NBA game outcomes based on team performance metrics and dynamic data updates.

## Features

- Predicts NBA game outcomes using:
  - **Team Standings**
  - **Recent 10-game Performance**
  - **Net Efficiency Ratings**
  - **Home and Away Records**
  - **Head-to-Head Results**
  - **Back-to-Back Game Impact**
- Simulates remaining regular season games 1000 times to estimate final standings
- Dynamically updates team metrics after each simulated game for improved accuracy

# Simulation Result （24-25 NBA season Final Ranks） Real Data updated as of March 18, 2025.
![NBA_Final_Standings_west_00](https://github.com/user-attachments/assets/adcf962a-1307-4f3f-a88f-8b75f80e5eab)
![NBA_Final_Standings_east_00](https://github.com/user-attachments/assets/60ddc399-22be-4de7-89fe-ed3c887e10f1)

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/nba-game-predictor.git
cd nba-game-predictor

# Install dependencies
pip install -r requirements.txt
```
## Usage

1. **Predict Next Day Games**

```bash
python Next_Day_games_Predictor.py
```

2. **Simulation the whole season for Final Rankings**
   - Simulate the remaining NBA season 10000 times.

```bash
python Season_Ranking_Simulation.py
```

## Data Sources
https://www.basketball-reference.com/

## Limitations
- The metrics used to evaluate teams are still relatively limited.
- The model for assessing team strength is simple and lacks theoretical support; the weight parameters are manually defined and may be less rigorous.
- The prediction of next day's games does not account for player absences.
