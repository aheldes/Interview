from django.urls import path

from . import views

app_name = 'main'
urlpatterns = [
    path('', views.home, name="home"),
    path('search/', views.search_page, name="search"),
    path('substance/<id>/', views.substance, name="substance"),
    path('pdf/<id>/', views.pdf_result, name="pdf"),
    path('medicine/<id>', views.medicine_result, name="medicine"),
]