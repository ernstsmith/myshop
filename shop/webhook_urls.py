from django.urls import path
from . import webhook_views

urlpatterns = [
    path('', webhook_views.telegram_webhook, name='telegram_webhook'),
]
