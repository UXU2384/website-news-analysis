from django.urls import path
from app_pk import views

# declare a  namespace for this APP
# the name of namespace is  'app_top_keyword'
# We will use the namespace in the future integrated website.
app_name = 'app_pk'

urlpatterns = [
    path('', views.home, name='home'),
    path('api_get_pk/', views.api_get_pk, name='api_pk'),
]