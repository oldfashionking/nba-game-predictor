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

1. **Data Collection**
   - Run the script to fetch updated NBA data.

```bash
python data_collector.py
```

2. **Simulation**
   - Simulate the remaining NBA season 1000 times.

```bash
python season_simulator.py
```

3. **Generate Reports**
   - Run the report generator to analyze and present insights.

```bash
python report_generator.py
```

## Data Sources


