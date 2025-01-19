from db_config import DBConfig
from db_operations import DatabaseManager
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import text

#TODO check general update logic streaks
#TODO check update long streaks
#TODO update streak statistics
class DatabaseUpdater:
    def __init__(self):
        self.config = DBConfig()
        self.db = DatabaseManager(self.config)
        
    def get_latest_dates(self):
        """Get the latest date for each ticker in raw_stock_data"""
        session = self.db.Session()
        try:
            query = text("""
                SELECT ticker, MAX(date) as last_date
                FROM raw_stock_data
                GROUP BY ticker
            """)
            result = session.execute(query)
            return {row.ticker: row.last_date for row in result}
        finally:
            session.close()
    
    def get_ongoing_streaks(self):
        """Get the most recent streak for each ticker"""
        session = self.db.Session()
        try:
            query = text("""
                WITH ranked_streaks AS (
                    SELECT 
                        ticker,
                        streak_type,
                        start_date,
                        end_date,
                        length,
                        total_change,
                        total_change_pct,
                        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY end_date DESC) as rn
                    FROM long_streaks
                )
                SELECT *
                FROM ranked_streaks
                WHERE rn = 1
            """)
            result = session.execute(query)
            return {row.ticker: {
                'type': row.streak_type,
                'start_date': row.start_date,
                'end_date': row.end_date,
                'length': row.length,
                'total_change': float(row.total_change),
                'total_change_pct': float(row.total_change_pct)
            } for row in result}
        finally:
            session.close()
    
    def update_raw_data(self, ticker: str, last_date: datetime):
        """Update raw stock data from last_date to today"""
        today = datetime.now().date()  # Convert to date
        
        if (today - last_date) < timedelta(days=1):
            return None
            
        # Download only new data
        df = yf.download(ticker, start=last_date + timedelta(days=1), 
                        end=today, progress=False)
        
        if not df.empty:
            self.db.save_raw_stock_data(ticker, df)
            return df
        return None
    
    def update_streaks(self, ticker: str, ongoing_streak: dict, new_data: pd.DataFrame):
        """Update streak information incrementally"""
        if new_data is None or new_data.empty:
            return
            
        session = self.db.Session()
        try:
            # Get the last price from previous data
            query = text("""
                SELECT close 
                FROM raw_stock_data 
                WHERE ticker = :ticker AND date = :date
            """)
            prev_close = session.execute(query, {
                'ticker': ticker, 
                'date': ongoing_streak['end_date']
            }).scalar()
            prev_close = float(prev_close)

            # Simplify the DataFrame structure by selecting only the Close column
            close_series = new_data['Close'][ticker] if isinstance(new_data['Close'], pd.DataFrame) else new_data['Close']
            
            # Calculate daily changes
            prev_closes = pd.Series(index=close_series.index)
            prev_closes.iloc[0] = prev_close
            prev_closes.iloc[1:] = close_series.iloc[:-1].values
            
            daily_changes = close_series - prev_closes
            
            # Check if ongoing streak continues
            current_streak = ongoing_streak.copy()
            
            for date, daily_change in daily_changes.items():
                close_price = close_series[date]
                
                if (current_streak['type'] == 'up' and daily_change > 0) or \
                   (current_streak['type'] == 'down' and daily_change < 0):
                    # Streak continues
                    current_streak['length'] += 1
                    current_streak['end_date'] = date
                    current_streak['total_change'] += float(daily_change)
                    current_streak['total_change_pct'] = \
                        (float(close_price) - float(prev_close)) / float(prev_close) * 100
                else:
                    # Streak ends, save it and start new one
                    if current_streak['length'] > 4:  # Only save long streaks
                        self._save_streak(ticker, current_streak)
                    
                    # Start new streak
                    prev_price = prev_closes[date]
                    current_streak = {
                        'type': 'up' if daily_change > 0 else 'down',
                        'start_date': date,
                        'end_date': date,
                        'length': 1,
                        'total_change': float(daily_change),
                        'total_change_pct': float(daily_change) / float(prev_price) * 100
                    }
                    
            # Save final streak if it's long enough
            if current_streak['length'] > 4:
                self._save_streak(ticker, current_streak)
                
        finally:
            session.close()
    
    def _save_streak(self, ticker: str, streak: dict):
        """Save a single streak to database"""
        next_day = streak['end_date'] + timedelta(days=1)
        
        # Get next day's change if available
        session = self.db.Session()
        try:
            query = text("""
                SELECT close 
                FROM raw_stock_data 
                WHERE ticker = :ticker AND date = :date
            """)
            next_day_close = session.execute(query, {
                'ticker': ticker, 
                'date': next_day
            }).scalar()
            
            if next_day_close is not None:
                end_close = session.execute(query, {
                    'ticker': ticker, 
                    'date': streak['end_date']
                }).scalar()
                
                next_day_change = float(next_day_close) - float(end_close)
                next_day_change_pct = next_day_change / float(end_close) * 100
            else:
                next_day_change = 0.0
                next_day_change_pct = 0.0
                
            # Save streak
            self.db.save_long_streaks(ticker, [{
                'type': streak['type'],
                'start_date': streak['start_date'],
                'end_date': streak['end_date'],
                'length': streak['length'],
                'change': streak['total_change'],
                'change_pct': streak['total_change_pct'],
                'next_day_change': next_day_change,
                'next_day_change_pct': next_day_change_pct
            }])
            
        finally:
            session.close()
    
    def update_all(self):
        """Update all data in database"""
        # Get latest dates and ongoing streaks
        latest_dates = self.get_latest_dates()
        ongoing_streaks = self.get_ongoing_streaks()
        
        # Update each ticker
        for ticker in latest_dates.keys():
            try:
                print(f"Updating {ticker}...")

                # Update raw data
                new_data = self.update_raw_data(ticker, latest_dates[ticker])

                # Update streaks if we have new data
                if new_data is not None and ticker in ongoing_streaks:
                    self.update_streaks(ticker, ongoing_streaks[ticker], new_data)

                # Update company info occasionally (e.g., weekly)
                last_update = self.get_company_last_update(ticker)
                if (datetime.now() - last_update).days >= 7:
                    self.update_company_info(ticker)
            except:
                print('Exception while updating ticker ' + ticker)
    
    def get_company_last_update(self, ticker: str) -> datetime:
        """Get the last update time for a company"""
        session = self.db.Session()
        try:
            query = text("""
                SELECT last_updated 
                FROM companies 
                WHERE ticker = :ticker
            """)
            return session.execute(query, {'ticker': ticker}).scalar()
        finally:
            session.close()
    
    def update_company_info(self, ticker: str):
        """Update company information"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            company_data = {
                'name': info.get('longName'),
                'exchange': info.get('exchange'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap')
            }
            self.db.save_company_info(ticker, company_data)
        except Exception as e:
            print(f"Error updating company info for {ticker}: {str(e)}")

if __name__ == "__main__":
    updater = DatabaseUpdater()
    updater.update_all() 