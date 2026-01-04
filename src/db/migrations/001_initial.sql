-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    carrier VARCHAR(100),
    insured_name VARCHAR(255),
    property_address TEXT,
    materials_cost DECIMAL(12, 2),
    labor_cost DECIMAL(12, 2),
    other_costs DECIMAL(12, 2),
    minimum_margin DECIMAL(5, 4) DEFAULT 0.33,
    estimate_pdf BYTEA,
    photos JSONB DEFAULT '[]'::jsonb,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_carrier ON jobs(carrier);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- Examples table (carrier before/after supplementation examples)
CREATE TABLE IF NOT EXISTS examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    carrier VARCHAR(100) NOT NULL,
    insurance_estimate TEXT NOT NULL,
    supplementation TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_examples_carrier ON examples(carrier);

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for jobs updated_at
DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
