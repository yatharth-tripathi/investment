import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
from db_config import DBConfig
from db_operations import DatabaseManager

#TODO new script, same as this but from db instead of yf
def get_consecutive_trends(df):
    """
    Analyze consecutive up/down trends in price data.
    """
    # Calculate daily price changes and convert to numpy arrays immediately
    df['Price_Change'] = df['Close'].diff()
    df['Price_Change_Pct'] = df['Close'].pct_change() * 100
    
    # Convert to numpy arrays for easier handling
    price_changes = df['Price_Change'].values
    price_changes_pct = df['Price_Change_Pct'].values
    close_prices = df['Close'].values
    
    # Initialize variables for tracking streaks
    current_up_streak = 0
    current_down_streak = 0
    max_up_streak = 0
    max_down_streak = 0
    
    # Track streak dates and changes
    up_streaks = defaultdict(int)
    down_streaks = defaultdict(int)
    long_streak_info = {
        'up': [],    # Will store tuples of (length, start_date, total_change, pct_change)
        'down': []
    }
    
    # Lists to store cumulative changes during streaks
    up_streak_changes = []
    down_streak_changes = []
    up_streak_changes_pct = []
    down_streak_changes_pct = []
    
    current_up_change = 0
    current_down_change = 0
    current_up_change_pct = 0
    current_down_change_pct = 0
    streak_start_price = close_prices[0]
    streak_start_date = df.index[0]
    
    for i in range(1, len(df)):
        current_price = close_prices[i]
        current_change = price_changes[i]
        
        if current_change > 0:
            if current_down_streak > 0:
                # End of down streak
                down_streaks[current_down_streak] += 1
                down_streak_changes.append(float(current_down_change.item()))  # Extract single value
                down_streak_changes_pct.append(float(current_down_change_pct.item()))  # Extract single value
                
                if current_down_streak > 4:
                    long_streak_info['down'].append({
                        'length': current_down_streak,
                        'start_date': streak_start_date,
                        'change': float(current_down_change.item()),
                        'change_pct': float(current_down_change_pct.item())
                    })
                
                current_down_streak = 0
                current_down_change = 0
                current_down_change_pct = 0
                streak_start_date = df.index[i]
                streak_start_price = current_price
            
            # Continue or start up streak
            if current_up_streak == 0:
                streak_start_date = df.index[i-1]
                streak_start_price = close_prices[i-1]
            current_up_streak += 1
            current_up_change += current_change
            current_up_change_pct = (current_price - streak_start_price) / streak_start_price * 100
            max_up_streak = max(max_up_streak, current_up_streak)
            
        elif current_change < 0:
            if current_up_streak > 0:
                # End of up streak
                up_streaks[current_up_streak] += 1
                up_streak_changes.append(float(current_up_change.item()))  # Extract single value
                up_streak_changes_pct.append(float(current_up_change_pct.item()))  # Extract single value
                
                if current_up_streak > 4:
                    long_streak_info['up'].append({
                        'length': current_up_streak,
                        'start_date': streak_start_date,
                        'change': float(current_up_change.item()),
                        'change_pct': float(current_up_change_pct.item())
                    })
                
                current_up_streak = 0
                current_up_change = 0
                current_up_change_pct = 0
                streak_start_date = df.index[i]
                streak_start_price = current_price
            
            # Continue or start down streak
            if current_down_streak == 0:
                streak_start_date = df.index[i-1]
                streak_start_price = close_prices[i-1]
            current_down_streak += 1
            current_down_change += current_change
            current_down_change_pct = (current_price - streak_start_price) / streak_start_price * 100
            max_down_streak = max(max_down_streak, current_down_streak)
    
    # Handle final streak
    if current_up_streak > 0:
        up_streaks[current_up_streak] += 1
        up_streak_changes.append(float(current_up_change.item()))  # Extract single value
        up_streak_changes_pct.append(float(current_up_change_pct.item()))  # Extract single value
        if current_up_streak > 4:
            long_streak_info['up'].append({
                'length': current_up_streak,
                'start_date': streak_start_date,
                'change': float(current_up_change.item()),
                'change_pct': float(current_up_change_pct.item())
            })
    elif current_down_streak > 0:
        down_streaks[current_down_streak] += 1
        down_streak_changes.append(float(current_down_change.item()))  # Extract single value
        down_streak_changes_pct.append(float(current_down_change_pct.item()))  # Extract single value
        if current_down_streak > 4:
            long_streak_info['down'].append({
                'length': current_down_streak,
                'start_date': streak_start_date,
                'change': float(current_down_change.item()),
                'change_pct': float(current_down_change_pct.item())
            })
    
    return {
        'max_up_streak': max_up_streak,
        'max_down_streak': max_down_streak,
        'up_streaks': dict(up_streaks),
        'down_streaks': dict(down_streaks),
        'max_up_change': max(up_streak_changes) if up_streak_changes else 0,
        'max_down_change': min(down_streak_changes) if down_streak_changes else 0,
        'max_up_change_pct': max(up_streak_changes_pct) if up_streak_changes_pct else 0, #0
        'max_down_change_pct': min(down_streak_changes_pct) if down_streak_changes_pct else 0,
        'avg_up_change': np.mean(up_streak_changes) if up_streak_changes else 0,
        'avg_down_change': np.mean(down_streak_changes) if down_streak_changes else 0,
        'avg_up_change_pct': np.mean(up_streak_changes_pct) if up_streak_changes_pct else 0,
        'avg_down_change_pct': np.mean(down_streak_changes_pct) if down_streak_changes_pct else 0,
        'long_streaks': long_streak_info
    }

def analyze_stock_trends(ticker, timeframe_months=6):
    """
    Analyze stock price trends over a specified timeframe.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    timeframe_months : int
        Number of months to analyze
        
    Returns:
    --------
    tuple: (DataFrame with price data, dict with trend statistics, dict with company info)
    """
    # Get stock info using yfinance
    stock = yf.Ticker(ticker)
    
    # Get company info
    info = stock.info
    company_data = {
        'name': info.get('longName'),
        'exchange': info.get('exchange'),
        'sector': info.get('sector'),
        'industry': info.get('industry'),
        'market_cap': info.get('marketCap')
    }
    
    # Calculate start date
    end_date = datetime.now()
    start_date = end_date - timedelta(days=timeframe_months * 30)
    
    # Download stock data
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    
    if df.empty:
        raise ValueError(f"No data found for ticker {ticker}")
    
    # Get trend statistics
    trends = get_consecutive_trends(df)
    
    return df, trends, company_data

def create_interactive_plots(df, trends, ticker):
    """
    Create interactive plots using plotly.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Price data
    trends : dict
        Trend statistics
    ticker : str
        Stock ticker symbol
    """
    # Create figure with secondary y-axis
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            f'{ticker} Price Chart',
            'Distribution of Consecutive Up/Down Days',
            'Price Change Statistics'
        ),
        vertical_spacing=0.1,
        row_heights=[0.5, 0.25, 0.25],
        specs=[
            [{"type": "xy"}],           # Changed from "candlestick" to "xy"
            [{"type": "xy"}],           # Bar chart
            [{"type": "table"}]         # Table
        ]
    )

    dates = df.index.tolist()
    prices = df['Close'].values.flatten()
    
    # Add price chart
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=prices,
            name='Price',
            mode='lines',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )
    
    # Add distribution of streaks
    max_streak = max(
        max(trends['up_streaks'].keys(), default=0),
        max(trends['down_streaks'].keys(), default=0)
    )
    
    x = list(range(1, max_streak + 1))
    up_counts = [trends['up_streaks'].get(i, 0) for i in x]
    down_counts = [trends['down_streaks'].get(i, 0) for i in x]
    
    fig.add_trace(
        go.Bar(
            x=x,
            y=up_counts,
            name='Up Streaks',
            marker_color='green'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=x,
            y=down_counts,
            name='Down Streaks',
            marker_color='red'
        ),
        row=2, col=1
    )
    
    # Prepare long streak information
    long_up_streaks = trends['long_streaks']['up']
    long_down_streaks = trends['long_streaks']['down']
    
    # Sort long streaks by length
    long_up_streaks.sort(key=lambda x: x['length'], reverse=True)
    long_down_streaks.sort(key=lambda x: x['length'], reverse=True)
    
    # Add statistics table with percentages and long streaks
    table_headers = ['Statistic', 'Value']
    table_rows = [
        ['Max Up Streak', f"{trends['max_up_streak']} days"],
        ['Max Down Streak', f"{trends['max_down_streak']} days"],
        ['Max Up Change', f"${trends['max_up_change']:.2f} ({trends['max_up_change_pct']:.1f}%)"],
        ['Max Down Change', f"${trends['max_down_change']:.2f} ({trends['max_down_change_pct']:.1f}%)"],
        ['Avg Up Change', f"${trends['avg_up_change']:.2f} ({trends['avg_up_change_pct']:.1f}%)"],
        ['Avg Down Change', f"${trends['avg_down_change']:.2f} ({trends['avg_down_change_pct']:.1f}%)"]
    ]
    
    # Add long streak information
    if long_up_streaks:
        table_rows.append(['', ''])  # Spacer
        table_rows.append(['Long Up Streaks (greater than 4 days)', ''])  # Added space instead of empty string
        for streak in long_up_streaks:
            table_rows.append([
                f"{streak['length']} days starting {streak['start_date'].strftime('%Y-%m-%d')}",
                f"${streak['change']:.2f} ({streak['change_pct']:.1f}%)"
            ])
    
    if long_down_streaks:
        table_rows.append(['', ''])  # Spacer
        table_rows.append(['Long Down Streaks (greater than 4 days)', ''])  # Added space instead of empty string
        for streak in long_down_streaks:
            table_rows.append([
                f"{streak['length']} days starting {streak['start_date'].strftime('%Y-%m-%d')}",
                f"${streak['change']:.2f} ({streak['change_pct']:.1f}%)"
            ])

    fig.add_trace(
        go.Table(
            header=dict(
                values=table_headers,
                fill_color='paleturquoise',
                align=['left', 'left']
            ),
            cells=dict(
                values=list(zip(*table_rows)),  # Transpose the rows for plotly's format
                align=['left', 'left']
            )
        ),
        row=3, col=1
    )
    
    # Update layout
    fig.update_layout(
        title_text=f"Stock Analysis for {ticker}",
        height=1200,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    # Update y-axes labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    
    # Update x-axes labels
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Consecutive Days", row=2, col=1)
    
    # Show the plot
    fig.show()

def main():
    # Example usage
    ticker = "AAPL"  # Example: Apple Inc.
    timeframe_months = 24
    
    try:
        # Initialize database
        config = DBConfig(password='password')
        db = DatabaseManager(config)
        
        df, trends, company_data = analyze_stock_trends(ticker, timeframe_months)
        create_interactive_plots(df, trends, ticker)
        
        # Create tables if they don't exist
        db.create_tables()

        # Save company info
        db.save_company_info(ticker, company_data)

        # Save raw stock data
        db.save_raw_stock_data(ticker, df)
        
        # Rest of the main function...

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 