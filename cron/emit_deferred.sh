#!/bin/sh

PROJECT_ROOT=/srv/www/wootmatch

cd $PROJECT_ROOT
python manage.py retry_deferred >> $PROJECT_ROOT/logs/deferred_mail.log 2>&1

