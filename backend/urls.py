from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.urls import re_path
from django.views.static import serve
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from orders.views import SendPaymentRequest, DeleteNotification, ApproveNotificationAPIView, NotificationCountAPIView
from users.views import GoogleSocialAuthView, ContactUsAPIView

schema_view = get_schema_view(
    openapi.Info(title="TSS API", default_version="v1"),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(r"^doc(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path( "doc/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path('admin/', admin.site.urls),
    path("user/", include("users.urls")),
    path("product/", include("product.urls")),
    path("order/", include("orders.urls")),
    path("stock/", include("stocks.urls")),
    path('notifications/', SendPaymentRequest.as_view(), name='notification-list-create'),
    path('approve-order-payment-notification/<int:id>/', ApproveNotificationAPIView.as_view(), name='notification-list-create'),
    path('notifications/<int:notification_id>/', DeleteNotification.as_view(), name='delete-notification'),
    path('notifications/count/', NotificationCountAPIView.as_view(), name='notification-count'),
    path('login-with-google/', GoogleSocialAuthView.as_view(), name="login-with-google"),
    path('contact-us/', ContactUsAPIView.as_view(), name="contact-us"),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)