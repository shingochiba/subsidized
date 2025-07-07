from .adoption_analysis import AdoptionAnalysisService

# ConversationManagerを既存サービスから取得
from .ai_advisor import ConversationManager

# LLM強化版AIサービスを使用
from .llm_enhanced_advisor import LLMEnhancedAdvisorService

# メインサービスとして設定
AIAdvisorService = LLMEnhancedAdvisorService

__all__ = [
    'AIAdvisorService',
    'ConversationManager', 
    'AdoptionAnalysisService',
]

# デバッグ用
print(' LLM Enhanced AI Advisor Service is now active!')
print(f'AIAdvisorService = {AIAdvisorService}')
