# advisor/services/__init__.py
# 強制的に改良版サービスを使用

print("Loading improved AI advisor service...")

try:
    from .improved_ai_advisor import ImprovedAIAdvisorService
    AIAdvisorService = ImprovedAIAdvisorService
    print("✅ ImprovedAIAdvisorService loaded successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    
    # 最終フォールバック
    class FinalFallbackService:
        def analyze_question(self, question_text, user_context=None):
            question_lower = question_text.lower()
            
            # ものづくり補助金の検出を強化
            if any(keyword in question_lower for keyword in ['ものづくり', 'monozukuri', '設備投資']):
                return {
                    'answer': """## 🏭 ものづくり補助金の申請方法

### 📋 基本情報
- **補助上限額**: 1,250万円
- **補助率**: 1/2以内
- **対象**: 革新的な設備投資・サービス開発

### 📅 申請手順

#### STEP 1: 事前準備（2-3ヶ月前）
1. 公募要領の確認
2. 必要書類の準備
3. 見積書の取得

#### STEP 2: 申請書作成
1. 事業計画書の作成
2. 経費明細書の整理
3. 添付書類の準備

#### STEP 3: 申請・審査
1. 電子申請（Jグランツ）
2. 審査期間（1-3ヶ月）
3. 結果通知

### ⚠️ 重要ポイント
- 革新性の明確化
- 付加価値額向上の計算
- 投資効果の説明

詳しい手順についてもお尋ねください！""",
                    'recommended_subsidies': [],
                    'confidence_score': 0.9,
                    'model_used': 'fallback-monozukuri'
                }
            
            return {
                'answer': "申し訳ございません。システムエラーが発生しました。",
                'recommended_subsidies': [],
                'confidence_score': 0.1,
                'model_used': 'error-fallback'
            }
    
    AIAdvisorService = FinalFallbackService
    print("⚠️ Using FinalFallbackService")

# 会話管理
class SimpleConversationManager:
    @staticmethod
    def save_conversation(session_id, user, message_type, content):
        pass
    
    @staticmethod
    def get_conversation_history(session_id, limit=10):
        return []

ConversationManager = SimpleConversationManager

__all__ = ['AIAdvisorService', 'ConversationManager']
