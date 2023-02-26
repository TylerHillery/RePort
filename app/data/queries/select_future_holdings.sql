WITH 
market_value as (
    SELECT
        future_holdings.holding_id,
        future_holdings.account_name,
        future_holdings.ticker,
        future_holdings.security_name,
        future_holdings.target_weight,
        future_holdings.price * future_holdings.shares / 
            (sum(future_holdings.price * future_holdings.shares) OVER (PARTITION BY future_holdings.account_name) + coalesce(future_cash.cash,0)) * 100 as current_weight,
        future_holdings.shares,
        future_holdings.cost,
        future_holdings.price,
        future_holdings.price * future_holdings.shares as market_value,
        future_cash.cash,
        sum(future_holdings.price * future_holdings.shares) OVER (PARTITION BY future_holdings.account_name) + coalesce(future_cash.cash,0) as portfolio_market_value
    FROM 
        future_holdings
        LEFT JOIN future_cash
            ON future_holdings.account_name = future_cash.account_name
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
        case 
            when target_diff >= 0
                then ceiling(target_diff / 100 * -1 * portfolio_market_value / price)
            else
                floor(target_diff / 100 * -1 * portfolio_market_value / price)
            end as all_shares_to_invest_whole,
        
        target_diff / 100 * -1 * portfolio_market_value / price as all_shares_to_invest_frac,
    FROM pct_to_invest_cte
)
SELECT 
    holding_id, 
    account_name,
    ticker,
    security_name,
    shares,
    target_weight,
    current_weight,
    round(target_diff,4) as target_diff,
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