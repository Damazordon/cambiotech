with fonte as (
    select * from {{ source('bronze', 'bronze_orders') }}
),

campos as (
    
    select
    order_id,                        
        coalesce(
                    try_to_timestamp(execution_date, 'yyyy-MM-dd'),
                    try_to_timestamp(execution_date, 'dd/MM/yyyy')
                )::DATE as execution_date,
        upper(replace(replace(currency_pair, '-', ''), '/', '')) as currency_pair, 
    executed_rate,                     
    trade_volume,                      
    client_id                         
        from fonte
    )
select * from campos

