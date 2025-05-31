from django.urls import path
from .views import UserRegistrationView, UserLoginView, UserListView, PasswordChangeView, PasswordResetRequestView, PasswordResetConfirmView, UserDeleteView, UserProfileView, GoogleSocialAuthView

urlpatterns = [
    path('', UserListView.as_view(), name='user_list'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('delete/<int:pk>/', UserDeleteView.as_view(), name='user_delete'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]