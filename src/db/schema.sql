-- Financial Assistant Schema for Supabase PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_date TIMESTAMPTZ NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'UAH',
    category VARCHAR(100) NOT NULL DEFAULT 'Інше',
    description TEXT,
    source VARCHAR(50) NOT NULL DEFAULT 'generic',
    dedup_hash VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fast time-series and analytical queries
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions (category);
CREATE INDEX IF NOT EXISTS idx_transactions_date_category ON transactions (transaction_date, category);
CREATE INDEX IF NOT EXISTS idx_transactions_dedup ON transactions (dedup_hash);

-- Enable Row Level Security (RLS)
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Allow full access for service_role and authenticated users
CREATE POLICY IF NOT EXISTS "Allow full access to transactions" ON transactions
    FOR ALL
    USING (true)
    WITH CHECK (true);
