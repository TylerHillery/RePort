SELECT
    CASE
        WHEN (future.shares - current.shares) > 0 then 'Buy'
        ELSE 'Sell'
    END AS "Order Type",
    current.ticker AS Ticker,
    future.shares - current.shares AS Shares,
    current.price AS Price,
    (future.shares - current.shares) * -1 * current.price AS "Trade Amount"
FROM
    holdings_df AS current
    INNER JOIN future_holdings_df AS future using(holding_id)
WHERE
    (future.shares - current.shares) != 0           
ORDER BY
    Ticker