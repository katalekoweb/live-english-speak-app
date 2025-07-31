from . import views
from django.urls import path

app_name = "users"

urlpatterns = [
    path('register', views.register, name="register"),
    path('login', views.login_view, name="login"),
    path('logout', views.logout_view, name="logout")
]
