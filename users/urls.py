from django.urls import path
from .views import SignUpView, CodeVerifyView, GetNewCodeView, UserChangeInfoView,\
    UserPhotoStatusView, LoginView, LogoutView, LoginRefresh, ForgotPasswordView, ResetPasswordView

urlpatterns = [
    path('sign-up/', SignUpView.as_view()),
    path('code-verify/', CodeVerifyView.as_view()),
    path('get-new-code/', GetNewCodeView.as_view()),
    path('change-info/', UserChangeInfoView.as_view()),
    path('change-photo/', UserPhotoStatusView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('login-refresh/', LoginRefresh.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
]






