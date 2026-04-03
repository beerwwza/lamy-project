import os
import sys
import django
from pprint import pprint

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def run_test():
    c = Client()
    user = User.objects.first()
    if not user:
        print("No user found")
        return

    c.force_login(user)
    try:
        response = c.get('/equipment/123D52/')
        if response.status_code == 500:
            print("HTTP 500 Error!")
        elif response.status_code == 302:
            print("Redirect to: ", response.url)
        elif response.status_code == 200:
            print("SUCCESS 200")
        else:
            print(f"Status Code: {response.status_code}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_test()
