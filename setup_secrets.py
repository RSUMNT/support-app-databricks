"""
One-time script to store your Lakebase connection URL as a Databricks secret.

Run this from a Databricks notebook (%sh python setup_secrets.py) or a
notebook terminal. It uses getpass so the value is never echoed or written
to shell history.
"""

import base64
import getpass

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import AclPermission

SCOPE = "database"
KEY = "lakebase-url"

w = WorkspaceClient()

# Create the secret scope if it doesn't already exist.
existing_scopes = [s.name for s in w.secrets.list_scopes()]
if SCOPE not in existing_scopes:
    w.secrets.create_scope(scope=SCOPE)
    print(f"Created secret scope '{SCOPE}'")
else:
    print(f"Secret scope '{SCOPE}' already exists")

lakebase_url = getpass.getpass(
    "Paste your Lakebase connection URL "
    "(postgresql://role:password@host:5432/databricks_postgres?sslmode=require): "
)

# Store the raw string — the Databricks secrets API base64-encodes it
# internally, and lakebase.py's _lakebase_url() decodes it back on read.
w.secrets.put_secret(scope=SCOPE, key=KEY, string_value=lakebase_url)

print(f"Stored secret '{KEY}' in scope '{SCOPE}'. Done.")
