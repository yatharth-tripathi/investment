from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, BigInteger, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class RawStockData(Base):
    __tablename__ = 'raw_stock_data'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric(12, 4))
    high = Column(Numeric(12, 4))
    low = Column(Numeric(12, 4))
    close = Column(Numeric(12, 4))
    volume = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('ticker', 'date', name='uix_ticker_date'),
        Index('idx_raw_stock_ticker_date', 'ticker', 'date')
    )

class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), unique=True, nullable=False)
    name = Column(String(255))
    exchange = Column(String(10))
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(Numeric(20, 2))
    last_updated = Column(DateTime, default=datetime.utcnow)

class StreakStatistic(Base):
    __tablename__ = 'streak_statistics'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    analysis_date = Column(Date, nullable=False)
    timeframe_months = Column(Integer, nullable=False)
    max_up_streak = Column(Integer)
    max_down_streak = Column(Integer)
    max_up_change = Column(Numeric(12, 4))
    max_down_change = Column(Numeric(12, 4))
    max_up_change_pct = Column(Numeric(8, 4))
    max_down_change_pct = Column(Numeric(8, 4))
    avg_up_change = Column(Numeric(12, 4))
    avg_down_change = Column(Numeric(12, 4))
    avg_up_change_pct = Column(Numeric(8, 4))
    avg_down_change_pct = Column(Numeric(8, 4))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('ticker', 'analysis_date', 'timeframe_months'),
        Index('idx_streak_statistics_ticker', 'ticker')
    )

class LongStreak(Base):
    __tablename__ = 'long_streaks'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    streak_type = Column(String(4), nullable=False)  # 'up' or 'down'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    length = Column(Integer, nullable=False)
    total_change = Column(Numeric(12, 4))
    total_change_pct = Column(Numeric(8, 4))
    next_day_change = Column(Numeric(12, 4))
    next_day_change_pct = Column(Numeric(8, 4))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('ticker', 'start_date', 'streak_type'),
        Index('idx_long_streaks_ticker', 'ticker')
    ) 