"""Start Django dev server on port 8001 for testing."""
import os, sys

# Load .env
with open('.env', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

os.environ['DJANGO_DEBUG'] = 'True'
os.environ['DJANGO_SETTINGS_MODULE'] = 'learning.settings'

from django.core.management import execute_from_command_line
sys.argv = ['manage.py', 'runserver', '8001', '--noreload']
execute_from_command_line(sys.argv)
