# usuarios/urls.py
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

app_name = "usuarios"

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(next_page="usuarios:login"),
        name="logout",
    ),
]