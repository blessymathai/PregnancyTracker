from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('admin/', admin.site.urls),

    # Guest Module
    path('', include('Guest.urls')),

    # User Module
    path('User/', include('User.urls')),

    # Doctor Module
    path('Doctor/', include('Doctor.urls')),

    # Administrator Module
    path('Administrator/', include('Administrator.urls')),
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )