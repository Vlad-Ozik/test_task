#!/bin/sh
set -e

# Default environment variables
PGHOST="${POSTGRES_HOST:-localhost}"
PGUSER="${POSTGRES_USER:-postgres}"
PGDB="${POSTGRES_DB:-postgres}"

# Target Database and User from env
TARGET_DB="${CURRENCY_DB_NAME:-CURRENCY_TASK}"
TARGET_USER="${CURRENCY_DB_USER:-currency_user}"
TARGET_PASS="${CURRENCY_DB_PASSWORD:-currency_password}"

# Helper functions for escaping
escape_sql_literal() {
  echo "$1" | sed "s/'/''/g"
}

escape_sql_identifier() {
  echo "$1" | sed 's/"/""/g'
}

echo "Starting database initialization..."

# 2. Create User (Role) if not exists
echo "Ensuring user '$TARGET_USER' exists..."
escaped_user_literal=$(escape_sql_literal "$TARGET_USER")
escaped_user_identifier=$(escape_sql_identifier "$TARGET_USER")
escaped_pass_literal=$(escape_sql_literal "$TARGET_PASS")

role_exists=$(psql -U "$PGUSER" -d "$PGDB" -At -v ON_ERROR_STOP=1 \
  -c "SELECT 1 FROM pg_roles WHERE rolname = '${escaped_user_literal}' LIMIT 1;")

role_exists=$(echo "$role_exists" | tr -d '[:space:]')

if [ "$role_exists" != "1" ]; then
  echo "Creating user '$TARGET_USER'..."
  psql -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 \
    -c "CREATE USER \"${escaped_user_identifier}\" WITH PASSWORD '${escaped_pass_literal}';"
else
  # Optional: Update password if user exists
  echo "User '$TARGET_USER' already exists. Updating password..."
  psql -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 \
    -c "ALTER USER \"${escaped_user_identifier}\" WITH PASSWORD '${escaped_pass_literal}';"
fi

# 3. Create Database if not exists
echo "Ensuring database '$TARGET_DB' exists..."
escaped_db_literal=$(escape_sql_literal "$TARGET_DB")
escaped_db_identifier=$(escape_sql_identifier "$TARGET_DB")

db_exists=$(psql -U "$PGUSER" -d "$PGDB" -At -v ON_ERROR_STOP=1 \
  -c "SELECT 1 FROM pg_database WHERE datname = '${escaped_db_literal}' LIMIT 1;")

db_exists=$(echo "$db_exists" | tr -d '[:space:]')

if [ "$db_exists" != "1" ]; then
  echo "Creating database '$TARGET_DB'..."
  psql -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 \
    -c "CREATE DATABASE \"${escaped_db_identifier}\" OWNER \"${escaped_user_identifier}\";"
else
  echo "Database '$TARGET_DB' already exists."
fi

# 4. Grant Privileges
echo "Granting privileges..."

psql -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 \
  -c "GRANT ALL PRIVILEGES ON DATABASE \"${escaped_db_identifier}\" TO \"${escaped_user_identifier}\";"

echo "Initialization completed successfully."
