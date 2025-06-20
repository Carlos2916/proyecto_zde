from django.contrib import admin
from django.urls import path, include
import os


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
]

from django.conf import settings
from django.conf.urls.static import static


urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)