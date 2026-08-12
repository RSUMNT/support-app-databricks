-- ============================================================
-- Sample data — 3 tickets, 2+ messages each, 2+ statuses
-- ============================================================

INSERT INTO support.tickets (title, status, priority, category, created_by)
VALUES
    ('Cannot log into dashboard',  'open',        'high',   'access',  'raja.arram'),
    ('Export button not working',  'in_progress', 'medium', 'bug',     'jsmith'),
    ('Feature request: dark mode', 'resolved',    'low',    'feature', 'mlee');

INSERT INTO support.ticket_messages (ticket_id, message, author)
SELECT ticket_id, 'Still get 403 after clearing cache', 'raja.arram'
FROM support.tickets WHERE title = 'Cannot log into dashboard';

INSERT INTO support.ticket_messages (ticket_id, message, author)
SELECT ticket_id, 'Looking into SSO redirect config', 'support_agent_1'
FROM support.tickets WHERE title = 'Cannot log into dashboard';

INSERT INTO support.ticket_messages (ticket_id, message, author)
SELECT ticket_id, 'Happens on Chrome and Firefox', 'jsmith'
FROM support.tickets WHERE title = 'Export button not working';

INSERT INTO support.ticket_messages (ticket_id, message, author)
SELECT ticket_id, 'Repro''d on staging, job times out', 'support_agent_2'
FROM support.tickets WHERE title = 'Export button not working';

INSERT INTO support.ticket_messages (ticket_id, message, author)
SELECT ticket_id, 'Would love this for night shifts', 'mlee'
FROM support.tickets WHERE title = 'Feature request: dark mode';

INSERT INTO support.ticket_messages (ticket_id, message, author)
SELECT ticket_id, 'Shipped in v2.4, closing ticket', 'support_agent_1'
FROM support.tickets WHERE title = 'Feature request: dark mode';
