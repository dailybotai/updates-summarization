import streamlit as st
import sqlite3
import pandas as pd
import altair as alt

DB_FILE = "summaries.db"

def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM summaries", conn)
    conn.close()
    return df

st.title("Summarization Analysis Dashboard")

df = load_data()
if df.empty:
    st.warning("No data in database. Run main.py first.")
else:
    # Filters
    levels = st.multiselect("Select Levels", options=df['level'].unique(), default=df['level'].unique())
    entities = st.multiselect("Select Entities", options=df['entity'].unique(), default=df['entity'].unique())
    periods = st.multiselect("Select Periods (days)", options=df['period_days'].unique(), default=df['period_days'].unique())
    strategies = st.multiselect("Select Strategies", options=df['strategy'].unique(), default=df['strategy'].unique())
    
    filtered_df = df[
        (df['level'].isin(levels)) &
        (df['entity'].isin(entities)) &
        (df['period_days'].isin(periods)) &
        (df['strategy'].isin(strategies))
    ]
    
    st.subheader("Summary Data")
    st.dataframe(filtered_df[['level', 'entity', 'period_days', 'strategy', 'summary_text', 'tokens', 'time_taken', 'generated_at']])
    
    st.subheader("Token Usage Comparison")
    token_chart = alt.Chart(filtered_df).mark_bar().encode(
        x='strategy',
        y='mean(tokens)',
        color='level',
        column='period_days:O'
    ).properties(width=150)
    st.altair_chart(token_chart)
    
    st.subheader("Time Taken Comparison")
    time_chart = alt.Chart(filtered_df).mark_bar().encode(
        x='strategy',
        y='mean(time_taken)',
        color='level',
        column='period_days:O'
    ).properties(width=150)
    st.altair_chart(time_chart)
    
    st.subheader("Detailed Stats")
    st.write(filtered_df.groupby(['level', 'strategy', 'period_days']).agg({
        'tokens': ['mean', 'sum', 'count'],
        'time_taken': ['mean', 'sum']
    })) 