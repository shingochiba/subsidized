from django.urls import path
from . import views

app_name = 'advisor'

urlpatterns = [
    path('', views.ChatView.as_view(), name='chat'),
    path('api/question/', views.QuestionAPIView.as_view(), name='question_api'),
    path('api/subsidies/', views.subsidy_list, name='subsidy_list'),
    path('api/history/<str:session_id>/', views.conversation_history, name='conversation_history'),
]