with orders as (
    select * from {{ ref('stg_orders') }}
),

fx as (
    select 
        execution_date,
        from_symbol || to_symbol as currency_pair,
        close_rate
    from {{ ref('stg_fx_rates') }}
),

reconciliado as (
    select
        orders.order_id,
        orders.execution_date,
        orders.currency_pair,
        orders.executed_rate,
        fx.close_rate,
        orders.executed_rate - fx.close_rate as desvio_absoluto,
        (orders.executed_rate - fx.close_rate) / fx.close_rate as desvio_percentual,
        orders.trade_volume,
        orders.client_id
    from orders
    left join fx
        on orders.execution_date = fx.execution_date
        and orders.currency_pair = fx.currency_pair
)

select
    *,
    case
        when close_rate is null then true
        when abs(desvio_percentual) > {{ var('limite_anomalia_pct', 0.01) }} then true
        else false
    end as anomalia_flag
from reconciliado


