from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),     # админка
    path('accounts/', include('allauth.urls')),
    path('webhook/', include('shop.webhook_urls')),
    path('', include('shop.urls')),      # все URL из приложения shop
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Чтобы отображались картинки из ImageField
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
