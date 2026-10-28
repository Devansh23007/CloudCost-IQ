
SELECT
    billing_date,
    cloud_provider,
    team,
    service,
    currency,

    COUNT(*) AS billing_record_count,
    COUNT(DISTINCT account_id) AS account_count,

    ROUND(SUM(gross_cost), 2) AS gross_cost,
    ROUND(SUM(discount), 2) AS total_discount,
    ROUND(SUM(credits), 2) AS total_credits,
    ROUND(SUM(net_cost), 2) AS net_cost

FROM {{ ref('stg_cloud_billing') }}

GROUP BY
    billing_date,
    cloud_provider,
    team,
    service,
    currency
