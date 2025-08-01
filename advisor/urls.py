# advisor/urls.py - 最終版（完全に動作する）

from django.urls import path
from . import views

app_name = 'advisor'

urlpatterns = [
    # 基本ページ
    path('', views.index, name='index'),
    path('chat/', views.chat_interface, name='chat_interface'),
    path('enhanced-chat/', views.enhanced_chat_interface, name='enhanced_chat_interface'),
    
    # APIエンドポイント
    path('api/enhanced-chat/', views.enhanced_chat_api, name='enhanced_chat_api'),
    path('api/context-aware-chat/', views.ContextAwareChatAPIView.as_view(), name='context_aware_chat_api'),
    path('api/analyze/', views.analyze_question, name='analyze_question'),
    path('api/question/', views.analyze_question, name='question_api'),
    path('api/subsidies/', views.subsidy_list, name='subsidy_list'),
    
    # 会話履歴
    path('api/history/<str:session_id>/', views.conversation_history, name='conversation_history'),
    
    # 管理・統計ページ
    path('statistics/', views.subsidy_statistics, name='statistics'),
    path('predictions/', views.prediction_dashboard, name='prediction_dashboard'),
    path('alerts/', views.user_alerts, name='user_alerts'),
    path('trends/', views.trend_analysis, name='trend_analysis'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # 追加ページ
    path('prediction-calendar/', views.prediction_calendar, name='prediction_calendar'),
    path('statistics-dashboard/', views.statistics_dashboard, name='statistics_dashboard'),
    path('session-list/', views.session_list, name='session_list'),
    path('debug-history/', views.debug_history, name='debug_history'),
    
    # 管理機能
    path('export-session/<str:session_id>/', views.export_session, name='export_session'),
    path('delete-session/<str:session_id>/', views.delete_session, name='delete_session'),
    
    # API（予測・カレンダー）
    path('api/calendar-events/', views.get_calendar_events_api, name='calendar_events_api'),
    path('api/prediction-detail/', views.prediction_detail_api, name='prediction_detail_api'),
    
    # 互換性維持用
    path('chat-view/', views.chat_interface, name='chat_view'),
    path('analyze/', views.analyze_question, name='analyze'),
]