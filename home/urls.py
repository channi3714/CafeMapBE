from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map_view'),
    path('api/cafes/', views.cafe_data_api, name='cafe_data_api'),
]