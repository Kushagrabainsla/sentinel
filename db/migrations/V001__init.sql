CREATE TABLE IF NOT EXISTS schema_migrations (
    version       text PRIMARY KEY,
    applied_at    timestamptz NOT NULL DEFAULT now(),
    checksum      text NOT NULL
);

CREATE TABLE IF NOT EXISTS campaigns (
    id            bigserial PRIMARY KEY,
    name          text NOT NULL,
    template_id   text NOT NULL,
    segment_id    text NOT NULL,
    schedule_at   timestamptz,
    state         text NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS contacts (
    id            bigserial PRIMARY KEY,
    account_id    bigint NOT NULL DEFAULT 1,
    email         text NOT NULL UNIQUE,
    status        text NOT NULL DEFAULT 'active',
    attrs         jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
    id                bigserial PRIMARY KEY,
    type              text NOT NULL,
    ts                timestamptz,
    meta              jsonb NOT NULL DEFAULT '{}'::jsonb,
    provider_msg_id   text UNIQUE
);
