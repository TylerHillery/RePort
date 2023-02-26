SELECT 
    account_name,
    ticker,
    security_name,
    shares,
    target_weight,
    cost,
    price 
FROM 
    holdings 
ORDER BY 
    account_name,
    ticker