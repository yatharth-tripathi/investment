from db_config import DBConfig
from db_operations import DatabaseManager
from stock_trend_analysis import analyze_stock_trends
from datetime import datetime
import pandas as pd

def test_database_operations():
    # Initialize
    config = DBConfig(password='password')
    db = DatabaseManager(config)
    
    # Create tables
    print("Creating tables...")
    db.create_tables()
    
    # Test with a single ticker
    ticker = "AAPL"
    timeframe_months = 24
    
    print(f"\nAnalyzing {ticker} for {timeframe_months} months...")
    df, trends, company_data = analyze_stock_trends(ticker, timeframe_months)
    
    # Save company info
    print("\nSaving company information...")
    db.save_company_info(ticker, company_data)
    
    # Save raw data
    print("\nSaving raw stock data...")
    db.save_raw_stock_data(ticker, df)
    
    # Prepare and save streak statistics
    print("\nSaving streak statistics...")
    db.save_streak_statistics(
        ticker=ticker,
        analysis_date=datetime.now().date(),
        timeframe_months=timeframe_months,
        stats=trends
    )
    
    # Prepare and save long streaks
    print("\nSaving long streaks...")
    long_streaks_data = []
    for streak_type in ['up', 'down']:
        for streak in trends['long_streaks'][streak_type]:
            end_date = streak['start_date'] + pd.Timedelta(days=streak['length'])
            
            # Calculate next day changes
            next_day = end_date + pd.Timedelta(days=1)
            try:
                # Use .loc to safely access DataFrame rows
                if next_day in df.index:
                    next_day_price = float(df.loc[next_day, 'Close'])
                    end_date_price = float(df.loc[end_date, 'Close'])
                    next_day_change = next_day_price - end_date_price
                    next_day_change_pct = (next_day_price - end_date_price) / end_date_price * 100
                else:
                    next_day_change = 0.0
                    next_day_change_pct = 0.0
            except KeyError:
                next_day_change = 0.0
                next_day_change_pct = 0.0
            
            streak_data = {
                'type': streak_type,
                'start_date': streak['start_date'],
                'end_date': end_date,
                'length': int(streak['length']),
                'change': float(streak['change']),
                'change_pct': float(streak['change_pct']),
                'next_day_change': float(next_day_change),
                'next_day_change_pct': float(next_day_change_pct)
            }
            long_streaks_data.append(streak_data)
    
    db.save_long_streaks(ticker, long_streaks_data)
    
    # Verify data was saved by retrieving it
    print("\nVerifying saved data...")
    saved_data = db.get_raw_stock_data(
        ticker=ticker,
        start_date=(datetime.now() - pd.Timedelta(days=timeframe_months*30)).date(),
        end_date=datetime.now().date()
    )
    print(f"Retrieved {len(saved_data)} rows of raw stock data")
    
    print("\nDatabase operations completed successfully!")

if __name__ == "__main__":
    test_database_operations()