WITH 
market_value as (
    SELECT
        holdings.account_name,
        holdings.ticker,
        holdings.security_name,
        holdings.target_weight,
        holdings.price * holdings.shares / 
            (sum(holdings.price * holdings.shares) OVER (PARTITION BY holdings.account_name) + coalesce(cash.cash,0)) * 100 as current_weight,
        holdings.shares,
        holdings.cost,
        holdings.price,
        holdings.price * holdings.shares as market_value,
        cash.cash,
        sum(holdings.price * holdings.shares) OVER (PARTITION BY holdings.account_name) + coalesce(cash.cash,0) as portfolio_market_value
    FROM 
        holdings
        LEFT JOIN cash
            ON holdings.account_name = cash.account_name
),
gain_loss AS (
    SELECT
        *,
        current_weight - target_weight      as target_diff,
        market_value - cost                 as gain_loss,
        (market_value - cost) / cost * 100  as gain_loss_pct
    FROM 
        market_value

),
less_then_zero AS (
    SELECT
        account_name, 
        ticker, 
        target_diff / sum(target_diff) over (partition by account_name) * 100 as pct_to_invest
    FROM gain_loss
    WHERE target_diff < 0

),
pct_to_invest_cte as (
    SELECT
        gain_loss.*,
        coalesce(less_then_zero.pct_to_invest,0) as pct_to_invest
    FROM 
        gain_loss
        LEFT JOIN less_then_zero
            ON  gain_loss.account_name = less_then_zero.account_name
            AND gain_loss.ticker = less_then_zero.ticker
),
shares_to_invest as (
    SELECT
        *,
        floor(pct_to_invest * cash / price / 100)           as dynamic_shares_to_invest_whole,
        pct_to_invest * cash / price / 100                  as dynamic_shares_to_invest_frac,
        floor(target_weight * cash / price / 100)           as target_shares_to_invest_whole,
        target_weight * cash / price / 100                  as target_shares_to_invest_frac,
        floor(target_diff * -1 * portfolio_market_value)    as all_shares_to_invest_whole,
        target_diff * -1 * portfolio_market_value           as all_shares_to_invest_frac,
    FROM pct_to_invest_cte
)
SELECT 
    account_name,
    ticker,
    security_name,
    shares,
    target_weight,
    current_weight,
    target_diff,
    pct_to_invest,
    round(cost,2) as cost,
    round(market_value,2) as market_value,
    round(price,2) as price,
    gain_loss,
    gain_loss_pct,
    round(cash,2) as cash,
    round(portfolio_market_value,2) as portfolio_market_value,
    dynamic_shares_to_invest_whole,
    dynamic_shares_to_invest_frac,
    target_shares_to_invest_whole,
    target_shares_to_invest_frac,
    all_shares_to_invest_whole,
    all_shares_to_invest_frac
FROM
    shares_to_invest
ORDER BY
    account_name,
    ticker