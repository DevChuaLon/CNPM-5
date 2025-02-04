import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_booking.settings')
django.setup()

User = get_user_model()

def create_superuser():
    username = 'admin'
    email = 'hung82390@gmail.com'
    password = '1'
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print('Superuser created successfully.')
    else:
        print('Superuser already exists.')

if __name__ == '__main__':
    create_superuser()