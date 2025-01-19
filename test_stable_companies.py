from db_config import DBConfig
from db_operations import DatabaseManager
from stock_trend_analysis import analyze_stock_trends
import yfinance as yf
from datetime import datetime
import pandas as pd
import numpy as np

def get_sp500_tickers():
    """Get list of S&P 500 tickers using Wikipedia"""
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    df = table[0]
    return df['Symbol'].tolist()

def analyze_company_stability(ticker, timeframe_months=36):
    """
    Analyze company stability based on various metrics
    
    Returns:
    --------
    dict: Stability metrics including:
        - volatility: Standard deviation of returns
        - market_cap: Market capitalization
        - avg_volume: Average trading volume
        - beta: Beta coefficient (market sensitivity)
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data
        end_date = datetime.now()
        start_date = end_date - pd.Timedelta(days=timeframe_months*30)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            return None
            
        # Calculate daily returns
        df['Returns'] = df['Close'].pct_change()
        
        stability_metrics = {
            'volatility': df['Returns'].std() * np.sqrt(252),  # Annualized volatility
            'market_cap': info.get('marketCap', 0),
            'avg_volume': df['Volume'].mean(),
            'beta': info.get('beta', None)
        }
        
        return stability_metrics
        
    except Exception as e:
        print(f"Error analyzing {ticker}: {str(e)}")
        return None

def is_stable_or_important(metrics, 
                         min_market_cap=1e10,  # $10B minimum market cap
                         max_volatility=0.3,    # 30% maximum annual volatility
                         min_avg_volume=1e6):   # 1M minimum average daily volume
    """Determine if a company is stable or important based on metrics"""
    if metrics is None:
        return False
        
    # Check if company meets any of the criteria
    is_large = metrics['market_cap'] >= min_market_cap
    is_stable = metrics['volatility'] <= max_volatility
    is_liquid = metrics['avg_volume'] >= min_avg_volume
    
    return is_large or (is_stable and is_liquid)

def test_populate_stable_companies():
    """Test script to populate database with stable/important company data"""
    # Initialize database
    config = DBConfig(password='password')
    db = DatabaseManager(config)
    
    # Create tables
    print("Creating tables...")
    db.create_tables()
    
    # Get S&P 500 tickers
    print("\nFetching S&P 500 tickers...")
    tickers = get_sp500_tickers()
    
    # Analysis parameters
    timeframe_months = 36  # 3 years of data
    
    # Track progress and results
    stable_companies = []
    total_companies = len(tickers)
    
    print(f"\nAnalyzing {total_companies} companies...")
    for i, ticker in enumerate(tickers, 1):
        print(f"Processing {ticker} ({i}/{total_companies})...")
        
        # Analyze stability
        metrics = analyze_company_stability(ticker, timeframe_months)
        
        if metrics and is_stable_or_important(metrics):
            try:
                # Get detailed data and save to database
                df, trends, company_data = analyze_stock_trends(ticker, timeframe_months)
                
                # Save company info
                db.save_company_info(ticker, company_data)
                
                # Save raw stock data
                db.save_raw_stock_data(ticker, df)
                
                # Save streak statistics
                db.save_streak_statistics(
                    ticker=ticker,
                    analysis_date=datetime.now().date(),
                    timeframe_months=timeframe_months,
                    stats=trends
                )
                
                # Prepare and save long streaks
                long_streaks_data = []
                for streak_type in ['up', 'down']:
                    for streak in trends['long_streaks'][streak_type]:
                        end_date = streak['start_date'] + pd.Timedelta(days=streak['length'])
                        
                        # Calculate next day changes
                        next_day = end_date + pd.Timedelta(days=1)
                        try:
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
                
                # Store results
                stable_companies.append({
                    'ticker': ticker,
                    'market_cap': metrics['market_cap'],
                    'volatility': metrics['volatility'],
                    'avg_volume': metrics['avg_volume'],
                    'beta': metrics['beta']
                })
                
                print(f"✓ {ticker} data saved successfully")
                
            except Exception as e:
                print(f"✗ Error processing {ticker}: {str(e)}")
    
    # Print summary
    print("\n=== Analysis Summary ===")
    print(f"Total companies analyzed: {total_companies}")
    print(f"Stable/Important companies found: {len(stable_companies)}")
    
    # Sort and print stable companies by market cap
    if stable_companies:
        print("\nStable/Important Companies (sorted by market cap):")
        sorted_companies = sorted(stable_companies, key=lambda x: x['market_cap'], reverse=True)
        for company in sorted_companies:
            print(f"\n{company['ticker']}:")
            print(f"  Market Cap: ${company['market_cap']:,.0f}")
            print(f"  Annual Volatility: {company['volatility']*100:.1f}%")
            print(f"  Avg Daily Volume: {company['avg_volume']:,.0f}")
            print(f"  Beta: {company['beta']:.2f}" if company['beta'] else "  Beta: N/A")

if __name__ == "__main__":
    test_populate_stable_companies() 