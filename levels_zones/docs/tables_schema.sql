-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main trading sessions table
CREATE TABLE trading_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ticker_id TEXT UNIQUE NOT NULL,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    is_live BOOLEAN DEFAULT true,
    historical_date DATE,
    historical_time TIME,
    
    -- JSON columns for complex data
    weekly_data JSONB,
    daily_data JSONB,
    
    -- Metrics
    pre_market_price DECIMAL(10,2),
    atr_5min DECIMAL(10,2),
    atr_10min DECIMAL(10,2),
    atr_15min DECIMAL(10,2),
    daily_atr DECIMAL(10,2),
    atr_high DECIMAL(10,2),
    atr_low DECIMAL(10,2),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_ticker_date UNIQUE (ticker, date)
);

-- Price levels table
CREATE TABLE price_levels (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES trading_sessions(id) ON DELETE CASCADE,
    level_id TEXT UNIQUE NOT NULL,
    line_price DECIMAL(10,2) NOT NULL,
    candle_datetime TIMESTAMP NOT NULL,
    candle_high DECIMAL(10,2) NOT NULL,
    candle_low DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_candle_prices CHECK (candle_high >= candle_low),
    CONSTRAINT valid_level_id CHECK (level_id LIKE '%_L%')
);

-- Analysis runs tracking (for historical record)
CREATE TABLE analysis_runs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES trading_sessions(id) ON DELETE CASCADE,
    run_type TEXT NOT NULL, -- 'manual', 'scheduled', 'recalculation'
    run_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completion_timestamp TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'running', -- 'running', 'completed', 'failed'
    metadata JSONB -- Any additional info about the run
);

-- HVN (High Volume Node) zones table with historical tracking
CREATE TABLE hvn_zones (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES trading_sessions(id) ON DELETE CASCADE,
    analysis_run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    zone_high DECIMAL(10,2) NOT NULL,
    zone_low DECIMAL(10,2) NOT NULL,
    volume_profile JSONB, -- Detailed volume data
    percentile_rank INTEGER CHECK (percentile_rank BETWEEN 0 AND 100),
    is_primary_zone BOOLEAN DEFAULT false,
    timeframe TEXT NOT NULL, -- '5min', '15min', 'daily'
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_zone_range CHECK (zone_high > zone_low)
);

-- Camarilla pivot levels table with historical tracking
CREATE TABLE camarilla_levels (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES trading_sessions(id) ON DELETE CASCADE,
    analysis_run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    pivot_point DECIMAL(10,2) NOT NULL,
    r1 DECIMAL(10,2) NOT NULL,
    r2 DECIMAL(10,2) NOT NULL,
    r3 DECIMAL(10,2) NOT NULL,
    r4 DECIMAL(10,2) NOT NULL,
    s1 DECIMAL(10,2) NOT NULL,
    s2 DECIMAL(10,2) NOT NULL,
    s3 DECIMAL(10,2) NOT NULL,
    s4 DECIMAL(10,2) NOT NULL,
    calculated_from_date DATE NOT NULL, -- Which day's data was used
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Confluence scoring table with historical tracking
CREATE TABLE confluence_scores (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES trading_sessions(id) ON DELETE CASCADE,
    analysis_run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    price_level DECIMAL(10,2) NOT NULL,
    score DECIMAL(5,2) NOT NULL, -- 0-100 score
    contributing_factors JSONB, -- Details of what contributed to score
    level_type TEXT, -- 'resistance', 'support', 'pivot'
    rank INTEGER, -- 1 = highest score
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance tracking table
CREATE TABLE performance_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES trading_sessions(id) ON DELETE CASCADE,
    analysis_run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    metric_value DECIMAL(10,4),
    metric_data JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_trading_sessions_ticker_date ON trading_sessions(ticker, date);
CREATE INDEX idx_trading_sessions_ticker_id ON trading_sessions(ticker_id);
CREATE INDEX idx_price_levels_session_id ON price_levels(session_id);
CREATE INDEX idx_price_levels_level_id ON price_levels(level_id);
CREATE INDEX idx_analysis_runs_session_id ON analysis_runs(session_id);
CREATE INDEX idx_analysis_runs_timestamp ON analysis_runs(run_timestamp);
CREATE INDEX idx_hvn_zones_session_id ON hvn_zones(session_id);
CREATE INDEX idx_hvn_zones_analysis_run ON hvn_zones(analysis_run_id);
CREATE INDEX idx_camarilla_levels_session_id ON camarilla_levels(session_id);
CREATE INDEX idx_camarilla_levels_analysis_run ON camarilla_levels(analysis_run_id);
CREATE INDEX idx_confluence_scores_session_id ON confluence_scores(session_id);
CREATE INDEX idx_confluence_scores_analysis_run ON confluence_scores(analysis_run_id);
CREATE INDEX idx_confluence_scores_rank ON confluence_scores(session_id, rank);
CREATE INDEX idx_performance_metrics_session_id ON performance_metrics(session_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to trading_sessions
CREATE TRIGGER update_trading_sessions_updated_at BEFORE UPDATE
    ON trading_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - Optional but recommended
ALTER TABLE trading_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_levels ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE hvn_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE camarilla_levels ENABLE ROW LEVEL SECURITY;
ALTER TABLE confluence_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;

-- Views for easier querying

-- Latest calculations view
CREATE VIEW latest_calculations AS
SELECT DISTINCT ON (cs.session_id, cs.price_level)
    ts.ticker,
    ts.ticker_id,
    ts.date,
    cs.price_level,
    cs.score,
    cs.level_type,
    cs.rank,
    cs.contributing_factors,
    cs.calculated_at
FROM confluence_scores cs
JOIN trading_sessions ts ON cs.session_id = ts.id
ORDER BY cs.session_id, cs.price_level, cs.calculated_at DESC;

-- Session analysis history view
CREATE VIEW session_analysis_history AS
SELECT 
    ts.ticker,
    ts.ticker_id,
    ts.date,
    ar.id as analysis_run_id,
    ar.run_type,
    ar.run_timestamp,
    ar.completion_timestamp,
    ar.status,
    COUNT(DISTINCT hz.id) as hvn_zones_count,
    COUNT(DISTINCT cl.id) as camarilla_levels_count,
    COUNT(DISTINCT cs.id) as confluence_scores_count
FROM trading_sessions ts
JOIN analysis_runs ar ON ts.id = ar.session_id
LEFT JOIN hvn_zones hz ON ar.id = hz.analysis_run_id
LEFT JOIN camarilla_levels cl ON ar.id = cl.analysis_run_id
LEFT JOIN confluence_scores cs ON ar.id = cs.analysis_run_id
GROUP BY ts.ticker, ts.ticker_id, ts.date, ar.id;