SELECT
    'Before' as rebalance,
    ticker,
    shares,
    target_weight,
    current_weight,
    target_diff,
    cost,
    market_value,
    price,
    gain_loss,
    gain_loss_pct,
FROM
    holdings_df
UNION
SELECT
    'After' as rebalance,
    ticker,
    shares,
    target_weight,
    current_weight,
    target_diff,
    cost,
    market_value,
    price,
    gain_loss,
    gain_loss_pct,
FROM
    future_holdings_df
            