import os
import sys

path = '/Users/olegtsss/Dev/new_admin_panel_sprint_1/venv/lib/python3.9/site-packages'  # noqa
if path not in sys.path:
    sys.path.append(path)

from django.core.wsgi import get_wsgi_application  # noqa

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
