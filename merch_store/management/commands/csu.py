from django.core.management import BaseCommand

from merch_store.models import User


class Command(BaseCommand):

    def handle(self, *args, **options):
        user = User.objects.create(
            email='admin@service.py',
            first_name='admin',
            last_name='service',
            is_staff=True,
            is_superuser=True
        )
        user.set_password('1')
        user.save()
        print('SuperUser setted up successfully')
