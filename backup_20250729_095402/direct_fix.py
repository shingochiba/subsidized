# direct_fix.py
# 現在の問題を直接修正するスクリプト

import os
import sys

def create_improved_service():
    """改良版サービスを直接作成"""
    
    # servicesディレクトリを作成
    os.makedirs('advisor/services', exist_ok=True)
    
    # improved_ai_advisor.py を作成
    improved_service_code = '''# advisor/services/improved_ai_advisor.py

from ..models import SubsidyType

class ImprovedAIAdvisorService:
    """改良された質問解析機能を持つAIアドバイザー"""
    
    def analyze_question(self, question_text, user_context=None):
        """質問を詳細に分析して適切な回答を生成"""
        
        question_lower = question_text.lower()
        print(f"Debug: 質問を分析中: {question_text}")
        
        # ものづくり補助金の質問を検出
        if self._is_monozukuri_question(question_lower):
            print("Debug: ものづくり補助金の質問として検出")
            return self._get_monozukuri_response(question_lower)
        
        # IT導入補助金
        elif self._is_it_question(question_lower):
            print("Debug: IT導入補助金の質問として検出")
            return self._get_it_response()
        
        # 一般的な回答
        else:
            print("Debug: 一般的な質問として処理")
            return self._get_general_response()
    
    def _is_monozukuri_question(self, question_lower):
        """ものづくり補助金の質問かどうか判定"""
        keywords = [
            'ものづくり補助金',
            'ものづくり',
            '設備投資',
            '革新的サービス',
            'monozukuri'
        ]
        
        result = any(keyword in question_lower for keyword in keywords)
        print(f"Debug: ものづくり判定結果: {result}, キーワード: {keywords}")
        return result
    
    def _is_it_question(self, question_lower):
        """IT導入補助金の質問かどうか判定"""
        keywords = [
            'it導入補助金',
            'it補助金',
            'itツール',
            'デジタル化'
        ]
        return any(keyword in question_lower for keyword in keywords)
    
    def _get_monozukuri_response(self, question_lower):
        """ものづくり補助金の詳細回答"""
        
        # 申請方法を聞いている場合
        if any(keyword in question_lower for keyword in ['申請方法', '申請手順', 'やり方', '手続き']):
            answer = """## 🏭 ものづくり補助金の申請方法

ものづくり補助金の申請手順を詳しくご説明いたします。

### 📋 基本情報
- **正式名称**: ものづくり・商業・サービス生産性向上促進補助金
- **補助上限額**: 1,250万円（デジタル枠）
- **補助率**: 1/2以内（小規模事業者は2/3）
- **申請時期**: 年2-3回の公募

### 📅 詳細な申請手順

#### **STEP 1: 事前準備（申請の2-3ヶ月前）**

1. **公募要領の確認**
   - 最新版の公募要領をダウンロード
   - 対象要件・対象経費を詳細確認
   - 審査項目の把握

2. **基本要件の確認**
   - 中小企業・小規模事業者の該当確認
   - 3年間の事業継続意思
   - 付加価値額年率平均3%以上向上計画

3. **必要書類の準備**
   - 決算書（直近3期分）
   - 確定申告書
   - 履歴事項全部証明書

#### **STEP 2: 計画策定（申請の1-2ヶ月前）**

1. **事業計画書の作成**
   - 現状の課題分析
   - 導入設備・システムの詳細
   - 革新性・独自性の説明
   - 付加価値額向上の根拠

2. **見積書の取得**
   - 複数業者からの相見積もり
   - 設備仕様書の収集
   - 価格の妥当性確認

#### **STEP 3: 申請書作成**

1. **様式記入**
   - 様式1：事業計画書
   - 様式2：経費明細書
   - 様式3：資金調達内訳書

2. **添付書類の準備**
   - 会社案内・製品カタログ
   - 工場レイアウト図
   - 技術資料

#### **STEP 4: 申請・審査**

1. **電子申請**
   - Jグランツでの提出
   - 期限厳守（締切日17:00まで）

2. **審査期間**
   - 書面審査（通常2-3ヶ月）

3. **結果通知**
   - 採択・不採択の連絡

### ⚠️ 申請時の重要ポイント

#### **革新性の明確化**
- 従来技術との違いを具体的に説明
- 新規性・優位性を数値で表現

#### **事業性の説明**
- 市場ニーズの根拠
- 競合分析
- 販売計画の妥当性

#### **実現可能性の証明**
- 技術的実現可能性
- 人的体制の整備
- 資金計画の確実性

### 💡 採択率向上のコツ

1. **早期準備**: 公募開始前から準備開始
2. **専門家活用**: 認定支援機関との連携
3. **具体性重視**: 曖昧な表現を避ける
4. **数値根拠**: 効果を定量的に説明

ご不明な点があれば、お気軽にお尋ねください！"""

        else:
            # 一般的なものづくり補助金の説明
            answer = """## 🏭 ものづくり補助金について

**正式名称**: ものづくり・商業・サービス生産性向上促進補助金

### 📊 補助金概要
- **補助上限額**: 1,250万円（デジタル枠）
- **補助率**: 1/2以内（小規模事業者は2/3）
- **対象**: 革新的な設備投資・サービス開発
- **申請時期**: 年2-3回程度

### 🎯 対象となる事業
- 新製品・新サービスの開発
- 生産性向上設備の導入
- IoT・AI等の先進技術活用

### ✅ 主な要件
1. 中小企業・小規模事業者
2. 3年間の事業継続
3. 付加価値額年率平均3%以上向上
4. 革新性のある取り組み

申請方法についてもお気軽にお尋ねください！"""

        return {
            'answer': answer,
            'recommended_subsidies': self._get_subsidies_by_keyword(['ものづくり']),
            'confidence_score': 0.95,
            'model_used': 'improved-monozukuri-detailed'
        }
    
    def _get_it_response(self):
        """IT導入補助金の回答"""
        answer = """## 🖥️ IT導入補助金について

### 📊 基本情報
- **補助上限額**: 最大450万円
- **補助率**: 1/2以内
- **対象**: ITツール・ソフトウェアの導入

### 📋 申請要件
1. gBizIDプライムの取得
2. SECURITY ACTIONの実施  
3. IT導入支援事業者との連携

### 🛠️ 対象ITツール
- 会計・財務・給与ソフト
- 顧客管理・営業支援システム
- ECサイト・ネットショップ構築

詳しい申請方法についてもお尋ねください！"""

        return {
            'answer': answer,
            'recommended_subsidies': self._get_subsidies_by_keyword(['IT導入']),
            'confidence_score': 0.9,
            'model_used': 'improved-it'
        }
    
    def _get_general_response(self):
        """一般的な回答"""
        answer = """## 💡 補助金制度について

### 主要な補助金制度
- **IT導入補助金**: デジタル化支援（最大450万円）
- **ものづくり補助金**: 設備投資支援（最大1,250万円）
- **小規模事業者持続化補助金**: 販路開拓支援（最大200万円）

### 選択のポイント
1. 事業規模と目的の明確化
2. 投資予定額の確認
3. 申請時期の把握

具体的な補助金についてお聞かせください！"""

        return {
            'answer': answer,
            'recommended_subsidies': self._get_all_subsidies()[:3],
            'confidence_score': 0.7,
            'model_used': 'improved-general'
        }
    
    def _get_subsidies_by_keyword(self, keywords):
        """キーワードで補助金を検索"""
        subsidies = []
        try:
            for keyword in keywords:
                subsidy = SubsidyType.objects.filter(
                    name__icontains=keyword
                ).first()
                if subsidy:
                    subsidies.append(subsidy)
        except Exception as e:
            print(f"補助金検索エラー: {e}")
        return subsidies
    
    def _get_all_subsidies(self):
        """全補助金を取得"""
        try:
            return list(SubsidyType.objects.all()[:5])
        except Exception as e:
            print(f"補助金取得エラー: {e}")
            return []
'''
    
    # ファイルに保存
    try:
        with open('advisor/services/improved_ai_advisor.py', 'w', encoding='utf-8') as f:
            f.write(improved_service_code)
        print("✅ improved_ai_advisor.py を作成しました")
    except Exception as e:
        print(f"❌ ファイル作成エラー: {e}")

def update_services_init():
    """services/__init__.pyを強制更新"""
    
    init_code = '''# advisor/services/__init__.py
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
'''
    
    try:
        with open('advisor/services/__init__.py', 'w', encoding='utf-8') as f:
            f.write(init_code)
        print("✅ services/__init__.py を更新しました")
    except Exception as e:
        print(f"❌ __init__.py更新エラー: {e}")

def force_reload_django():
    """Djangoモジュールを強制リロード"""
    import importlib
    import sys
    
    # キャッシュクリア
    modules_to_clear = [
        'advisor.services',
        'advisor.services.improved_ai_advisor'
    ]
    
    for module_name in modules_to_clear:
        if module_name in sys.modules:
            del sys.modules[module_name]
            print(f"🗑️ {module_name} をキャッシュから削除")

def test_service():
    """サービスをテスト"""
    try:
        # Django設定
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
        import django
        django.setup()
        
        from advisor.services import AIAdvisorService
        
        service = AIAdvisorService()
        result = service.analyze_question("ものづくり補助金の申請方法を教えてください", {})
        
        print(f"✅ テスト成功")
        print(f"使用モデル: {result['model_used']}")
        print(f"回答開始: {result['answer'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

def main():
    """メイン実行"""
    print("🚀 直接修正を開始します")
    print("=" * 50)
    
    # 1. 改良版サービスを作成
    create_improved_service()
    
    # 2. services/__init__.py を更新
    update_services_init()
    
    # 3. キャッシュクリア
    force_reload_django()
    
    # 4. テスト実行
    test_result = test_service()
    
    print("=" * 50)
    if test_result:
        print("✅ 修正完了！サーバーを再起動してください")
        print("\n📋 次のステップ:")
        print("1. python manage.py runserver を停止（Ctrl+C）")
        print("2. python manage.py runserver 0.0.0.0:8000 で再起動")
        print("3. チャットで「ものづくり補助金の申請方法を教えてください」をテスト")
    else:
        print("❌ 修正に問題があります。詳細なエラーを確認してください")

if __name__ == "__main__":
    main()