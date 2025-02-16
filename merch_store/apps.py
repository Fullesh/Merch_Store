from django.apps import AppConfig


class MerchStoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'merch_store'

    def ready(self):
        import merch_store.signals
