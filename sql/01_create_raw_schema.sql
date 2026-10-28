
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.cloud_billing (
    record_id       VARCHAR(50) PRIMARY KEY,
    billing_date    DATE NOT NULL,
    cloud_provider  VARCHAR(20) NOT NULL,
    account_id      VARCHAR(50) NOT NULL,
    service         VARCHAR(100) NOT NULL,
    team            VARCHAR(100) NOT NULL,
    region          VARCHAR(50) NOT NULL,
    usage_quantity  NUMERIC(18, 3) NOT NULL,
    usage_unit      VARCHAR(30) NOT NULL,
    unit_price      NUMERIC(18, 5) NOT NULL,
    gross_cost      NUMERIC(18, 2) NOT NULL,
    discount        NUMERIC(18, 2) NOT NULL DEFAULT 0,
    credits         NUMERIC(18, 2) NOT NULL DEFAULT 0,
    currency        VARCHAR(3) NOT NULL,
    invoice_id      VARCHAR(50) NOT NULL,
    loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_usage_nonnegative
        CHECK (usage_quantity >= 0),

    CONSTRAINT chk_unit_price_nonnegative
        CHECK (unit_price >= 0),

    CONSTRAINT chk_gross_cost_nonnegative
        CHECK (gross_cost >= 0),

    CONSTRAINT chk_discount_nonnegative
        CHECK (discount >= 0),

    CONSTRAINT chk_credits_nonnegative
        CHECK (credits >= 0),

    CONSTRAINT chk_adjustments_within_gross
        CHECK (discount + credits <= gross_cost),

    CONSTRAINT chk_supported_provider
        CHECK (cloud_provider IN ('AWS', 'Azure', 'GCP')),

    CONSTRAINT chk_supported_currency
        CHECK (currency = 'USD')
);

CREATE INDEX IF NOT EXISTS idx_cloud_billing_date
    ON raw.cloud_billing (billing_date);

CREATE INDEX IF NOT EXISTS idx_cloud_billing_provider
    ON raw.cloud_billing (cloud_provider);

CREATE INDEX IF NOT EXISTS idx_cloud_billing_team
    ON raw.cloud_billing (team);
