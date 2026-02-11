from django.urls import path, re_path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from main.views import SearchFilesView, FileDetailCreateAPIView, FileDetailUpdateAPIView, FiltersView

swagger_info = openapi.Info(
    title="Offentligabeslut API",
    default_version='v1',
    description=(
        "API for searching Swedish municipal documents (protokoll).\n\n"
        "## Authentication\n"
        "Access is open to all IP addresses. Registered IP ranges may have higher rate limits "
        "and access to additional fields (e.g. full document text).\n\n"
        "## Rate Limiting\n"
        "Requests are rate-limited per minute. If you exceed the limit, "
        "you will receive a `429 Too Many Requests` response.\n\n"
        "## Search Syntax\n"
        "- **Basic search**: `budget 2024` — finds documents containing all words\n"
        "- **Exact phrase**: `\"kommunstyrelsen protokoll\"` — matches the exact phrase\n"
        "- **Exclude words**: `budget -skola` — excludes documents containing 'skola'\n"
        "- Combine all of the above in one query"
    ),
    contact=openapi.Contact(email="info@offentligabeslut.se"),
)

schema_view = get_schema_view(
    swagger_info,
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        path('files/', SearchFilesView.as_view()),
        path('filters/', FiltersView.as_view()),
    ],
)

urlpatterns = [
    path('login/', TokenObtainPairView.as_view()),
    path('files/', SearchFilesView.as_view()),
    path('filters/', FiltersView.as_view()),
    # path('files/create/', FileDetailCreateAPIView.as_view()),
    # path('files/update/<int:pk>/', FileDetailUpdateAPIView.as_view()),
    path('admin/', admin.site.urls),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
