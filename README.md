# Summarization Analysis POC

This is a proof-of-concept Python project to analyze user update data from a CSV file and generate summaries using OpenAI's LLM from user and team perspectives. It compares different summarization strategies in terms of token consumption and summary output for quality assessment.

## Setup

1. Install dependencies using Poetry (assumes Poetry is installed globally):
   ```
   poetry install
   ```
   This will create a virtual environment and install packages.

2. Copy `.env.example` to `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_key_here
   ```

3. Ensure the CSV file `daily-stand-up_responses_19-06-until-10-07.csv` is in the project root.

## Running the Script

Run `poetry run python main.py`. It will load the data, run various summarization strategies, and store results in summaries.db.

Strategies include daily/weekly/monthly summaries per user or per team, with chaining for larger periods.

Note: This assumes all respondents are in one team ("DailyBot Team") since no team field is in the CSV. Summaries are generated for example users and the team over periods like 3, 5, 7, 15, 30 days.

## Output

The script outputs a report to console and saves it to `report.txt`.

## Updates
- Added random team assignments (Team A and Team B).
- Levels: user, team, all_teams.
- Strategies: direct, daily_chained, weekly_chained.
- Periods: 1,3,5,7,15,30 days.
- Results stored in SQLite (summaries.db).
- Model: gpt-4o-mini.
- Tracks time taken.

## Running the UI
After running `poetry run python main.py` to populate the database, run:
```
poetry run streamlit run app.py
```
This launches a dashboard to filter and compare summaries, tokens, and time taken. 