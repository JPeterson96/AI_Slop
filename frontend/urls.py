from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('submit/', views.submit_text, name='submit_text'),
    path("ask/", views.ai_response, name="ai_response"),
    path('workflow-status/', views.workflow_status_stream, name='workflow_status'),
    path('trace/', views.trace_dashboard, name='trace_dashboard'),
    path('trace/api/', views.trace_api, name='trace_api'),
]
