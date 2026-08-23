with fonte as (
    select * from {{ source('bronze', 'bronze_fx_rates') }}
),

deduplicado as (
    select
        execution_date::DATE AS execution_date,
        from_symbol,
        to_symbol,
        close_rate,
        source_file,
        ingested_at
    from fonte
    qualify row_number() over (
        partition by execution_date
        order by ingested_at desc
    ) = 1
)

select * from deduplicado