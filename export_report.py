import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

DB_FILE = "summaries.db"

def export_static_report():
    """Export database results to static HTML and CSV files"""
    
    # Load data
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM summaries", conn)
    conn.close()
    
    if df.empty:
        print("No data found. Run main.py first.")
        return
    
    # Export raw data to CSV
    df.to_csv("summaries_export.csv", index=False)
    print("Exported raw data to summaries_export.csv")
    
    # Create summary statistics
    summary_stats = df.groupby(['level', 'strategy']).agg({
        'tokens': ['mean', 'std', 'min', 'max'],
        'time_taken': ['mean', 'std', 'min', 'max']
    }).round(2)
    
    summary_stats.to_csv("summary_statistics.csv")
    print("Exported summary statistics to summary_statistics.csv")
    
    # Create visualizations
    plt.figure(figsize=(15, 10))
    
    # Token usage by strategy
    plt.subplot(2, 2, 1)
    df.groupby('strategy')['tokens'].mean().plot(kind='bar')
    plt.title('Average Tokens by Strategy')
    plt.ylabel('Tokens')
    plt.xticks(rotation=45)
    
    # Time taken by strategy
    plt.subplot(2, 2, 2)
    df.groupby('strategy')['time_taken'].mean().plot(kind='bar')
    plt.title('Average Time by Strategy')
    plt.ylabel('Time (seconds)')
    plt.xticks(rotation=45)
    
    # Token usage by period
    plt.subplot(2, 2, 3)
    df.groupby('period_days')['tokens'].mean().plot(kind='bar')
    plt.title('Average Tokens by Period')
    plt.ylabel('Tokens')
    plt.xlabel('Period (days)')
    
    # Time by period
    plt.subplot(2, 2, 4)
    df.groupby('period_days')['time_taken'].mean().plot(kind='bar')
    plt.title('Average Time by Period')
    plt.ylabel('Time (seconds)')
    plt.xlabel('Period (days)')
    
    plt.tight_layout()
    plt.savefig('analysis_charts.png', dpi=300, bbox_inches='tight')
    print("Exported charts to analysis_charts.png")
    
    # Create HTML report
    html_report = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Summarization Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .summary {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>Summarization Analysis Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Summary Statistics</h2>
        <img src="analysis_charts.png" alt="Analysis Charts" style="max-width: 100%;">
        
        <h2>Key Findings</h2>
        <div class="summary">
            <h3>Token Usage</h3>
            <p>Most efficient strategy: {df.groupby('strategy')['tokens'].mean().idxmin()}</p>
            <p>Average tokens: {df.groupby('strategy')['tokens'].mean().round(0).to_dict()}</p>
        </div>
        
        <div class="summary">
            <h3>Time Performance</h3>
            <p>Fastest strategy: {df.groupby('strategy')['time_taken'].mean().idxmin()}</p>
            <p>Average time (seconds): {df.groupby('strategy')['time_taken'].mean().round(2).to_dict()}</p>
        </div>
        
        <h2>Detailed Results</h2>
        {df.to_html(classes='data', table_id='results')}
        
        <h2>Files</h2>
        <ul>
            <li><a href="summaries_export.csv">Raw Data (CSV)</a></li>
            <li><a href="summary_statistics.csv">Summary Statistics (CSV)</a></li>
            <li><a href="analysis_charts.png">Charts (PNG)</a></li>
        </ul>
    </body>
    </html>
    """
    
    with open('analysis_report.html', 'w') as f:
        f.write(html_report)
    
    print("Exported complete report to analysis_report.html")
    print("\nFiles created:")
    print("- analysis_report.html (main report)")
    print("- summaries_export.csv (raw data)")
    print("- summary_statistics.csv (aggregated stats)")
    print("- analysis_charts.png (visualizations)")

if __name__ == "__main__":
    export_static_report() 