SELECT
    holdings.account_name,
    holdings.ticker,
    holdings.security_name,
    holdings.price * holdings.shares / 
        (
            sum(holdings.price * holdings.shares) OVER (PARTITION BY holdings.account_name) + coalesce(cash.cash,0)
        ) * 100 as current_weight,
    holdings.target_weight,
    holdings.shares,
    holdings.cost,
    holdings.price,
    cash.cash, 
    sum(holdings.price * holdings.shares) OVER (PARTITION BY holdings.account_name) + coalesce(cash.cash,0) as portfolio_market_value
FROM 
    holdings
    LEFT JOIN cash
        ON holdings.account_name = cash.account_name
ORDER BY
    holdings.account_name,
    holdings.ticker