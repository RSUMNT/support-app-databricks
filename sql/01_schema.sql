-- ============================================================
-- Support Ticket schema for Lakebase (Postgres)
-- Run this in a Databricks SQL editor connected to your Lakebase
-- instance, or via psql using your LAKEBASE_URL.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS support;

DROP TABLE IF EXISTS support.ticket_messages;
DROP TABLE IF EXISTS support.tickets;

CREATE TABLE support.tickets (
    ticket_id     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title         VARCHAR(255) NOT NULL,
    status        VARCHAR(32) NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    priority      VARCHAR(32) NOT NULL DEFAULT 'medium'
                    CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    category      VARCHAR(32),
    created_by    VARCHAR(64) NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT now(),
    updated_at    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE support.ticket_messages (
    message_id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id     INT NOT NULL REFERENCES support.tickets(ticket_id) ON DELETE CASCADE,
    message       VARCHAR(1000) NOT NULL,
    author        VARCHAR(64) NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_ticket_messages_ticket_id ON support.ticket_messages(ticket_id);
CREATE INDEX idx_tickets_status ON support.tickets(status);

-- Optional, only needed if you want to try Lakebase Change Data Feed later:
-- ALTER TABLE support.tickets REPLICA IDENTITY FULL;
-- ALTER TABLE support.ticket_messages REPLICA IDENTITY FULL;
