-- Database already created via createdb command

-- Traders table to store basic trader information
CREATE TABLE IF NOT EXISTS traders (
    id SERIAL PRIMARY KEY,
    address VARCHAR(42) UNIQUE NOT NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Performance metrics table (stores daily snapshots)
CREATE TABLE IF NOT EXISTS trader_performance (
    id SERIAL PRIMARY KEY,
    trader_id INTEGER REFERENCES traders(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    pnl_percentage DECIMAL(10, 2),
    pnl_absolute DECIMAL(20, 8),
    win_rate DECIMAL(5, 2),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    avg_win DECIMAL(20, 8),
    avg_loss DECIMAL(20, 8),
    account_value DECIMAL(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trader_id, date)
);

-- Positions table to track all positions
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    trader_id INTEGER REFERENCES traders(id) ON DELETE CASCADE,
    coin VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- 'LONG' or 'SHORT'
    entry_price DECIMAL(20, 8) NOT NULL,
    size DECIMAL(20, 8) NOT NULL,
    leverage DECIMAL(5, 2),
    position_value DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8),
    margin_used DECIMAL(20, 8),
    liquidation_price DECIMAL(20, 8),
    transaction_hash VARCHAR(66), -- Hyperliquid transaction hash (0x + 64 chars)
    opened_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP,
    close_price DECIMAL(20, 8),
    realized_pnl DECIMAL(20, 8),
    status VARCHAR(20) DEFAULT 'OPEN', -- 'OPEN', 'CLOSED'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trade opportunities table
CREATE TABLE IF NOT EXISTS trade_opportunities (
    id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(id) ON DELETE CASCADE,
    trader_id INTEGER REFERENCES traders(id) ON DELETE CASCADE,
    coin VARCHAR(20) NOT NULL,
    loser_side VARCHAR(10) NOT NULL,
    suggested_side VARCHAR(10) NOT NULL,
    loser_entry_price DECIMAL(20, 8) NOT NULL,
    suggested_entry_price DECIMAL(20, 8),
    confidence_score DECIMAL(5, 2),
    status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'EXECUTED', 'EXPIRED', 'CANCELLED'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    expired_at TIMESTAMP
);

-- Our trades table (tracks what we actually did)
CREATE TABLE IF NOT EXISTS our_trades (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES trade_opportunities(id) ON DELETE CASCADE,
    coin VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    size DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8),
    pnl DECIMAL(20, 8),
    pnl_percentage DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'OPEN',
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

-- API logs table for tracking rate limits
CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    weight_used INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_traders_address ON traders(address);
CREATE INDEX IF NOT EXISTS idx_trader_performance_trader_id_date ON trader_performance(trader_id, date);
CREATE INDEX IF NOT EXISTS idx_positions_trader_id_status ON positions(trader_id, status);
CREATE INDEX IF NOT EXISTS idx_positions_opened_at ON positions(opened_at);
CREATE INDEX IF NOT EXISTS idx_trade_opportunities_status ON trade_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_logs(created_at);

-- Views for easier querying
CREATE OR REPLACE VIEW v_trader_30d_performance AS
SELECT 
    t.id,
    t.address,
    AVG(tp.pnl_percentage) as avg_pnl_percentage,
    SUM(tp.pnl_absolute) as total_pnl,
    AVG(tp.win_rate) as avg_win_rate,
    SUM(tp.total_trades) as total_trades,
    MAX(tp.date) as last_updated
FROM traders t
JOIN trader_performance tp ON t.id = tp.trader_id
WHERE tp.date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY t.id, t.address;

CREATE OR REPLACE VIEW v_top_losers AS
SELECT 
    *,
    RANK() OVER (ORDER BY avg_pnl_percentage ASC) as loss_rank
FROM v_trader_30d_performance
WHERE avg_pnl_percentage < 0
ORDER BY avg_pnl_percentage ASC
LIMIT 500;