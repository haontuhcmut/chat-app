#!/bin/sh
set -e  # exit on error

echo "Running migrations..."
alembic upgrade head
echo "Migrations completed successfully"

echo "Starting Celery worker..."
celery -A app.celery_task.c_app worker -l info &
#CELERY_PID=$!

echo "Starting FastAPI application..."
if [ "$ENVIRONMENT" = "development" ]; then
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
else
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
fi

## Wait for Celery worker to exit
#wait $CELERY_PID
