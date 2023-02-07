UPDATE holdings SET
    account_name    = ?, 
    ticker          = ?,
    shares          = ?,
    target_weight   = ?,
    cost            = ?,
    price           = ?    
WHERE
    account_name    = ?
AND ticker          = ?