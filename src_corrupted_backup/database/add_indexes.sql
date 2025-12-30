-- Database Performance Optimization
-- Add indexes for frequently queried columns

-- Index for orders table (timestamp descending for recent trades)
CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(timestamp DESC);

-- Index for orders table (ticker for filtering)
CREATE INDEX IF NOT EXISTS idx_orders_ticker ON orders(ticker);

-- Composite index for stock_data (ticker + date for range queries)
-- Note: stock_data table is in data_manager.py's database (stock_data.db)
-- This index should be applied there separately if needed

-- Index for positions table (ticker for lookups)
CREATE INDEX IF NOT EXISTS idx_positions_ticker ON positions(ticker);

-- Analyze tables to update statistics
ANALYZE orders;
ANALYZE positions;
ANALYZE balance;
