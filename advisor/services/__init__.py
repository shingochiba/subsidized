from .enhanced_chat_service import EnhancedChatService
from .subsidy_prediction_service import SubsidyPredictionService

# 既存のサービスとの互換性を保持
try:
    from .ai_advisor import AIAdvisorService
except ImportError:
    # フォールバック
    AIAdvisorService = EnhancedChatService

# ConversationManagerクラスを追加（後方互換性のため）
class ConversationManager:
    """会話履歴管理 - 後方互換性のためのラッパークラス"""
    
    @staticmethod
    def save_conversation(session_id, user, message_type, content):
        """会話の保存"""
        from ..models import ConversationHistory
        from django.utils import timezone
        
        ConversationHistory.objects.create(
            session_id=session_id,
            user=user,
            message_type=message_type,
            content=content,
            timestamp=timezone.now()
        )
    
    @staticmethod
    def get_conversation_history(session_id, limit=10):
        """会話履歴の取得"""
        from ..models import ConversationHistory
        
        return ConversationHistory.objects.filter(
            session_id=session_id
        ).order_by('-timestamp')[:limit]

__all__ = [
    'EnhancedChatService',
    'SubsidyPredictionService', 
    'AIAdvisorService',
    'ConversationManager'  # 後方互換性のため追加
]