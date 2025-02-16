from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from merch_store.apps import MerchStoreConfig
from merch_store.views import AuthAPIView, InfoAPIView, SendCoinAPIView, BuyItemAPIView

app_name = MerchStoreConfig.name

urlpatterns = [
    path('info', InfoAPIView.as_view(), name='user_info'),
    path('auth', AuthAPIView.as_view(), name='auth'),
    path('auth/refresh', TokenRefreshView.as_view(), name='refresh'),
    path('sendCoin', SendCoinAPIView.as_view(), name='send_coin'),
    path('buy/<str:item_name>', BuyItemAPIView.as_view(), name='buy_item'),
]
