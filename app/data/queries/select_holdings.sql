SELECT
    account_name,
    ticker,
    security_name,
    target_weight,
    shares,
    cost,
    price
FROM 
    holdings
ORDER BY
    account_name,ticker