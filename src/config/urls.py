from django.urls import path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView

from main.views import SearchFilesView, FileDetailCreateAPIView, FileDetailUpdateAPIView

urlpatterns = [
    path('login/', TokenObtainPairView.as_view()),
    path('files/', SearchFilesView.as_view()),
    path('files/create/', FileDetailCreateAPIView.as_view()),
    path('files/update/', FileDetailUpdateAPIView.as_view()),
    path('admin/', admin.site.urls),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
