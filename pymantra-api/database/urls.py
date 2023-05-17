from django.urls import path

from . import views

urlpatterns = [
    path("get-subgraph", views.get_subgraph),
    path("get-reaction-subgraph", views.get_reaction_subgraph),
    path("as-networkx", views.as_networkx),
]
