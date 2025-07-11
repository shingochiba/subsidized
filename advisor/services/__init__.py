# advisor/services/__init__.py

from .adoption_analysis import AdoptionAnalysisService

# ConversationManagerを既存サービスから取得
from .ai_advisor import ConversationManager

# 🆕 新しい文脈認識AIサービスを使用
from .context_aware_ai_advisor import ContextAwareAIAdvisorService

# メインサービスとして設定（採択率専用回答機能付き）
AIAdvisorService = ContextAwareAIAdvisorService

__all__ = [
    'AIAdvisorService',
    'ConversationManager', 
    'AdoptionAnalysisService',
]

# デバッグ用
print('🎯 Context-Aware AI Advisor Service is now active!')
print(f'🔄 Using: {AIAdvisorService.__name__}')
print(f'📍 Module: {AIAdvisorService.__module__}')
print(f'📊 Features: Adoption Rate Analysis, Intent Recognition, Specialized Responses')