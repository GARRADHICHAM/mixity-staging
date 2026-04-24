web: gunicorn mixity.wsgi
worker: newrelic-admin run-program python manage.py rqworker default
release: python manage.py makemigrations --check --dry-run && python manage.py migrate && playwright install chromium