"""
Low Price Stock Finder

This script identifies stocks that are at their 13, 26, or 52-week highs/lows (within a user-defined percentage)
and are priced below a specified threshold, considering all stocks in the database.
"""

from stock_analysis import StockAnalyzer
import pandas as pd
from sqlalchemy import distinct
from db_operations import RawStockData

def find_low_price_stocks(threshold: float, variation: float):
    analyzer = StockAnalyzer()
    
    # Get all available tickers from the RawStockData class
    all_tickers_query = analyzer.session.query(distinct(RawStockData.ticker)).all()
    all_tickers = [ticker[0] for ticker in all_tickers_query]  # Extracting tickers from the query result
    
    highs_lows = analyzer.get_high_low_analysis(all_tickers, periods=[13, 26, 52])
    
    # Filter stocks based on the criteria
    results = []
    for index, row in highs_lows.iterrows():
        current_price = analyzer.get_current_price(row['ticker']).iloc[0]['current_price']
        high_13w = row['high_13w']
        low_13w = row['low_13w']
        high_26w = row['high_26w']
        low_26w = row['low_26w']
        high_52w = row['high_52w']
        low_52w = row['low_52w']
        
        # Calculate the variation threshold
        variation_threshold = variation / 100
        
        # Check if current price is below the threshold and within ±variation% of highs/lows
        if (current_price < threshold and
            (abs(current_price - high_13w) / high_13w <= variation_threshold or
             abs(current_price - low_13w) / low_13w <= variation_threshold or
             abs(current_price - high_26w) / high_26w <= variation_threshold or
             abs(current_price - low_26w) / low_26w <= variation_threshold or
             abs(current_price - high_52w) / high_52w <= variation_threshold or
             abs(current_price - low_52w) / low_52w <= variation_threshold)):
            results.append({
                'ticker': row['ticker'],
                'current_price': current_price,
                'high_13w': high_13w,
                'low_13w': low_13w,
                'high_26w': high_26w,
                'low_26w': low_26w,
                'high_52w': high_52w,
                'low_52w': low_52w
            })
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    user_threshold = float(input("Enter the price threshold: "))
    user_variation = float(input("Enter the variation percentage (e.g., 5 for ±5%): "))
    low_price_stocks = find_low_price_stocks(user_threshold, user_variation)
    print(low_price_stocks) 