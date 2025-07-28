# advisor/urls.py - セッション一覧機能追加版

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
    path('api/analyze/', views.analyze_question, name='analyze_question'),
    path('api/question/', views.analyze_question, name='question_api'),
    path('api/subsidies/', views.subsidy_list, name='subsidy_list'),
    
    # 会話履歴
    path('api/history/<str:session_id>/', views.conversation_history, name='conversation_history'),
    path('debug/sessions/', views.session_list, name='session_list'),
    # デバッグ機能
    path('debug/history/', views.debug_conversation_history, name='debug_history'),
    path('debug/sessions/', views.session_list, name='session_list'),  # 新規追加
    path('api/debug-history/', views.debug_conversation_history, name='debug_history_api'),
    
    # セッション管理API（オプション）
    # path('api/delete-session/', views.delete_session, name='delete_session'),
    # path('api/clear-all-sessions/', views.clear_all_sessions, name='clear_all_sessions'),
    
    # その他のページ
    path('statistics/', views.subsidy_statistics, name='statistics'),
    path('predictions/', views.prediction_dashboard, name='prediction_dashboard'),
    path('alerts/', views.user_alerts, name='user_alerts'),
    path('trends/', views.trend_analysis, name='trend_analysis'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # 互換性維持用
    path('chat-view/', views.chat_interface, name='chat_view'),
    path('analyze/', views.analyze_question, name='analyze'),
]