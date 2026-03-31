-- ============================================================
-- EXTREMEXP DAL - PostgreSQL Schema (Python Implementation)
-- Version: 1.0
-- PostgreSQL: 11+ (triggers use EXECUTE FUNCTION; for PG < 11 use EXECUTE PROCEDURE)
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- EXPERIMENTS
-- ============================================================
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- All fields nullable (matches Elasticsearch validation behavior)
    name TEXT,
    intent TEXT,
    start TIMESTAMPTZ,
    "end" TIMESTAMPTZ,
    model TEXT,
    comment TEXT,
    status TEXT DEFAULT 'new',

    -- JSONB fields
    metadata JSONB DEFAULT '{}',
    creator JSONB DEFAULT '{}',

    -- Workflow references
    workflow_ids UUID[] DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_created_at ON experiments(created_at DESC);
CREATE INDEX idx_experiments_metadata ON experiments USING GIN (metadata);
CREATE INDEX idx_experiments_creator ON experiments USING GIN (creator);

COMMENT ON TABLE experiments IS 'Stores experiment metadata and configuration';
COMMENT ON COLUMN experiments.model IS 'DSL text representation of experiment';
COMMENT ON COLUMN experiments.workflow_ids IS 'Array of workflow UUIDs belonging to this experiment';

-- ============================================================
-- WORKFLOWS
-- ============================================================
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,

    -- Basic fields
    name TEXT NOT NULL,
    start TIMESTAMPTZ,
    "end" TIMESTAMPTZ,
    comment TEXT,
    status TEXT DEFAULT 'scheduled',

    -- JSONB embedded data (matches Elasticsearch structure)
    parameters JSONB DEFAULT '[]',
    tasks JSONB DEFAULT '[]',
    input_datasets JSONB DEFAULT '[]',
    output_datasets JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',

    -- Metric references
    metric_ids UUID[] DEFAULT '{}',
    metrics JSONB DEFAULT '[]',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workflows_experiment ON workflows(experiment_id);
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_created_at ON workflows(created_at DESC);
CREATE INDEX idx_workflows_start_end ON workflows(start, "end");
CREATE INDEX idx_workflows_metadata ON workflows USING GIN (metadata);

COMMENT ON TABLE workflows IS 'Stores workflow execution instances';
COMMENT ON COLUMN workflows.parameters IS 'Array of workflow parameters (JSONB)';
COMMENT ON COLUMN workflows.tasks IS 'Array of task definitions (JSONB)';
COMMENT ON COLUMN workflows.metrics IS 'Denormalized metric summary for quick access';

-- ============================================================
-- METRICS
-- ============================================================
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,

    -- Parent reference (polymorphic)
    parent_type TEXT NOT NULL CHECK (parent_type IN ('workflow', 'experiment')),
    parent_id UUID NOT NULL,

    -- Metric details
    name TEXT,
    kind TEXT,
    type TEXT,
    semantic_type TEXT,
    value TEXT,
    produced_by_task TEXT,
    date TIMESTAMPTZ,

    -- Records (JSONB for small series)
    records JSONB DEFAULT '[]',

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_experiment ON metrics(experiment_id);
CREATE INDEX idx_metrics_parent ON metrics(parent_type, parent_id);
CREATE INDEX idx_metrics_kind ON metrics(kind);
CREATE INDEX idx_metrics_name ON metrics(name);
CREATE INDEX idx_metrics_semantic_type ON metrics(semantic_type);

COMMENT ON TABLE metrics IS 'Stores performance metrics from workflows';
COMMENT ON COLUMN metrics.parent_type IS 'Type of parent (workflow or experiment)';
COMMENT ON COLUMN metrics.kind IS 'Metric kind: scalar, series, timeseries';
COMMENT ON COLUMN metrics.records IS 'JSONB array of metric records (for series/timeseries)';

-- ============================================================
-- METRIC_RECORDS (Performance optimization for large series)
-- ============================================================
CREATE TABLE metric_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_id UUID NOT NULL REFERENCES metrics(id) ON DELETE CASCADE,
    value DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metric_records_metric ON metric_records(metric_id);
CREATE INDEX idx_metric_records_created ON metric_records(metric_id, created_at);
CREATE INDEX idx_metric_records_timestamp ON metric_records(metric_id, timestamp);

COMMENT ON TABLE metric_records IS 'Normalized metric records for large series (performance optimization)';
COMMENT ON COLUMN metric_records.timestamp IS 'Timestamp for timeseries metrics (nullable for series)';

-- ============================================================
-- METRIC_AGGREGATIONS (Cached aggregation computations)
-- ============================================================
CREATE TABLE metric_aggregations (
    metric_id UUID PRIMARY KEY REFERENCES metrics(id) ON DELETE CASCADE,
    count BIGINT NOT NULL DEFAULT 0,
    sum DOUBLE PRECISION,
    min DOUBLE PRECISION,
    max DOUBLE PRECISION,
    average DOUBLE PRECISION,
    median DOUBLE PRECISION,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE metric_aggregations IS 'Cached aggregation values (count, sum, min, max, avg, median)';
COMMENT ON COLUMN metric_aggregations.median IS 'Median value computed via sorting records';

