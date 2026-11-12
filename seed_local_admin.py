import os,json,secrets
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','myproject.settings')
import django
django.setup()
from django.contrib.auth.models import User
p=Path('.local-login.json')
if not p.exists():
 data={'username':'labadmin','password':secrets.token_urlsafe(24)};p.write_text(json.dumps(data));p.chmod(0o600)
else:data=json.loads(p.read_text())
u,created=User.objects.get_or_create(username=data['username']);u.is_staff=True;u.is_superuser=True;u.first_name='Demo learner';u.set_password(data['password']);u.save()
print('Local lab administrator ready.')
