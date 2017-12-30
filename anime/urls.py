from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^$', views.index, name='anime_index'),
    re_path(r'^crunchyroll/$', views.crunchyroll, name='anime_crunchyroll'),
    re_path(r'^(.*?)/$', views.watch, name='anime_watch'),
]