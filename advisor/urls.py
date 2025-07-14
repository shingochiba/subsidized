# advisor/urls.py - 採択率分析機能完成版

from django.urls import path
from . import views
from .api import enhanced_chat_api

app_name = 'advisor'

urlpatterns = [
    # メインページ
    path('', views.ChatView.as_view(), name='chat'),
    
    # チャット機能API
    path('api/question/', views.QuestionAPIView.as_view(), name='question_api'),
    path('api/subsidies/', views.subsidy_list, name='subsidy_list'),
    path('api/history/<str:session_id>/', views.conversation_history, name='conversation_history'),
    path('api/chat-service-status/', views.chat_service_status, name='chat_service_status'),
    
    # 🆕 強化された採択率分析機能
    path('analysis/', views.AdoptionAnalysisView.as_view(), name='adoption_analysis'),
    path('analysis/<int:subsidy_id>/', views.AdoptionAnalysisView.as_view(), name='adoption_analysis_detail'),
    
    # 🆕 採択率分析API（完全版）
    path('api/adoption-statistics/', views.adoption_statistics_api, name='adoption_statistics'),
    path('api/adoption-statistics/<int:subsidy_id>/', views.adoption_statistics_api, name='adoption_statistics_detail'),
    path('api/adoption-tips/<int:subsidy_id>/', views.adoption_tips_api, name='adoption_tips'),
    path('api/adoption-probability/', views.AdoptionProbabilityView.as_view(), name='adoption_probability'),
    path('api/industry-comparison/', views.industry_comparison, name='industry_comparison'),
    
    # 🆕 申請履歴管理
    path('history/', views.ApplicationHistoryView.as_view(), name='application_history'),
    path('api/user-application-history/', views.user_application_history, name='user_application_history'),
    
    # 既存の補助金予測機能（修正版）
    path('api/prediction-calendar/', views.prediction_calendar_api, name='prediction_calendar'),
    path('api/upcoming-subsidies/', views.upcoming_subsidies_api, name='upcoming_subsidies'),
    path('api/subsidy-trend/<int:subsidy_id>/', views.subsidy_trend_api, name='subsidy_trend'),
    path('api/generate-predictions/', views.GeneratePredictionsView.as_view(), name='generate_predictions'),
    path('api/prediction-summary/', views.prediction_summary_api, name='prediction_summary'),
    
    # 🆕 デバッグ・テスト用エンドポイント
    path('api/test-adoption-data/', views.test_adoption_data, name='test_adoption_data'),
    path('api/create-sample-adoption-data/', views.create_sample_adoption_data, name='create_sample_adoption_data'),
    path('api/system-status/', views.system_status, name='system_status'),

    path('', views.index, name='index'),
    path('chat/', views.chat_interface, name='chat_interface'),
    path('api/analyze/', views.analyze_question, name='analyze_question'),
    
    # 新機能: 強化されたチャット機能
    path('enhanced-chat/', views.enhanced_chat_interface, name='enhanced_chat_interface'),
    path('api/enhanced-chat/', enhanced_chat_api.enhanced_chat_conversation, name='enhanced_chat_api'),
    
    # 新機能: 補助金予測機能
    path('predictions/', views.prediction_dashboard, name='prediction_dashboard'),
    path('api/subsidy-predictions/', enhanced_chat_api.subsidy_predictions, name='subsidy_predictions_api'),
    path('api/prediction-calendar/', enhanced_chat_api.prediction_calendar, name='prediction_calendar_api'),
    
    # 管理機能
    path('alerts/', views.user_alerts, name='user_alerts'),
    path('trends/', views.trend_analysis, name='trend_analysis'),
]