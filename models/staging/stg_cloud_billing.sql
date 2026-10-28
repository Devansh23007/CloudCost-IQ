
WITH source_data AS (

    SELECT *
    FROM {{ source('raw', 'cloud_billing') }}

),

cleaned AS (

    SELECT
        record_id,
        billing_date,
        cloud_provider,
        account_id,
        service,
        team,
        region,

        usage_quantity::NUMERIC(18, 3) AS usage_quantity,
        usage_unit,
        unit_price::NUMERIC(18, 5) AS unit_price,

        gross_cost::NUMERIC(18, 2) AS gross_cost,
        discount::NUMERIC(18, 2) AS discount,
        credits::NUMERIC(18, 2) AS credits,

        currency,
        invoice_id,
        loaded_at

    FROM source_data

)

SELECT
    *,
    ROUND(
        gross_cost - discount - credits,
        2
    ) AS net_cost

FROM cleaned
