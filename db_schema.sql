-- Raw stock data table
CREATE TABLE IF NOT EXISTS raw_stock_data (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);

-- Companies information
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255),
    exchange VARCHAR(10),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap DECIMAL(20,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Streak statistics
CREATE TABLE IF NOT EXISTS streak_statistics (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    analysis_date DATE NOT NULL,
    timeframe_months INTEGER NOT NULL,
    max_up_streak INTEGER,
    max_down_streak INTEGER,
    max_up_change DECIMAL(12,4),
    max_down_change DECIMAL(12,4),
    max_up_change_pct DECIMAL(8,4),
    max_down_change_pct DECIMAL(8,4),
    avg_up_change DECIMAL(12,4),
    avg_down_change DECIMAL(12,4),
    avg_up_change_pct DECIMAL(8,4),
    avg_down_change_pct DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, analysis_date, timeframe_months)
);

-- Long streak details
CREATE TABLE IF NOT EXISTS long_streaks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    streak_type VARCHAR(4) NOT NULL, -- 'up' or 'down'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    length INTEGER NOT NULL,
    total_change DECIMAL(12,4),
    total_change_pct DECIMAL(8,4),
    next_day_change DECIMAL(12,4),
    next_day_change_pct DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, start_date, streak_type)
);

-- Create indexes
CREATE INDEX idx_raw_stock_ticker_date ON raw_stock_data(ticker, date);
CREATE INDEX idx_long_streaks_ticker ON long_streaks(ticker);
CREATE INDEX idx_streak_statistics_ticker ON streak_statistics(ticker); 