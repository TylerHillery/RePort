SELECT
    account_name,
    ticker,
    security_name,
    shares,
    target_weight,
    price,
    cost
FROM 
    holdings
ORDER BY
    account_name,ticker