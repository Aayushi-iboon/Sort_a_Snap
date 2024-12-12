#!/bin/sh
#chown -R root:root static/
#chmod -R 755 static/
#chown -R root:root media/
#chmod -R 755 media/
python manage.py collectstatic --noinput

python3 manage.py makemigrations imagesense
python3 manage.py makemigrations groups
python manage.py migrate
which gunicorn
gunicorn -b :8000 face.wsgi
