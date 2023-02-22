UPDATE holdings SET
    shares          = ?,
    target_weight   = ?,
    cost            = ?,
    price           = ?    
WHERE
    holding_id = ? 