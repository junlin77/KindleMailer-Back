from django.urls import path
from . import views
from .views import KindleEmailAPI

urlpatterns = [
    path('api/search/', views.search_api, name='search_api'),
    path('api/send_to_kindle/', views.send_to_kindle_api, name='send_to_kindle_api'),
    path('api/login/', views.login_api, name='login_api'),
    path('api/get_kindle_email/', KindleEmailAPI.as_view(), name='get_kindle_email_api'),
    path('api/set_kindle_email/', KindleEmailAPI.as_view(), name='set_kindle_email_api'),
]