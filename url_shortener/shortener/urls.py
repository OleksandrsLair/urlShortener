from django.urls import path
from . import views

urlpatterns = [
    path("api/shorten", views.shorten, name="shorten"),
    path("api/resolve/<str:code>", views.resolve, name="resolve"),
    path("r/<str:code>", views.redirect_view, name="redirect"),
    path("stats/<str:code>", views.stats, name="stats"),
]
