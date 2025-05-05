from django.urls import path
from app_sentiment import views

# declare a  namespace for this APP
# the name of namespace is  'app_top_keyword'
# We will use the namespace in the future integrated website.
app_name = 'app_sentiment'

urlpatterns = [
    path('', views.home, name='home'),
    path('api_get_sentiment/', views.api_get_sentiment, name='api_sentiment'),
]