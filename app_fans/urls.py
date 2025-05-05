from django.urls import path
from app_fans import views

app_name = 'app_fans'


urlpatterns = [
    # top (popular) persons
    path('', views.home, name='home'),
]