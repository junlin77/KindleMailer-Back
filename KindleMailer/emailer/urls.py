from django.urls import path
from . import views

urlpatterns = [
    path('api/search/', views.search_api, name='search_api'),
    path('api/send_to_kindle/', views.send_to_kindle_api, name='send_to_kindle_api'),
    path('api/login/', views.login_api, name='login_api'),
]