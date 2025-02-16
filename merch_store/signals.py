from django.db.models.signals import post_migrate
from django.dispatch import receiver
from merch_store.models import Merch

@receiver(post_migrate)
def create_initial_merch_data(sender, **kwargs):
    # Replace 'myapp' with your actual app name
    if sender.name == 'merch_store':
        # Check if the data already exists to avoid duplicates
        if not Merch.objects.exists():
            initial_data = [
                {'name': 't-shirt', 'price': 80},
                {'name': 'cup', 'price': 20},
                {'name': 'book', 'price': 50},
                {'name': 'pen', 'price': 10},
                {'name': 'powerbank', 'price': 200},
                {'name': 'hoody', 'price': 300},
                {'name': 'umbrella', 'price': 200},
                {'name': 'socks', 'price': 10},
                {'name': 'wallet', 'price': 50},
                {'name': 'pink-hoody', 'price': 500},
            ]
            for item in initial_data:
                Merch.objects.create(**item)