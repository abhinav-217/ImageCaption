from django.contrib import admin
from django.urls import path
from mainApp import views
urlpatterns = [
    path("",views.index,name='mainApp'),
    path("generate",views.generate,name='mainAppAbout')
]
