web: sh -c "python manage.py migrate && gunicorn --bind 0.0.0.0:$PORT myshop.wsgi:application --log-file -"
