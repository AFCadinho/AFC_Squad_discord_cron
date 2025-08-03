#!/bin/bash

# Check if message is provided
if [ -z "$1" ]; then
  echo "❌ Please provide a migration message."
  echo "Usage: ./migrate.sh \"add is_active column\""
  exit 1
fi

# Step 1: Generate migration
echo "📦 Generating migration: $1"
poetry run alembic revision --autogenerate -m "$1"

# Step 2: Apply migration
echo "🚀 Applying migration..."
poetry run alembic upgrade head

echo "✅ Migration complete!"
