from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('submit/', views.submit_text, name='submit_text'),
    path("ask/", views.ai_response, name="ai_response"),
]
