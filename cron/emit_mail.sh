#!/bin/sh

PROJECT_ROOT=/srv/www/wootmatch

cd $PROJECT_ROOT
python manage.py send_mail >> $PROJECT_ROOT/logs/cron_mailer.log 2>&1

