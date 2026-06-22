import os, django
os.environ["DJANGO_SETTINGS_MODULE"] = "learning.settings"
django.setup()

from django.db import connection
tables = connection.introspection.table_names()
print("django_cache exists:", 'django_cache' in tables)
print("All tables:", [t for t in tables if 'cache' in t.lower()])

# Try using the cache
try:
    from django.core.cache import cache
    cache.set('test_key', 'test_value', 30)
    val = cache.get('test_key')
    print("Cache test:", val)
except Exception as e:
    print("Cache error:", e)
