import os

from django.contrib.auth import get_user_model


username = os.environ["DJANGO_BOOTSTRAP_ADMIN_USERNAME"].strip()
password = os.environ["DJANGO_BOOTSTRAP_ADMIN_PASSWORD"]
User = get_user_model()

user, _ = User.objects.get_or_create(username=username)
user.set_password(password)
user.is_superuser = True
user.is_staff = True
user.is_active = True
user.role = "ADMIN"
user.save()
print(f"Bootstrapped admin account: {username}")
