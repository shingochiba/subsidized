# advisor/urls.py - 完全互換版
# 既存のURL構造を保持しつつ、新機能も追加

from django.urls import path
from . import views

# 修正：enhanced_chat_apiのインポートを条件付きに
try:
    from .api import enhanced_chat_api
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    print("Warning: Enhanced chat API not available")

app_name = 'advisor'

urlpatterns = [
    # 既存のURL構造を完全に保持
    path('', views.index, name='index'),  # 新しいメインページ
    path('chat/', views.chat_interface, name='chat_interface'),  # 基本チャット
    
    # 既存のAPIエンドポイント（後方互換性）
    path('api/analyze/', views.analyze_question, name='analyze_question'),
    path('api/question/', views.analyze_question, name='question_api'),  # 既存のAPIへのエイリアス
    path('api/subsidies/', views.subsidy_list, name='subsidy_list'),
    
    # 会話履歴
    path('api/history/<str:session_id>/', views.conversation_history, name='conversation_history'),
    
    # 統計・分析ページ
    path('statistics/', views.subsidy_statistics, name='statistics'),
    
    # 管理機能
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]

# 新機能（API利用可能な場合）
if API_AVAILABLE:
    urlpatterns.extend([
        # 強化されたチャット機能
        path('enhanced-chat/', views.enhanced_chat_interface, name='enhanced_chat_interface'),
        path('api/enhanced-chat/', enhanced_chat_api.enhanced_chat_conversation, name='enhanced_chat_api'),
        
        # 補助金予測機能
        path('predictions/', views.prediction_dashboard, name='prediction_dashboard'),
        path('api/subsidy-predictions/', enhanced_chat_api.subsidy_predictions, name='subsidy_predictions_api'),
        path('api/prediction-calendar/', enhanced_chat_api.prediction_calendar, name='prediction_calendar_api'),
        
        # 追加API
        path('api/conversation-history/', enhanced_chat_api.conversation_history, name='conversation_history'),
        path('api/mark-alert-read/', enhanced_chat_api.mark_alert_read, name='mark_alert_read'),
        path('api/status/', enhanced_chat_api.api_status, name='api_status'),
        
        # ユーザー機能
        path('alerts/', views.user_alerts, name='user_alerts'),
        path('trends/', views.trend_analysis, name='trend_analysis'),
    ])
else:
    # フォールバック用の基本ページ（API機能なし）
    urlpatterns.extend([
        path('enhanced-chat/', views.chat_interface, name='enhanced_chat_interface'),
        path('predictions/', views.prediction_dashboard, name='prediction_dashboard'),
        path('alerts/', views.user_alerts, name='user_alerts'),
        path('trends/', views.trend_analysis, name='trend_analysis'),
    ])

# 既存のURLパターンとの完全互換性
# 以前のURL構造からのエイリアス
urlpatterns.extend([
    # 古いパターンの互換性維持
    path('chat-view/', views.chat_interface, name='chat_view'),
    path('analyze/', views.analyze_question, name='analyze'),
])