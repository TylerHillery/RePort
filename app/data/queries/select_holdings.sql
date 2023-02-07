SELECT
    account_name,
    ticker,
    security_name,
    target_weight,
    (price * shares / sum(price * shares) over(partition by account_name)) * 100 as current_weight,
    shares,
    cost,
    price
FROM 
    holdings
ORDER BY
    account_name,ticker