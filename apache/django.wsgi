import os
import os
import sys
sys.path.append('/srv/www')
sys.path.append('/srv/www/wootmatch')

sys.path.append(os.path.abspath(os.path.join(__file__, '../../..')))
sys.path.append(os.path.abspath(os.path.join(__file__, '../..')))

os.environ['DJANGO_SETTINGS_MODULE'] = 'wootmatch.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

