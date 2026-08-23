select *
from {{ ref('mart_reconciliacao') }}
where anomalia_flag = true
    and close_rate is not null
    and abs(desvio_percentual) <= {{ var('limite_anomalia_pct', 0.01) }}