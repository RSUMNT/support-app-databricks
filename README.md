# Support Ticket App — Lakebase + Databricks Apps

A Databricks App (Streamlit) backed by **Lakebase** (managed Postgres),
using a single native-password secret for connection — no OAuth token
juggling.

## Files

- `app.py` — Streamlit UI: ticket list, filters, stats, create ticket,
  view/add messages, update status, delete with confirmation
- `lakebase.py` — Lakebase connection helper. Fetches a single
  `LAKEBASE_URL` from a Databricks secret scope and exposes
  `run_query` / `run_write` / `run_write_returning`
- `setup_secrets.py` — one-time script to store your Lakebase connection
  URL as a Databricks secret
- `app.yaml` — Databricks App config (command + env vars pointing at the
  secret scope/key)
- `.env.example` — local dev template
- `sql/01_schema.sql` — `tickets` + `ticket_messages` tables
- `sql/02_seed_data.sql` — 3 tickets, 2+ messages each, 2+ statuses

---

## Step 1 — Create a Lakebase instance and a native-password role

1. In your Databricks workspace, go to **Catalog** → **Lakebase** tab
   (or search "Lakebase" in the workspace search bar). In some workspace
   versions it's under **Compute** → **Lakebase** instead.
2. Click **Create Lakebase instance** (or **Create database instance**).
   - Name it e.g. `support-app-db`.
   - Choose **Autoscaling** for capacity (better fit than Provisioned for
     a small app like this — see earlier discussion).
   - Click **Create**, wait for status **Available**.
3. Open the instance → go to the **Roles & Databases** tab (may be called
   **Permissions** or **Roles**).
4. **Enable native (password) authentication** if it isn't already on —
   look for a toggle like **Native passwords** / **Password authentication**.
   This is the key step that avoids the OAuth-token problems from before.
5. **Create a new role**:
   - Click **Add role** / **Create role**.
   - Choose **Password** as the auth method (not OAuth).
   - Name it e.g. `support_app` and let Databricks generate a password
     (or set your own).
6. **Copy the connection URL** shown for the role — it looks like:
   ```
   postgresql://support_app:<password>@<host>.database.cloud.databricks.com:5432/databricks_postgres?sslmode=require
   ```
   Keep this handy for Step 3. Don't paste it anywhere except the secret
   setup below.

## Step 2 — Create the schema and load sample data

1. Open a SQL connection to your Lakebase instance — either the built-in
   SQL editor pointed at the Lakebase instance, or `psql`:
   ```bash
   psql "postgresql://support_app:<password>@<host>:5432/databricks_postgres?sslmode=require"
   ```
2. Run `sql/01_schema.sql`, then `sql/02_seed_data.sql` (paste contents
   into the SQL editor, or `psql ... -f sql/01_schema.sql`).
3. Verify:
   ```sql
   SELECT * FROM support.tickets;
   SELECT * FROM support.ticket_messages ORDER BY ticket_id;
   ```
   You should see 3 tickets and 6 messages. Screenshot this for your
   submission.

## Step 3 — Store the Lakebase URL as a Databricks secret

Do this once from a **Databricks notebook** (no local CLI needed):

1. Create a new notebook, attach it to any running cluster/compute.
2. Upload/place `setup_secrets.py` somewhere in your workspace (e.g. the
   same Git folder from Step 5 below, once created), then in a notebook
   cell run:
   ```
   %sh python setup_secrets.py
   ```
   Or open a terminal from the notebook (**Run** → **Open terminal**) and
   run `python setup_secrets.py` there.
3. It prompts (via `getpass`, nothing echoed or logged) for your Lakebase
   connection URL from Step 1.6. Paste it in.
4. This creates a secret scope called `database` with a key
   `lakebase-url` holding your connection string.

## Step 4 — Push this project to GitHub

If you haven't already:
```bash
cd lakebase-support-app
git init
git add .
git commit -m "Support ticket app backed by Lakebase"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```
(Adjust if you already have a repo set up.)

**Double check `.gitignore` is excluding `.env`** so you never commit a
real connection string.

## Step 5 — Create a Git folder in Databricks

1. In the Databricks workspace sidebar: **Workspace** → **Create** →
   **Git folder** (older UI: **Repos** → **Add Repo**).
2. Paste your GitHub repo URL.
3. Name the folder, click **Create Git folder**. This clones the repo
   directly into your workspace.

## Step 6 — Create the Databricks App

1. Sidebar → **Compute** → **Apps** (or search "Apps").
2. Click **Create app** → choose **Custom** (or "From scratch").
3. Name it, e.g. `support-ticket-app`.
4. When asked for the source, choose **Git** and point it at the Git
   folder from Step 5 (or paste the repo URL directly if that's the
   option you're given — see below).
5. Databricks reads `app.yaml` from the folder automatically to configure
   the run command and env vars.

## Step 7 — Deploy

1. Click **Deploy** (or **Create and deploy**).
2. Wait for status **Running** (installs `requirements.txt` the first
   time — can take a couple minutes).
3. Whenever you change code: push to GitHub, then in the Git folder click
   **Pull** (to sync the latest commit into the workspace), then go back
   to the Apps page and click **Deploy** again to redeploy with the new
   code.

## Step 8 — Test

Open the app URL and confirm:
- The 3 seeded tickets load
- Create a new ticket → appears in the list
- Open a ticket → add a message → appears
- Change status → **Save status** → updates
- **Refresh the browser tab** → everything persists (proves it's reading
  Lakebase, not local state)

Screenshot this for your submission.

## Troubleshooting

- **"secret does not exist" / permission error fetching the secret** —
  confirm you ran `setup_secrets.py` successfully (Step 3) and that the
  app's service principal has access to the `database` secret scope.
  Check the scope's ACLs:
  ```python
  from databricks.sdk import WorkspaceClient
  w = WorkspaceClient()
  for acl in w.secrets.list_acls(scope="database"):
      print(acl)
  ```
  If the app's identity isn't listed, grant it:
  ```python
  from databricks.sdk.service.workspace import AclPermission
  w.secrets.put_acl(scope="database", principal="<app-service-principal>", permission=AclPermission.READ)
  ```
- **Connection refused / timeout** — double check the host/port in the
  Lakebase URL are exactly as shown on the instance's connection page.
- **relation "support.tickets" does not exist** — Step 2 wasn't run
  against this instance, or you're pointed at the wrong database name.

## Security note

No passwords or connection strings are stored in this repository.
`lakebase.py` fetches the connection URL at runtime from a Databricks
secret scope, set up once via `setup_secrets.py` using `getpass` (never
written to disk or shell history).
