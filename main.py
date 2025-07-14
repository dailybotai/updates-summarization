import os
import pandas as pd
from datetime import datetime, timedelta
import time
import sqlite3
import random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CSV_FILE = "daily-stand-up_responses_19-06-until-10-07.csv"
MODEL = "gpt-4o-mini"
DB_FILE = "summaries.db"

def load_and_prepare_data():
    df = pd.read_csv(CSV_FILE)
    df['Creation Date'] = pd.to_datetime(df['Creation Date'])
    unique_users = df['Respondent'].unique()
    random.shuffle(unique_users)
    split = len(unique_users) // 2
    team_a_users = unique_users[:split]
    team_b_users = unique_users[split:]
    df['Team'] = df['Respondent'].apply(lambda x: 'Team A' if x in team_a_users else 'Team B')
    return df

def get_data_for_period(df, start_date, end_date):
    return df[(df['Creation Date'] >= start_date) & (df['Creation Date'] <= end_date)]

def get_data_for_user(df, user):
    return df[df['Respondent'] == user]

def get_data_for_team(df, team):
    return df[df['Team'] == team]

def summarize_text(text, prompt_prefix="Summarize the following updates:"):
    print("  Calling OpenAI API...")
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": f"{prompt_prefix}\n\n{text}"}]
        )
        end_time = time.time()
        summary = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        time_taken = end_time - start_time
        return summary, tokens_used, time_taken
    except Exception as e:
        print(f"  API Error: {str(e)}")
        return "Error", 0, 0

def generate_summary(df, level, entity, period_days, strategy):
    print(f"Generating {strategy} summary for {level} {entity} over {period_days} days...")
    end_date = df['Creation Date'].max()
    start_date = end_date - timedelta(days=period_days - 1)  # Inclusive
    if level == 'user':
        period_df = get_data_for_user(get_data_for_period(df, start_date, end_date), entity)
        prefix = f"Summarize {entity}'s "
    elif level == 'team':
        period_df = get_data_for_team(get_data_for_period(df, start_date, end_date), entity)
        prefix = f"Summarize {entity}'s "
    else:  # all
        period_df = get_data_for_period(df, start_date, end_date)
        prefix = "Summarize all teams' "
    
    if period_df.empty:
        print("No data for this period.")
        return "No data", 0, 0
    
    if strategy == 'direct':
        text = "\n".join(period_df['Previous work day progress'].fillna('') + " " + period_df['Plans for today'].fillna(''))
        summary, tokens, time_taken = summarize_text(text, prefix + f"{period_days}-day activity:")
        print(f"Done! Tokens: {tokens}, Time: {time_taken:.2f}s")
        return summary, tokens, time_taken
    elif strategy == 'daily_chained' and period_days > 1:
        summaries = []
        tokens = 0
        time_taken = 0
        grouped = period_df.groupby(period_df['Creation Date'].dt.date)
        for i, (date, group) in enumerate(grouped, 1):
            print(f"  Summarizing day {i}/{len(grouped)} ({date})...")
            text = "\n".join(group['Previous work day progress'].fillna('') + " " + group['Plans for today'].fillna(''))
            daily_sum, daily_tokens, daily_time = summarize_text(text, prefix + f"updates for {date}:")
            summaries.append(daily_sum)
            tokens += daily_tokens
            time_taken += daily_time
            print(f"  Done day {i}: Tokens: {daily_tokens}, Time: {daily_time:.2f}s")
        print("  Chaining daily summaries...")
        chain_text = "\n".join(summaries)
        final_sum, final_tokens, final_time = summarize_text(chain_text, prefix + f"{period_days}-day activity:")
        tokens += final_tokens
        time_taken += final_time
        print(f"  Done chaining! Tokens: {final_tokens}, Time: {final_time:.2f}s")
        print(f"Overall: Tokens: {tokens}, Time: {time_taken:.2f}s")
        return final_sum, tokens, time_taken
    elif strategy == 'weekly_chained' and period_days > 7:
        summaries = []
        tokens = 0
        time_taken = 0
        week_starts = pd.date_range(start_date, end_date, freq='W-MON')
        for i, week_start in enumerate(week_starts, 1):
            week_end = week_start + timedelta(days=6)
            if week_end < start_date: continue
            print(f"  Summarizing week {i}/{len(week_starts)} (starting {week_start.date()})...")
            week_df = get_data_for_period(period_df, week_start, min(week_end, end_date))
            if week_df.empty: continue
            text = "\n".join(week_df['Previous work day progress'].fillna('') + " " + week_df['Plans for today'].fillna(''))
            week_sum, week_tokens, week_time = summarize_text(text, prefix + f"updates for week starting {week_start.date()}:")
            summaries.append(week_sum)
            tokens += week_tokens
            time_taken += week_time
            print(f"  Done week {i}: Tokens: {week_tokens}, Time: {week_time:.2f}s")
        print("  Chaining weekly summaries...")
        chain_text = "\n".join(summaries)
        final_sum, final_tokens, final_time = summarize_text(chain_text, prefix + f"{period_days}-day activity:")
        tokens += final_tokens
        time_taken += final_time
        print(f"  Done chaining! Tokens: {final_tokens}, Time: {final_time:.2f}s")
        print(f"Overall: Tokens: {tokens}, Time: {time_taken:.2f}s")
        return final_sum, tokens, time_taken
    else:
        # Fallback to direct if chaining not applicable
        print("Fallback to direct strategy.")
        return generate_summary(df, level, entity, period_days, 'direct')

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS summaries
                 (id INTEGER PRIMARY KEY, level TEXT, entity TEXT, period_days INTEGER, strategy TEXT, 
                  summary_text TEXT, tokens INTEGER, time_taken REAL, generated_at TEXT)''')
    conn.commit()
    return conn

def store_result(conn, level, entity, period_days, strategy, summary, tokens, time_taken):
    generated_at = datetime.now().isoformat()
    c = conn.cursor()
    c.execute('''INSERT INTO summaries (level, entity, period_days, strategy, summary_text, tokens, time_taken, generated_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (level, entity, period_days, strategy, summary, tokens, time_taken, generated_at))
    conn.commit()

def run_analysis(df):
    conn = init_db()
    users = df['Respondent'].unique()[:6]  # More users for variety
    teams = df['Team'].unique()
    periods = [1, 3, 5, 7, 15, 30]
    strategies = ['direct', 'daily_chained', 'weekly_chained']
    
    print("Starting user-level analysis...")
    for u_i, user in enumerate(users, 1):
        print(f"Processing user {user} ({u_i}/{len(users)})")
        for p_i, period in enumerate(periods, 1):
            print(f"  Period {period} days ({p_i}/{len(periods)})")
            for strategy in strategies:
                if (strategy == 'weekly_chained' and period <= 7) or (strategy == 'daily_chained' and period == 1):
                    continue  # Skip inapplicable
                summary, tokens, time_taken = generate_summary(df, 'user', user, period, strategy)
                store_result(conn, 'user', user, period, strategy, summary, tokens, time_taken)
    
    print("Starting team-level analysis...")
    for t_i, team in enumerate(teams, 1):
        print(f"Processing team {team} ({t_i}/{len(teams)})")
        for p_i, period in enumerate(periods, 1):
            print(f"  Period {period} days ({p_i}/{len(periods)})")
            for strategy in strategies:
                if (strategy == 'weekly_chained' and period <= 7) or (strategy == 'daily_chained' and period == 1):
                    continue
                summary, tokens, time_taken = generate_summary(df, 'team', team, period, strategy)
                store_result(conn, 'team', team, period, strategy, summary, tokens, time_taken)
    
    print("Starting all-teams analysis...")
    for p_i, period in enumerate(periods, 1):
        print(f"Processing period {period} days ({p_i}/{len(periods)})")
        for strategy in strategies:
            if (strategy == 'weekly_chained' and period <= 7) or (strategy == 'daily_chained' and period == 1):
                continue
            summary, tokens, time_taken = generate_summary(df, 'all', 'All Teams', period, strategy)
            store_result(conn, 'all', 'All Teams', period, strategy, summary, tokens, time_taken)
    
    conn.close()
    print("Analysis complete. Results stored in summaries.db")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in .env")
    else:
        df = load_and_prepare_data()
        run_analysis(df) 