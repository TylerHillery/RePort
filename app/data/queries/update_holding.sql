UPDATE holdings SET
    account_name    = ?, 
    ticker          = ?,
    shares          = ?,
    cost            = ?,
    target_weight   = ?
WHERE
    account_name    = ?
AND ticker          = ?