#!/bin/sh
chown -R root:root static/
chmod -R 755 static/
chown -R root:root media/
chmod -R 755 media/
python manage.py collectstatic --noinput

python3 manage.py makemigrations
# python3 manage.py makemigrations accounts
# python3 manage.py makemigrations studies
# python3 manage.py makemigrations core
# python3 manage.py makemigrations referrals
# python3 manage.py makemigrations bulkupload
# python3 manage.py makemigrations ringcentral
python manage.py migrate 
/usr/local/bin/gunicorn -b :8000 face.wsgi
