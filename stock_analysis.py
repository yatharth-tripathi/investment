"""
Stock Analysis Library

This module provides comprehensive analysis functionality for stock data stored in the database.
It implements various technical indicators, filters, and sorting capabilities based on available data.
"""

from typing import List, Dict, Union, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import func, and_, or_, desc, text
from sqlalchemy.orm import Session
from models import RawStockData, Company, StreakStatistic, LongStreak
from db_config import DBConfig
from db_operations import DatabaseManager

class StockAnalyzer:
    def __init__(self, config: DBConfig = None):
        if config is None:
            config = DBConfig()
        self.db = DatabaseManager(config)
        self.session = self.db.Session()

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()

    def _to_list(self, tickers: Union[str, List[str]]) -> List[str]:
        """Convert single ticker to list if necessary."""
        return [tickers] if isinstance(tickers, str) else tickers

    def get_current_price(self, tickers: Union[str, List[str]], date: Optional[datetime] = None) -> pd.DataFrame:
        """Get the most recent closing price for given tickers."""
        tickers = self._to_list(tickers)
        
        subq = self.session.query(
            RawStockData.ticker,
            RawStockData.date,
            RawStockData.close,
            func.row_number().over(
                partition_by=RawStockData.ticker,
                order_by=desc(RawStockData.date)
            ).label('rn')
        ).filter(
            RawStockData.ticker.in_(tickers),
            RawStockData.date <= (date if date else func.current_date())
        ).subquery()
        
        query = self.session.query(
            subq.c.ticker,
            subq.c.date,
            subq.c.close.label('current_price')
        ).filter(subq.c.rn == 1)
        
        return pd.read_sql(query.statement, self.session.bind)

    def get_price_changes(self, tickers: Union[str, List[str]], lookback_days: int = 252) -> pd.DataFrame:
        """Calculate price changes and returns over specified period."""
        tickers = self._to_list(tickers)
        
        # Using window functions with SQLAlchemy
        window = func.lag(RawStockData.close, lookback_days).over(
            partition_by=RawStockData.ticker,
            order_by=RawStockData.date
        )
        
        query = self.session.query(
            RawStockData.ticker,
            RawStockData.date,
            RawStockData.close.label('current_price'),
            window.label('past_price'),
            (100 * (RawStockData.close - window) / window).label('price_change_pct')
        ).filter(
            RawStockData.ticker.in_(tickers)
        ).order_by(desc(RawStockData.date))
        
        return pd.read_sql(query.statement, self.session.bind)

    def get_high_low_analysis(self, tickers: Union[str, List[str]], periods: List[int] = [13, 26, 52]) -> pd.DataFrame:
        """Get high and low prices for multiple periods (in weeks)."""
        tickers = self._to_list(tickers)
        results = pd.DataFrame([])
        
        for period in periods:
            weeks_ago = datetime.now() - timedelta(weeks=period)
            
            query = self.session.query(
                RawStockData.ticker,
                func.max(RawStockData.high).label(f'high_{period}w'),
                func.min(RawStockData.low).label(f'low_{period}w'),
                Company.name,
                Company.sector,
                Company.industry
            ).join(
                Company,
                RawStockData.ticker == Company.ticker
            ).filter(
                RawStockData.ticker.in_(tickers),
                RawStockData.date >= weeks_ago
            ).group_by(
                RawStockData.ticker,
                Company.name,
                Company.sector,
                Company.industry
            )
            
            df = pd.read_sql(query.statement, self.session.bind)
            if results.empty:
                results = df
            else:
                results = pd.merge(results, df, on=['ticker', 'name', 'sector', 'industry'])
        
        return results

    def get_volume_analysis(self, tickers: Union[str, List[str]], days: int = 30) -> pd.DataFrame:
        """Calculate volume statistics including average daily volume and changes."""
        tickers = self._to_list(tickers)
        days_ago = datetime.now() - timedelta(days=days)
        
        latest_volume = func.first_value(RawStockData.volume).over(
            partition_by=RawStockData.ticker,
            order_by=desc(RawStockData.date)
        )
        
        query = self.session.query(
            RawStockData.ticker,
            func.avg(RawStockData.volume).label('avg_daily_volume'),
            func.max(RawStockData.volume).label('max_volume'),
            func.min(RawStockData.volume).label('min_volume'),
            latest_volume.label('latest_volume'),
            Company.name,
            Company.sector,
            Company.industry
        ).join(
            Company,
            RawStockData.ticker == Company.ticker
        ).filter(
            RawStockData.ticker.in_(tickers),
            RawStockData.date >= days_ago
        ).group_by(
            RawStockData.ticker,
            Company.name,
            Company.sector,
            Company.industry
        )
        
        df = pd.read_sql(query.statement, self.session.bind)
        df['volume_change_from_avg_pct'] = (
            (df['latest_volume'] - df['avg_daily_volume']) / df['avg_daily_volume'] * 100
        )
        return df

    def calculate_moving_averages(self, tickers: Union[str, List[str]], 
                                windows: List[int] = [20, 50, 200]) -> pd.DataFrame:
        """Calculate various moving averages for given tickers."""
        tickers = self._to_list(tickers)
        
        # Create dynamic window functions for each MA period
        ma_columns = []
        for w in windows:
            ma = func.avg(RawStockData.close).over(
                partition_by=RawStockData.ticker,
                order_by=RawStockData.date,
                rows=(w-1, 0)
            ).label(f'ma_{w}')
            ma_columns.append(ma)
        
        query = self.session.query(
            RawStockData.ticker,
            RawStockData.date,
            RawStockData.close,
            *ma_columns
        ).filter(
            RawStockData.ticker.in_(tickers)
        ).order_by(
            RawStockData.ticker,
            desc(RawStockData.date)
        )
        
        return pd.read_sql(query.statement, self.session.bind)

    def calculate_rsi(self, tickers: Union[str, List[str]], period: int = 14) -> pd.DataFrame:
        """Calculate Relative Strength Index (RSI) using pandas for better performance."""
        tickers = self._to_list(tickers)
        
        # Get the raw price data
        query = self.session.query(
            RawStockData.ticker,
            RawStockData.date,
            RawStockData.close
        ).filter(
            RawStockData.ticker.in_(tickers)
        ).order_by(
            RawStockData.ticker,
            RawStockData.date
        )
        
        df = pd.read_sql(query.statement, self.session.bind)
        
        # Calculate RSI using pandas
        df['price_change'] = df.groupby('ticker')['close'].diff()
        df['gain'] = df['price_change'].clip(lower=0)
        df['loss'] = -df['price_change'].clip(upper=0)
        
        # Calculate average gain and loss
        df['avg_gain'] = df.groupby('ticker')['gain'].rolling(
            window=period, min_periods=period
        ).mean().reset_index(0, drop=True)
        
        df['avg_loss'] = df.groupby('ticker')['loss'].rolling(
            window=period, min_periods=period
        ).mean().reset_index(0, drop=True)
        
        # Calculate RSI
        df['rsi'] = 100 - (100 / (1 + df['avg_gain'] / df['avg_loss']))
        
        return df[['ticker', 'date', 'close', 'rsi']].sort_values(['ticker', 'date'], ascending=[True, False])

    def get_streak_analysis(self, tickers: Union[str, List[str]], 
                          min_streak_length: int = 3) -> pd.DataFrame:
        """Get streak analysis from the streak_statistics table."""
        tickers = self._to_list(tickers)
        
        query = self.session.query(
            StreakStatistic,
            Company.name,
            Company.sector,
            Company.industry
        ).join(
            Company,
            StreakStatistic.ticker == Company.ticker
        ).filter(
            StreakStatistic.ticker.in_(tickers),
            or_(
                StreakStatistic.max_up_streak >= min_streak_length,
                StreakStatistic.max_down_streak >= min_streak_length
            )
        ).order_by(desc(StreakStatistic.analysis_date))
        
        return pd.read_sql(query.statement, self.session.bind)

    def filter_by_criteria(self, criteria: Dict) -> pd.DataFrame:
        """Filter stocks based on multiple criteria."""
        query = self.session.query(
            Company.ticker,
            Company.name,
            Company.sector,
            Company.industry,
            Company.market_cap,
            Company.exchange,
            RawStockData.close.label('current_price'),
            RawStockData.volume.label('latest_volume'),
            StreakStatistic.max_up_streak,
            StreakStatistic.max_down_streak
        ).join(
            RawStockData,
            and_(
                Company.ticker == RawStockData.ticker,
                RawStockData.date == self.session.query(func.max(RawStockData.date)).filter(
                    RawStockData.ticker == Company.ticker
                ).scalar_subquery()
            )
        ).outerjoin(
            StreakStatistic,
            Company.ticker == StreakStatistic.ticker
        )
        
        # Apply filters
        if criteria.get('min_price'):
            query = query.filter(RawStockData.close >= criteria['min_price'])
        if criteria.get('max_price'):
            query = query.filter(RawStockData.close <= criteria['max_price'])
        if criteria.get('min_volume'):
            query = query.filter(RawStockData.volume >= criteria['min_volume'])
        if criteria.get('sector'):
            query = query.filter(Company.sector == criteria['sector'])
        if criteria.get('min_market_cap'):
            query = query.filter(Company.market_cap >= criteria['min_market_cap'])
        if criteria.get('max_market_cap'):
            query = query.filter(Company.market_cap <= criteria['max_market_cap'])
        if criteria.get('exchange'):
            query = query.filter(Company.exchange == criteria['exchange'])
        if criteria.get('min_up_streak'):
            query = query.filter(StreakStatistic.max_up_streak >= criteria['min_up_streak'])
        if criteria.get('min_down_streak'):
            query = query.filter(StreakStatistic.max_down_streak >= criteria['min_down_streak'])
        
        return pd.read_sql(query.statement, self.session.bind)

    def calculate_volatility(self, tickers: Union[str, List[str]], window: int = 252) -> pd.DataFrame:
        """Calculate historical volatility using pandas for better performance."""
        tickers = self._to_list(tickers)
        
        query = self.session.query(
            RawStockData.ticker,
            RawStockData.date,
            RawStockData.close
        ).filter(
            RawStockData.ticker.in_(tickers)
        ).order_by(
            RawStockData.ticker,
            RawStockData.date
        )
        
        df = pd.read_sql(query.statement, self.session.bind)
        
        # Calculate daily returns
        df['daily_return'] = df.groupby('ticker')['close'].apply(
            lambda x: np.log(x / x.shift(1))
        )
        
        # Calculate rolling standard deviation and annualize
        df['annualized_volatility'] = df.groupby('ticker')['daily_return'].rolling(
            window=window, min_periods=window
        ).std().reset_index(0, drop=True) * np.sqrt(252)
        
        return df[['ticker', 'date', 'annualized_volatility']].sort_values(
            ['ticker', 'date'], ascending=[True, False]
        )

    def get_sector_performance(self, timeframe_days: int = 30) -> pd.DataFrame:
        """Calculate sector-wide performance metrics."""
        days_ago = datetime.now() - timedelta(days=timeframe_days)
        
        # Get start and end prices for each stock
        subq = self.session.query(
            Company.sector,
            RawStockData.ticker,
            func.first_value(RawStockData.close).over(
                partition_by=RawStockData.ticker,
                order_by=desc(RawStockData.date)
            ).label('current_price'),
            func.first_value(RawStockData.close).over(
                partition_by=RawStockData.ticker,
                order_by=RawStockData.date
            ).label('start_price')
        ).join(
            RawStockData,
            Company.ticker == RawStockData.ticker
        ).filter(
            RawStockData.date >= days_ago,
            Company.sector.isnot(None)
        ).subquery()
        
        query = self.session.query(
            subq.c.sector,
            func.count(func.distinct(subq.c.ticker)).label('num_companies'),
            func.avg(
                100 * (subq.c.current_price - subq.c.start_price) / subq.c.start_price
            ).label('avg_sector_return'),
            func.min(
                100 * (subq.c.current_price - subq.c.start_price) / subq.c.start_price
            ).label('min_return'),
            func.max(
                100 * (subq.c.current_price - subq.c.start_price) / subq.c.start_price
            ).label('max_return')
        ).group_by(
            subq.c.sector
        ).order_by(text('avg_sector_return DESC'))
        
        return pd.read_sql(query.statement, self.session.bind)

    def get_available_sectors(self) -> List[str]:
        """Get list of all available sectors in the database."""
        return [r[0] for r in self.session.query(Company.sector).filter(
            Company.sector.isnot(None)
        ).distinct().order_by(Company.sector).all()]

    def get_available_industries(self, sector: Optional[str] = None) -> List[str]:
        """Get list of all available industries, optionally filtered by sector."""
        query = self.session.query(Company.industry).filter(Company.industry.isnot(None))
        if sector:
            query = query.filter(Company.sector == sector)
        return [r[0] for r in query.distinct().order_by(Company.industry).all()] 