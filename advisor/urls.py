from django.urls import path
from . import views

app_name = 'advisor'

urlpatterns = [
    # 既存のURL
    path('', views.ChatView.as_view(), name='chat'),
    path('api/question/', views.QuestionAPIView.as_view(), name='question_api'),
    path('api/subsidies/', views.subsidy_list, name='subsidy_list'),
    path('api/history/<str:session_id>/', views.conversation_history, name='conversation_history'),
    
    # 🆕 採択率分析機能のURL
    path('analysis/', views.AdoptionAnalysisView.as_view(), name='adoption_analysis'),
    path('analysis/<int:subsidy_id>/', views.AdoptionAnalysisView.as_view(), name='adoption_analysis_detail'),
    
    # 🆕 採択率分析API
    path('api/adoption-statistics/', views.adoption_statistics_api, name='adoption_statistics'),
    path('api/adoption-statistics/<int:subsidy_id>/', views.adoption_statistics_api, name='adoption_statistics_detail'),
    path('api/adoption-tips/<int:subsidy_id>/', views.adoption_tips_api, name='adoption_tips'),
    path('api/adoption-probability/', views.AdoptionProbabilityView.as_view(), name='adoption_probability'),
    
    # 🆕 申請履歴管理
    path('api/user-application-history/', views.user_application_history, name='user_application_history'),
    path('api/application-history/', views.ApplicationHistoryView.as_view(), name='application_history'),
    
    # 🆕 業種別比較
    path('api/industry-comparison/', views.industry_comparison, name='industry_comparison'),
]