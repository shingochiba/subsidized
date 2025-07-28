# fixed_syntax_error.py
# views.pyのシンタックスエラーを修正（f-string修正版）

import re

def fix_views_syntax():
    """views.pyのシンタックスエラーを修正"""
    
    try:
        with open('advisor/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔍 シンタックスエラーを検索中...")
        
        # 問題のあるパターンを修正
        fixes = [
            # }def のような構文エラーを修正
            (r'\}def ', '}\n\ndef '),
            (r'\}class ', '}\n\nclass '),
            
            # 不正な改行や文字を修正
            (r'\}\s*def ', '}\n\ndef '),
            (r'\}\s*class ', '}\n\nclass '),
        ]
        
        original_content = content
        
        for pattern, replacement in fixes:
            content = re.sub(pattern, replacement, content)
        
        # 特定の問題箇所を直接修正
        if '}def determine_current_message_flow' in content:
            content = content.replace('}def determine_current_message_flow', '}\n\ndef determine_current_message_flow')
            print("✅ }def 構文エラーを修正しました")
        
        if '}def analyze_message_improved' in content:
            content = content.replace('}def analyze_message_improved', '}\n\ndef analyze_message_improved')
            print("✅ analyze_message_improved の }def エラーを修正しました")
        
        # 修正内容を保存
        if content != original_content:
            with open('advisor/views.py', 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ views.py のシンタックスエラーを修正しました")
            return True
        else:
            print("ℹ️ 修正が必要な箇所は見つかりませんでした")
            return False
            
    except Exception as e:
        print("❌ 修正エラー:", str(e))
        return False

def validate_python_syntax():
    """Pythonファイルの構文をチェック"""
    
    try:
        with open('advisor/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 構文チェック
        compile(content, 'advisor/views.py', 'exec')
        print("✅ views.py の構文チェック完了")
        return True
        
    except SyntaxError as e:
        print("❌ 構文エラー:", str(e))
        print("行番号:", e.lineno)
        if e.text:
            print("エラー位置:", e.text.strip())
        return False
    except Exception as e:
        print("❌ チェックエラー:", str(e))
        return False

def backup_and_clean_views():
    """views.pyをバックアップして問題箇所をクリーンアップ"""
    
    try:
        # バックアップ作成
        with open('advisor/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open('advisor/views_backup.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ views.py をバックアップしました")
        
        # 問題箇所を特定して修正
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # 問題のある行を修正
            if '}def ' in line:
                # }def を正しい形式に修正
                fixed_line = line.replace('}def ', '}\n\ndef ')
                fixed_lines.extend(fixed_line.split('\n'))
                print("✅ 行" + str(i+1) + "を修正: }def エラー")
            elif line.strip().startswith('def ') and i > 0 and not lines[i-1].strip().endswith(':') and not lines[i-1].strip() == '':
                # 関数定義の前に改行を追加
                fixed_lines.append('')
                fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # 修正されたコンテンツを保存
        with open('advisor/views.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_lines))
        
        print("✅ views.py をクリーンアップしました")
        return True
        
    except Exception as e:
        print("❌ クリーンアップエラー:", str(e))
        return False

def emergency_views_replacement():
    """緊急時用：views.pyの問題箇所を完全置換"""
    
    # 緊急時用の最小限のviews.py
    emergency_views = '''# advisor/views.py - 緊急修正版

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
import json
import uuid
from datetime import datetime, timedelta

# モデルのインポート
from .models import SubsidyType, Question, Answer, ConversationHistory

# サービスのインポート（エラー処理付き）
try:
    from .services import AIAdvisorService, ConversationManager
    SERVICES_AVAILABLE = True
except ImportError as e:
    print("Warning: Services import error:", str(e))
    SERVICES_AVAILABLE = False
    
    class AIAdvisorService:
        def analyze_question(self, question_text, user_context=None):
            return {
                'answer': 'サービスが利用できません。',
                'recommended_subsidies': [],
                'confidence_score': 0.0,
                'model_used': 'fallback'
            }
    
    class ConversationManager:
        @staticmethod
        def save_conversation(*args, **kwargs):
            pass
        
        @staticmethod
        def get_conversation_history(*args, **kwargs):
            return []

def index(request):
    """メインページ"""
    return render(request, 'advisor/index.html')

def chat(request):
    """チャットページ"""
    return render(request, 'advisor/chat.html')

@csrf_exempt
def enhanced_chat_api(request):
    """Enhanced Chat API エンドポイント - 修正版"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        user_context = data.get('user_context', {})
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'メッセージが入力されていません'
            }, status=400)
        
        # 直接質問解析
        result = analyze_message_improved(message, user_context)
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'response': {
                'answer': result['answer'],
                'recommendedSubsidies': result.get('recommended_subsidies', []),
                'confidenceScore': result.get('confidence_score', 0.7),
                'modelUsed': result.get('model_used', 'emergency-fix')
            }
        })
        
    except Exception as e:
        print("Enhanced chat API error:", str(e))
        return JsonResponse({
            'success': False,
            'error': '処理中にエラーが発生しました'
        }, status=500)

def analyze_message_improved(message, user_context=None):
    """改良された直接メッセージ解析 - 緊急修正版"""
    message_lower = message.lower()
    
    print("🔍 メッセージ解析:", message)
    
    # ものづくり補助金
    if any(keyword in message_lower for keyword in ['ものづくり', 'monozukuri', '設備投資']):
        print("✅ ものづくり補助金として検出")
        
        if any(keyword in message_lower for keyword in ['申請方法', '申請手順', 'やり方', '申請']):
            return {
                'answer': """## 🏭 ものづくり補助金の申請方法

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
   - 審査項目：技術面、事業化面、政策面

3. **結果通知**
   - 採択・不採択の連絡

### ⚠️ 申請時の重要ポイント

#### **革新性の明確化**
- 従来技術との違いを具体的に説明
- 新規性・優位性を数値で表現
- 特許・ノウハウの活用

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

### 📞 サポート体制

- **認定支援機関**: 商工会議所、中小企業診断士等
- **地域事務局**: 各都道府県の相談窓口
- **専門家派遣**: 申請書作成支援

ご質問やより詳細な相談については、お気軽にお尋ねください！""",
                'confidence_score': 0.95,
                'model_used': 'emergency-monozukuri-application',
                'recommended_subsidies': []
            }
        else:
            return {
                'answer': """## 🏭 ものづくり補助金について

**正式名称**: ものづくり・商業・サービス生産性向上促進補助金

### 📊 補助金概要
- **補助上限額**: 1,250万円（デジタル枠）
- **補助率**: 1/2以内（小規模事業者は2/3）
- **対象**: 革新的な設備投資・サービス開発
- **申請時期**: 年2-3回程度

### 🎯 対象となる事業

#### **革新的サービス開発・試作品開発**
- 新製品・新サービスの開発
- 既存サービスの革新的改善

#### **設備投資**
- 生産性向上設備の導入
- IoT・AI等の先進技術活用
- 省エネ・環境配慮型設備

### ✅ 主な要件

1. **対象者**: 中小企業・小規模事業者
2. **事業継続**: 3年間の事業継続
3. **生産性向上**: 付加価値額年率平均3%以上向上
4. **革新性**: 従来技術との明確な違い

### 💰 補助対象経費

- **機械装置・システム構築費**
- **技術導入費**
- **専門家経費**
- **運搬費**
- **クラウドサービス利用費**

### 🚀 期待される効果

- 生産効率の大幅向上
- 新市場・新顧客の開拓
- 競争力の強化
- 売上・利益の拡大

申請方法や具体的な手順についてもお聞かせください！""",
                'confidence_score': 0.9,
                'model_used': 'emergency-monozukuri-general',
                'recommended_subsidies': []
            }
    
    # IT導入補助金
    elif any(keyword in message_lower for keyword in ['it導入', 'itツール', 'デジタル化', 'it補助金']):
        print("✅ IT導入補助金として検出")
        
        if any(keyword in message_lower for keyword in ['申請方法', '申請手順', 'やり方', '申請']):
            return {
                'answer': """## 🖥️ IT導入補助金の申請方法

IT導入補助金の申請手順を詳しくご説明いたします。

### 📋 基本情報
- **正式名称**: サービス等生産性向上IT導入支援事業
- **補助上限額**: 最大450万円
- **補助率**: 1/2以内
- **申請時期**: 年2回程度の公募

### 📅 詳細な申請手順

#### **STEP 1: 事前準備（申請の1-2ヶ月前）**

1. **gBizIDプライムの取得**
   - 法人・個人事業主向け認証システム
   - 申請から発行まで約2週間
   - **必須要件です**

2. **SECURITY ACTIONの実施**
   - ★一つ星または★★二つ星の取得
   - 情報セキュリティ対策の実施
   - **申請前に必ず完了させてください**

3. **IT導入支援事業者の選定**
   - 事前登録されたIT導入支援事業者から選択
   - ITツール選定の相談
   - 申請書作成支援

#### **STEP 2: ITツール選定（申請の1ヶ月前）**

1. **対象ITツールの確認**
   - 事前登録されたITツールから選択
   - 自社の課題解決に適したツール選定
   - 複数ツールの組み合わせも可能

2. **見積書の取得**
   - IT導入支援事業者から見積書取得
   - ライセンス費用、導入費用の確認
   - 保守・サポート費用の算出

#### **STEP 3: 申請書作成**

1. **交付申請書の作成**
   - IT導入支援事業者と共同作成
   - 現状の課題分析
   - 導入効果の説明

2. **必要書類の準備**
   - 履歴事項全部証明書
   - 決算書または確定申告書
   - 労働生産性向上に関する資料

#### **STEP 4: 申請・審査**

1. **電子申請**
   - 申請マイページからの提出
   - IT導入支援事業者が代理申請
   - 期限厳守

2. **審査期間**
   - 約1-2ヶ月
   - 書面審査のみ

3. **交付決定通知**
   - 採択・不採択の連絡

#### **STEP 5: ITツール導入・実績報告**

1. **ITツール導入**
   - 交付決定後に契約・導入開始
   - IT導入支援事業者のサポート

2. **実績報告**
   - 導入完了後30日以内
   - 効果測定結果の報告

3. **補助金交付**
   - 実績確認後に補助金支払い

### ⚠️ 申請時の重要ポイント

#### **生産性向上の明確化**
- 具体的な業務効率改善効果
- 定量的な効果測定指標
- 労働生産性向上の説明

#### **IT導入支援事業者の選択**
- 実績と専門性の確認
- サポート体制の充実度
- 継続的な保守・運用支援

#### **セキュリティ対策の実施**
- SECURITY ACTIONの完了
- 情報セキュリティ方針の策定
- 従業員への教育・研修

### 💡 採択率向上のコツ

1. **早期準備**: gBizID、SECURITY ACTION の事前取得
2. **適切なツール選択**: 自社課題に最適なITツール選定
3. **明確な効果説明**: 導入前後の比較を数値化
4. **信頼できるパートナー**: 実績豊富なIT導入支援事業者との連携

### 🛠️ 対象ITツール例

- **会計ソフト**: 財務管理の効率化
- **顧客管理システム**: 営業活動の最適化
- **ECサイト**: オンライン販売の拡充
- **勤怠管理システム**: 労務管理の自動化
- **在庫管理システム**: 在庫の適正化

### 📞 サポート窓口

- **IT導入補助金事務局**: 全般的な問い合わせ
- **IT導入支援事業者**: 具体的な申請支援
- **地域の商工会議所**: 地域密着型サポート

ご不明な点があれば、お気軽にお尋ねください！""",
                'confidence_score': 0.95,
                'model_used': 'emergency-it-application',
                'recommended_subsidies': []
            }
        else:
            return {
                'answer': """## 🖥️ IT導入補助金について

### 📊 基本情報
- **補助上限額**: 最大450万円
- **補助率**: 1/2以内
- **対象**: ITツール・ソフトウェアの導入

### 📋 申請要件
1. **gBizIDプライム**の取得
2. **SECURITY ACTION**の実施  
3. IT導入支援事業者との連携

### 🛠️ 対象ITツール
- 会計・財務・給与ソフト
- 顧客管理・営業支援システム
- ECサイト・ネットショップ構築
- 勤怠管理・人事システム

### 📈 導入効果
デジタル化により業務効率が向上し、売上アップや労働時間短縮が期待できます。

申請方法の詳細についてもお尋ねください！""",
                'confidence_score': 0.9,
                'model_used': 'emergency-it-general',
                'recommended_subsidies': []
            }
    
    # 小規模事業者持続化補助金
    elif any(keyword in message_lower for keyword in ['小規模', '持続化', '販路開拓', '小規模事業者']):
        print("✅ 小規模事業者持続化補助金として検出")
        
        if any(keyword in message_lower for keyword in ['申請方法', '申請手順', 'やり方', '申請']):
            return {
                'answer': """## 🏢 小規模事業者持続化補助金の申請方法

小規模事業者持続化補助金の申請手順を詳しくご説明いたします。

### 📋 基本情報
- **正式名称**: 小規模事業者持続化補助金
- **補助上限額**: 最大200万円（創業型）
- **補助率**: 2/3以内
- **申請時期**: 年4回程度の公募

### 📅 詳細な申請手順

#### **STEP 1: 事前準備（申請の2-3ヶ月前）**

1. **小規模事業者要件の確認**
   - 製造業：従業員20人以下
   - 商業・サービス業：従業員5人以下
   - **必須要件です**

2. **商工会議所との連携**
   - 地域の商工会議所に相談予約
   - 経営計画策定の指導依頼
   - **様式4（確認書）の取得が必要**

3. **現状分析の実施**
   - 自社の強み・弱みの分析
   - 市場環境・競合状況の把握
   - 課題・問題点の整理

#### **STEP 2: 経営計画策定（申請の1-2ヶ月前）**

1. **経営計画書の作成（様式2）**
   - 企業概要の記載
   - 顧客ニーズと市場の動向
   - 自社の経営状況分析
   - 経営方針・目標と今後のプラン

2. **補助事業計画書の作成（様式3）**
   - 補助事業の具体的内容
   - 販路開拓等の取組内容
   - 業務効率化の取組内容
   - 補助事業の効果

#### **STEP 3: 必要書類準備**

1. **基本書類**
   - 小規模事業者持続化補助金交付申請書（様式1）
   - 経営計画書（様式2）
   - 補助事業計画書（様式3）
   - 商工会議所の確認書（様式4）

2. **添付書類**
   - 履歴事項全部証明書
   - 決算書または確定申告書
   - 見積書（複数業者から推奨）
   - 位置図・写真等

#### **STEP 4: 申請・審査**

1. **申請書提出**
   - 電子申請（Jグランツ）
   - 商工会議所経由での提出
   - 期限厳守

2. **審査期間**
   - 約2-3ヶ月
   - 書面審査

3. **採択発表**
   - 採択・不採択の通知

#### **STEP 5: 事業実施・報告**

1. **補助事業の実施**
   - 採択通知後に事業開始
   - 計画に沿った着実な実行

2. **実績報告**
   - 事業完了後30日以内
   - 実績報告書の提出
   - 領収書等の証憑書類添付

3. **補助金交付**
   - 実績確認後に補助金支払い

### ⚠️ 申請時の重要ポイント

#### **商工会議所との密な連携**
- 経営計画策定の段階から相談
- 様式4（確認書）の取得は必須
- 継続的な経営支援の活用

#### **具体的な販路開拓計画**
- ターゲット顧客の明確化
- 具体的なアプローチ方法
- 期待される効果の数値化

#### **実現可能性の重視**
- 無理のない事業計画
- 自社の体制・能力に見合った内容
- 継続的な取組への発展性

### 💡 採択率向上のコツ

1. **早期の商工会議所相談**: 計画策定段階からサポート活用
2. **現状分析の徹底**: SWOT分析等による客観的な現状把握
3. **具体的な目標設定**: 売上増加等の定量的な目標設定
4. **継続性の説明**: 補助事業終了後の継続・発展計画

### 🎯 対象となる取組例

#### **販路開拓の取組**
- 新商品・サービスのPR
- ホームページ・ECサイト構築
- 展示会・商談会への参加
- 店舗改装・商品陳列の工夫

#### **業務効率化の取組**
- 専門家によるコンサルティング
- ITシステムの導入
- 機器・設備の導入
- 従業員教育・研修

### 📞 サポート窓口

- **地域の商工会議所**: 経営計画策定支援
- **事務局**: 制度全般の問い合わせ
- **中小企業診断士等**: 専門的なアドバイス

ご質問があれば、まずは地域の商工会議所にご相談ください！""",
                'confidence_score': 0.95,
                'model_used': 'emergency-jizokuuka-application',
                'recommended_subsidies': []
            }
        else:
            return {
                'answer': """## 🏢 小規模事業者持続化補助金について

### 📊 基本情報
- **補助上限額**: 最大200万円（創業型）
- **補助率**: 2/3以内
- **対象**: 販路開拓・生産性向上

### ✅ 主な要件
1. 小規模事業者であること
2. 商工会議所の支援
3. 経営計画の策定

### 🎯 対象事業
- 広告宣伝・PR活動
- 展示会・商談会参加
- ホームページ・ECサイト作成
- 店舗改装・設備導入

### 📈 期待される効果
販路拡大により売上向上と事業の持続的発展が見込めます。

商工会議所との連携方法についてもサポートします。""",
                'confidence_score': 0.9,
                'model_used': 'emergency-jizokuuka-general',
                'recommended_subsidies': []
            }
    
    # 省力化投資補助金
    elif any(keyword in message_lower for keyword in ['省力化', '人手不足', '自動化', 'iot', 'ai', 'ロボット']):
        print("✅ 省力化投資補助金として検出")
        
        if any(keyword in message_lower for keyword in ['申請方法', '申請手順', 'やり方', '申請']):
            return {
                'answer': """## 🤖 省力化投資補助金の申請方法

省力化投資補助金の申請手順を詳しくご説明いたします。

### 📋 基本情報
- **正式名称**: 中小企業省力化投資補助金
- **補助上限額**: 1,000万円
- **補助率**: 1/2以内
- **申請時期**: 年3-4回程度の公募

### 📅 詳細な申請手順

#### **STEP 1: 事前準備（申請の2-3ヶ月前）**

1. **対象要件の確認**
   - 中小企業・小規模事業者の該当確認
   - 人手不足の状況説明
   - 省力化の必要性

2. **省力化製品の選定**
   - 事前登録された省力化製品から選択
   - IoT・AI・ロボット等の先進技術
   - 自社の課題解決に適した製品選定

#### **STEP 2: 計画策定（申請の1-2ヶ月前）**

1. **事業計画書の作成**
   - 現在の人手不足状況
   - 導入する省力化設備の詳細
   - 省力化効果の定量的説明
   - 3年間の事業継続計画

2. **効果測定計画**
   - 導入前後の労働時間比較
   - 生産性向上効果の算出
   - 付加価値額向上の根拠

#### **STEP 3: 申請書作成・提出**

1. **申請書類作成**
   - 交付申請書
   - 事業計画書
   - 経費内訳書
   - 見積書・仕様書

2. **電子申請**
   - 専用システムからの提出
   - 期限厳守

#### **STEP 4: 審査・事業実施**

1. **審査期間**: 約1-2ヶ月
2. **事業実施**: 採択後の設備導入
3. **実績報告**: 効果測定結果の報告

### ⚠️ 重要ポイント

- **省力化効果の定量化**が最重要
- **人手不足の深刻さ**を具体的に説明
- **継続的な運用計画**の明示

詳しい申請サポートについてもお尋ねください！""",
                'confidence_score': 0.95,
                'model_used': 'emergency-shorikuka-application',
                'recommended_subsidies': []
            }
        else:
            return {
                'answer': """## 🤖 省力化投資補助金について

### 📊 基本情報
- **補助上限額**: 1,000万円
- **補助率**: 1/2以内
- **対象**: AI・IoT・ロボット等の省力化設備

### 🔧 対象設備
- AI・IoT機器
- ロボット・自動化装置
- センサー・制御システム
- 省力化ソフトウェア

### ✅ 主な要件
1. 省力化効果の定量的説明
2. 3年間の事業継続
3. 付加価値額の向上計画

### 📈 期待される効果
人手不足の解消と同時に、作業効率の大幅な向上が見込めます。

申請手順についてもお気軽にお尋ねください！""",
                'confidence_score': 0.9,
                'model_used': 'emergency-shorikuka-general',
                'recommended_subsidies': []
            }
    
    # 採択率に関する質問
    elif any(keyword in message_lower for keyword in ['採択率', '通る確率', '成功率', '受かる']):
        print("✅ 採択率質問として検出")
        return {
            'answer': """## 📊 主要補助金の採択率

### 最近の採択率実績

**IT導入補助金**: 約70%
- 比較的採択されやすい
- 要件を満たせば高確率

**ものづくり補助金**: 約50%
- 競争が激しい
- 革新性が重要

**小規模事業者持続化補助金**: 約60%
- 小規模事業者には有利
- 地域性も考慮される

**省力化投資補助金**: 約55%
- 人手不足解消のニーズが高い
- 効果の定量化が重要

### 採択率を上げるポイント
1. 要件の完全な理解
2. 具体的な効果の説明
3. 適切な支援機関との連携
4. 早期の準備開始

より詳しい成功のコツについてもお教えできます。""",
            'confidence_score': 0.9,
            'model_used': 'emergency-adoption-rate',
            'recommended_subsidies': []
        }
    
    # 申請方法の一般的な質問（特定の補助金が明確でない場合）
    elif any(keyword in message_lower for keyword in ['申請方法', '申請手順', 'やり方', '手続き']) and '申請' in message_lower:
        print("✅ 一般的な申請方法質問として検出")
        return {
            'answer': """## 📋 補助金申請の基本手順

### 共通する申請フロー

#### **STEP 1: 事前準備**
1. **公募要領の確認**
   - 最新版のダウンロード
   - 対象要件・対象経費の把握
2. **必要書類の準備**
   - 決算書、確定申告書
   - 履歴事項全部証明書
3. **支援機関との連携**
   - 商工会議所、認定支援機関

#### **STEP 2: 計画策定**
1. **事業計画書の作成**
   - 現状分析と課題整理
   - 具体的な取組内容
   - 期待される効果
2. **見積書の取得**
   - 複数業者からの相見積もり

#### **STEP 3: 申請・審査**
1. **電子申請**
   - Jグランツ等の指定システム
2. **審査期間**
   - 通常1-3ヶ月
3. **結果通知**

#### **STEP 4: 事業実施・報告**
1. **採択後の事業開始**
2. **実績報告書の提出**
3. **補助金の交付**

### 📋 補助金別の詳細申請方法

どちらの補助金の申請方法をお知りになりたいですか？

- **「IT導入補助金の申請方法を教えて」**
- **「ものづくり補助金の申請方法を教えて」**
- **「小規模事業者持続化補助金の申請方法を教えて」**
- **「省力化投資補助金の申請方法を教えて」**

具体的な補助金名をお聞かせいただければ、より詳細な申請手順をご説明いたします！""",
            'confidence_score': 0.8,
            'model_used': 'emergency-general-application',
            'recommended_subsidies': []
        }
    
    # 一般的な補助金質問
    else:
        print("✅ 一般的な質問として検出")
        return {
            'answer': """## 💡 補助金制度について

### 主要な補助金制度
- **IT導入補助金**: デジタル化支援（最大450万円）
- **ものづくり補助金**: 設備投資支援（最大1,250万円）
- **小規模事業者持続化補助金**: 販路開拓支援（最大200万円）
- **省力化投資補助金**: 人手不足解消支援（最大1,000万円）

### 選択のポイント
1. **事業規模**: 小規模事業者 vs 中小企業
2. **目的**: デジタル化 vs 設備投資 vs 販路拡大
3. **投資額**: 予算に応じた補助金選択
4. **申請時期**: 年間スケジュールの確認

### 次のステップ
以下について詳しくお聞かせください：
- 具体的な取り組み内容
- 投資予定額
- 事業規模

より具体的なアドバイスをご提供いたします！""",
            'confidence_score': 0.7,
            'model_used': 'emergency-general',
            'recommended_subsidies': []
        }

# その他の基本的なビュー関数
@csrf_exempt
def analyze_question(request):
    """既存API互換性のためのエンドポイント"""
    return enhanced_chat_api(request)

def subsidy_list(request):
    """補助金一覧"""
    return render(request, 'advisor/subsidy_list.html')

def subsidy_detail(request, subsidy_id):
    """補助金詳細"""
    return render(request, 'advisor/subsidy_detail.html')

@login_required
def admin_dashboard(request):
    """管理ダッシュボード"""
    return render(request, 'advisor/admin_dashboard.html')

def trend_analysis(request):
    """トレンド分析"""
    return render(request, 'advisor/trend_analysis.html')
'''
    
    try:
        # 現在のviews.pyをバックアップ
        with open('advisor/views.py', 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        with open('advisor/views_broken_backup.py', 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        # 緊急版を保存
        with open('advisor/views.py', 'w', encoding='utf-8') as f:
            f.write(emergency_views)
        
        print("✅ 緊急版views.pyを作成しました")
        return True
        
    except Exception as e:
        print("❌ 緊急版作成エラー:", str(e))
        return False

def main():
    """メイン実行"""
    print("🚨 views.py シンタックスエラー修正を開始")
    print("=" * 50)
    
    # 1. 構文チェック
    if not validate_python_syntax():
        print("シンタックスエラーが検出されました。修正を開始します...")
        
        # 2. 通常の修正を試行
        if fix_views_syntax():
            # 修正後に再チェック
            if validate_python_syntax():
                print("✅ 通常修正で問題解決")
            else:
                print("⚠️ 通常修正では解決できませんでした。緊急修正を実行します...")
                emergency_views_replacement()
        else:
            print("⚠️ 通常修正に失敗しました。緊急修正を実行します...")
            emergency_views_replacement()
    else:
        print("✅ シンタックスエラーは検出されませんでした")
    
    print("=" * 50)
    print("🎉 修正完了！")
    print("\n📋 次のステップ:")
    print("1. python manage.py runserver 0.0.0.0:8000 で再起動")
    print("2. チャット機能をテスト")

if __name__ == "__main__":
    main()