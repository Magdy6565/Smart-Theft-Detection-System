# my_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_video, name='upload_video'),
    path('detect-theft/', views.detect_theft, name='detect_theft'),    
    path('', views.home, name='home'), 

]
