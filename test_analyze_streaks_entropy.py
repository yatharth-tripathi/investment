from db_config import DBConfig
from db_operations import DatabaseManager
from sqlalchemy import text
import pandas as pd
import numpy as np
from collections import defaultdict
from scipy.stats import entropy

def get_streak_statistics():
    """Query the database for down streak statistics for all companies"""
    config = DBConfig(password='password')
    db = DatabaseManager(config)
    
    # SQL query to get all down streaks
    query = text("""
        SELECT c.ticker, c.name, ls.length
        FROM long_streaks ls
        JOIN companies c ON ls.ticker = c.ticker
        WHERE ls.streak_type = 'down'
        ORDER BY c.ticker, ls.length
    """)
    
    # Execute query
    session = db.Session()
    try:
        result = session.execute(query)
        rows = result.fetchall()
    finally:
        session.close()
    
    return rows

def calculate_streak_distribution(streaks):
    """Calculate the frequency distribution of streak lengths"""
    # Count frequencies of each length
    freq_dict = defaultdict(int)
    for length in streaks:
        freq_dict[length] += 1
    
    # Convert to probability distribution
    total = sum(freq_dict.values())
    prob_dict = {k: v/total for k, v in freq_dict.items()}
    
    return prob_dict, freq_dict

def calculate_entropy(prob_distribution):
    """Calculate Shannon entropy of the distribution"""
    probabilities = list(prob_distribution.values())
    return entropy(probabilities, base=2)  # Use base 2 for bits

def analyze_streak_entropy():
    """Analyze entropy of down streak distributions for all companies"""
    # Get streak data
    print("Fetching streak data from database...")
    rows = get_streak_statistics()
    
    # Organize data by company
    company_data = defaultdict(lambda: {'name': '', 'streaks': []})
    for ticker, name, length in rows:
        company_data[ticker]['name'] = name
        company_data[ticker]['streaks'].append(length)
    
    # Calculate statistics for each company
    print("\nCalculating statistics...")
    results = []
    
    for ticker, data in company_data.items():
        streaks = data['streaks']
        prob_dist, freq_dist = calculate_streak_distribution(streaks)
        
        result = {
            'ticker': ticker,
            'company_name': data['name'],
            'max_down_streak': max(streaks),
            'avg_down_streak': np.mean(streaks),
            'total_down_streaks': len(streaks),
            'entropy': calculate_entropy(prob_dist),
            'frequency_distribution': dict(freq_dist)
        }
        results.append(result)
    
    # Sort by entropy (ascending - least entropic first)
    results.sort(key=lambda x: x['entropy'])
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Separate frequency distribution into its own DataFrame
    freq_df = pd.DataFrame([r['frequency_distribution'] for r in results])
    freq_df.index = df['ticker']
    
    # Drop frequency_distribution column from main DataFrame
    df = df.drop('frequency_distribution', axis=1)
    
    # Save to CSV files
    print("\nSaving results to CSV files...")
    df.to_csv('data/streak_entropy_analysis.csv', index=False)
    freq_df.to_csv('data/streak_length_frequencies.csv')
    
    # Print summary
    print("\n=== Analysis Summary ===")
    print(f"Total companies analyzed: {len(results)}")
    print("\nTop 10 Most Predictable Companies (Lowest Entropy):")
    for i, row in df.head(10).iterrows():
        print(f"\n{row['ticker']} - {row['company_name']}")
        print(f"  Entropy: {row['entropy']:.3f} bits")
        print(f"  Max Down Streak: {row['max_down_streak']} days")
        print(f"  Avg Down Streak: {row['avg_down_streak']:.2f} days")
        print(f"  Total Down Streaks: {row['total_down_streaks']}")
    
    print("\nFiles saved:")
    print("- streak_entropy_analysis.csv: Main analysis results")
    print("- streak_length_frequencies.csv: Detailed frequency distributions")
    
    return df, freq_df

if __name__ == "__main__":
    analyze_streak_entropy() 