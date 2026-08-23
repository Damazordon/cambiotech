CREATE TABLE IF NOT EXISTS orders (
    order_id UUID PRIMARY KEY,
    execution_date TEXT NOT NULL,
    currency_pair TEXT NOT NULL,
    executed_rate FLOAT NOT NULL,
    trade_volume FLOAT NOT NULL,
    client_id TEXT NOT NULL
);