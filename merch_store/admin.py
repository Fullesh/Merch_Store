from django.contrib import admin

from merch_store.models import User, Merch, Transaction

# Register your models here.

admin.site.register(User)
admin.site.register(Merch)
admin.site.register(Transaction)
