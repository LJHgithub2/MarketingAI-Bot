from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_info', views.generate_promotion, name='generate_promotion'),
]