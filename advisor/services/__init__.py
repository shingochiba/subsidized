# advisor/services/__init__.py

from .adoption_analysis import AdoptionAnalysisService

# 基本サービスをai_advisor.pyから取得
from .ai_advisor import ConversationManager

# AIAdvisorServiceは複数の候補から最適なものを選択
try:
    # 最優先: 戦略的AIアドバイザー
    from .strategic_ai_advisor import StrategicAIAdvisorService
    AIAdvisorService = StrategicAIAdvisorService
    service_type = "Strategic"
except ImportError:
    try:
        # 次候補: コンテキスト認識AIアドバイザー
        from .context_aware_ai_advisor import ContextAwareAIAdvisorService
        AIAdvisorService = ContextAwareAIAdvisorService
        service_type = "Context-Aware"
    except ImportError:
        try:
            # デフォルト: 基本AIアドバイザー
            from .ai_advisor import AIAdvisorService
            service_type = "Basic"
        except ImportError:
            # 最終的なフォールバック
            from .ai_advisor import DifyAIAdvisorService as AIAdvisorService
            service_type = "Dify"

__all__ = [
    'AIAdvisorService',
    'ConversationManager', 
    'AdoptionAnalysisService',
]

# デバッグ用情報表示
print(f'🎯 Active AI Advisor Service: {service_type} ({AIAdvisorService.__name__})')
print(f'📍 Module: {AIAdvisorService.__module__}')

# 利用可能な機能を表示
features = []
if hasattr(AIAdvisorService, 'analyze_question'):
    features.append('Question Analysis')
if 'strategic' in service_type.lower():
    features.append('Strategic Planning')
if 'context' in service_type.lower():
    features.append('Context Recognition')
if 'adoption' in str(AIAdvisorService.__module__):
    features.append('Adoption Rate Analysis')
    
print(f'📊 Available Features: {", ".join(features)}')