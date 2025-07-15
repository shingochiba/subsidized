import requests
import json
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from ..models import SubsidyType, ConversationHistory, Answer

class EnhancedChatService:
    """強化されたチャット機能 - LLM連携、文脈認識、リアルタイム対応"""
    
    def __init__(self):
        # Dify API設定
        self.dify_api_url = getattr(settings, 'DIFY_API_URL', '')
        self.dify_api_key = getattr(settings, 'DIFY_API_KEY', '')
        self.headers = {
            'Authorization': f'Bearer {self.dify_api_key}',
            'Content-Type': 'application/json'
        }
        
        # デバッグ情報
        print(f"EnhancedChatService initialized:")
        print(f"  API URL: {self.dify_api_url}")
        print(f"  API Key: {'設定済み' if self.dify_api_key else '未設定'}")
        
    def process_conversation(self, message, session_id, user_context=None):
        """
        文脈を考慮した高度な会話処理
        """
        
        # Step 1: 会話履歴の取得と分析
        conversation_context = self._analyze_conversation_history(session_id)
        
        # Step 2: 質問の意図認識
        intent_analysis = self._detect_question_intent(message, conversation_context)
        
        # Step 3: コンテキストに応じた回答生成
        response = self._generate_contextual_response(
            message, intent_analysis, conversation_context, user_context
        )
        
        # Step 4: 会話履歴の保存
        self._save_conversation_turn(session_id, message, response, intent_analysis, user_context)
        
        return response
    
    def _analyze_conversation_history(self, session_id):
        """過去の会話履歴を分析して文脈を理解"""
        recent_history = ConversationHistory.objects.filter(
            session_id=session_id
        ).order_by('-timestamp')[:10]
        
        context = {
            'previous_topics': [],
            'user_preferences': {},
            'discussed_subsidies': [],
            'conversation_flow': 'initial'
        }
        
        if not recent_history:
            return context
        
        # 履歴から文脈を抽出
        for entry in recent_history:
            if entry.message_type == 'user':
                # ユーザーの関心事を抽出
                topics = self._extract_topics_from_message(entry.content)
                context['previous_topics'].extend(topics)
            elif entry.message_type == 'assistant':
                # 過去に推薦した補助金を記録
                subsidies = self._extract_mentioned_subsidies(entry.content)
                context['discussed_subsidies'].extend(subsidies)
        
        # 会話の流れを判定
        context['conversation_flow'] = self._determine_conversation_flow(recent_history)
        
        return context
    
    def _extract_topics_from_message(self, message):
        """メッセージからトピックを抽出"""
        topics = []
        keywords = {
            'IT導入': ['IT', 'システム', 'デジタル', 'ソフトウェア'],
            'ものづくり': ['製造', '設備', '機械', '工場'],
            '事業再構築': ['再構築', '転換', '新事業', '多角化'],
            '小規模事業者': ['小規模', '個人事業', '零細企業'],
            '研究開発': ['研究', '開発', 'R&D', '技術開発']
        }
        
        message_lower = message.lower()
        for topic, words in keywords.items():
            if any(word.lower() in message_lower for word in words):
                topics.append(topic)
        
        return topics
    
    def _extract_mentioned_subsidies(self, content):
        """コンテンツから言及された補助金を抽出"""
        subsidies = []
        subsidy_types = SubsidyType.objects.all()
        
        for subsidy in subsidy_types:
            if subsidy.name in content:
                subsidies.append(subsidy.name)
        
        return subsidies
    
    def _determine_conversation_flow(self, history):
        """会話の流れを判定"""
        if len(history) <= 2:
            return 'initial'
        elif len(history) <= 6:
            return 'developing'
        else:
            return 'continuing'
    
    def _detect_question_intent(self, message, context):
        """AIを使用した質問意図の自動判別"""
        intent_patterns = {
            'search_subsidy': ['補助金', '助成金', '支援', 'どんな', '探し', '見つけ'],
            'application_process': ['申請', '手続き', 'やり方', '方法', '流れ', 'プロセス'],
            'eligibility_check': ['対象', '条件', '要件', '使える', '適用', '当てはまる'],
            'timing_inquiry': ['いつ', 'タイミング', '期限', '時期', 'スケジュール'],
            'amount_inquiry': ['金額', 'いくら', '予算', '費用', '額'],
            'success_tips': ['コツ', 'ポイント', '成功', 'アドバイス', '秘訣'],
            'follow_up': ['続き', 'さらに', 'もっと', '詳しく', '他に']
        }
        
        detected_intents = []
        confidence_scores = {}
        
        message_lower = message.lower()
        
        for intent, keywords in intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                detected_intents.append(intent)
                confidence_scores[intent] = score / len(keywords)
        
        # 会話履歴から継続性を判定
        if context['conversation_flow'] == 'continuing' and 'follow_up' not in detected_intents:
            detected_intents.append('follow_up')
            confidence_scores['follow_up'] = 0.8
        
        primary_intent = max(detected_intents, key=lambda x: confidence_scores[x]) if detected_intents else 'general_inquiry'
        
        return {
            'primary_intent': primary_intent,
            'all_intents': detected_intents,
            'confidence': confidence_scores.get(primary_intent, 0.5),
            'is_follow_up': 'follow_up' in detected_intents
        }
    
    def _generate_contextual_response(self, message, intent, context, user_context):
        """文脈と意図を考慮した高度な回答生成"""
        
        # Dify APIを使用した高度な回答生成
        if self.dify_api_key:
            enhanced_query = self._build_enhanced_query(message, intent, context, user_context)
            
            dify_response = self._call_dify_api(enhanced_query)
            
            if dify_response and 'answer' in dify_response:
                return self._process_dify_response(dify_response, intent, context)
        
        # フォールバック: 意図別の構造化回答
        return self._generate_intent_based_response(message, intent, context, user_context)
    
    def _build_enhanced_query(self, message, intent, context, user_context):
        """文脈を考慮した高度なクエリ構築"""
        
        # 基本情報
        base_info = f"""
【現在の質問】
{message}

【質問の意図分析】
- 主要意図: {intent['primary_intent']}
- 信頼度: {intent['confidence']:.2f}
- フォローアップ: {'はい' if intent['is_follow_up'] else 'いいえ'}
"""
        
        # 会話文脈
        context_info = ""
        if context['previous_topics']:
            context_info += f"\n【過去の話題】\n- " + "\n- ".join(context['previous_topics'][:3])
        
        if context['discussed_subsidies']:
            context_info += f"\n【既に話題に出た補助金】\n- " + "\n- ".join(context['discussed_subsidies'][:3])
        
        # ユーザー情報
        user_info = ""
        if user_context:
            user_info = f"""
【相談者情報】
- 事業種別: {user_context.get('business_type', '未設定')}
- 企業規模: {user_context.get('company_size', '未設定')}
- 地域: {user_context.get('region', '未設定')}
"""
        
        # 補助金データ
        subsidy_data = self._get_relevant_subsidy_data(intent['primary_intent'])
        
        return f"""あなたは経験豊富な補助金専門コンサルタントです。以下の情報を基に、相談者の文脈に沿った最適な回答を提供してください。

{base_info}
{context_info}
{user_info}

【利用可能な補助金情報】
{subsidy_data}

【回答指針】
1. 会話の流れを理解し、継続性のある回答
2. 質問の意図に直接答える
3. 相談者の立場に立った実践的なアドバイス
4. 次のアクションを明確に提示
5. 親しみやすく、専門的すぎない表現

日本語で、温かみのある文体で回答してください。"""

    def _get_relevant_subsidy_data(self, intent):
        """意図に関連する補助金データを取得"""
        subsidies = SubsidyType.objects.filter(is_active=True)[:5]
        
        subsidy_info = []
        for subsidy in subsidies:
            subsidy_info.append(f"""
- {subsidy.name}
  最大金額: {subsidy.max_amount}万円
  対象: {subsidy.target_business_type}
  説明: {subsidy.description[:100]}...
""")
        
        return "\n".join(subsidy_info) if subsidy_info else "補助金データを読み込み中..."
    
    def _call_dify_api(self, query_text):
        """Dify API呼び出し"""
        try:
            request_data = {
                "inputs": {},
                "query": query_text,
                "response_mode": "blocking",
                "user": f"enhanced_chat_{uuid.uuid4().hex[:8]}"
            }
            
            url = f"{self.dify_api_url}/chat-messages"
            
            print(f"Calling Dify API: {url}")
            print(f"Request data preview: {str(request_data)[:200]}...")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=request_data,
                timeout=30
            )
            
            print(f"Dify API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Dify API success: {bool(result.get('answer'))}")
                return result
            else:
                print(f"Dify API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Dify API error: {e}")
            return None
    
    def _process_dify_response(self, dify_response, intent, context):
        """Dify回答の処理と強化"""
        answer = dify_response.get('answer', '')
        
        # 推奨補助金の抽出
        recommended_subsidies = self._extract_recommended_subsidies(answer)
        
        # 信頼度の計算
        confidence_score = self._calculate_response_confidence(answer, intent, context)
        
        return {
            'answer': answer,
            'recommended_subsidies': recommended_subsidies,
            'confidence_score': confidence_score,
            'model_used': 'dify-enhanced',
            'intent_detected': intent['primary_intent'],
            'context_utilized': bool(context['previous_topics'] or context['discussed_subsidies'])
        }
    
    def _extract_recommended_subsidies(self, answer):
        """回答から推奨補助金を抽出"""
        recommended = []
        subsidies = SubsidyType.objects.filter(is_active=True)
        
        for subsidy in subsidies:
            if subsidy.name in answer:
                recommended.append({
                    'id': subsidy.id,
                    'name': subsidy.name,
                    'description': subsidy.description,
                    'max_amount': subsidy.max_amount,
                    'target_business_type': subsidy.target_business_type
                })
        
        return recommended[:3]  # 最大3件
    
    def _calculate_response_confidence(self, answer, intent, context):
        """回答の信頼度を計算"""
        base_confidence = 0.7
        
        # 回答の長さによる調整
        if len(answer) > 200:
            base_confidence += 0.1
        
        # 意図認識の確実性による調整
        if intent['confidence'] > 0.8:
            base_confidence += 0.1
        
        # 文脈利用による調整
        if context['previous_topics'] or context['discussed_subsidies']:
            base_confidence += 0.05
        
        return min(base_confidence, 0.95)
    
    def _generate_intent_based_response(self, message, intent, context, user_context):
        """意図別のフォールバック回答生成"""
        
        intent_type = intent['primary_intent']
        
        if intent_type == 'search_subsidy':
            return self._generate_search_response(user_context)
        elif intent_type == 'application_process':
            return self._generate_process_response()
        elif intent_type == 'eligibility_check':
            return self._generate_eligibility_response(user_context)
        elif intent_type == 'timing_inquiry':
            return self._generate_timing_response()
        elif intent_type == 'amount_inquiry':
            return self._generate_amount_response()
        elif intent_type == 'success_tips':
            return self._generate_tips_response()
        else:
            return self._generate_general_response(message)
    
    def _generate_search_response(self, user_context):
        """補助金検索の回答"""
        business_type = user_context.get('business_type', '一般事業者') if user_context else '一般事業者'
        
        return {
            'answer': f"""
{business_type}様におすすめの補助金をご案内いたします。

## 🎯 主要な補助金制度

### 1. 小規模事業者持続化補助金
- **最大金額**: 200万円
- **対象**: 小規模事業者の販路開拓・生産性向上
- **申請時期**: 年4回（通常2月、6月、10月、2月）

### 2. ものづくり補助金
- **最大金額**: 1,000万円
- **対象**: 革新的な設備投資・システム構築
- **申請時期**: 年2-3回

### 3. IT導入補助金
- **最大金額**: 450万円
- **対象**: ITツール・システム導入
- **申請時期**: 年2回

## 💡 次のステップ
具体的な事業内容をお聞かせいただければ、より詳細なアドバイスが可能です。
""",
            'recommended_subsidies': list(SubsidyType.objects.filter(is_active=True)[:3].values()),
            'confidence_score': 0.8,
            'model_used': 'fallback-search'
        }
    
    def _generate_process_response(self):
        """申請プロセスの回答"""
        return {
            'answer': """
## 📋 補助金申請の基本的な流れ

### **STEP 1: 事前準備**
1. **公募要領の確認** - 最新の申請要件をチェック
2. **必要書類の準備** - 決算書、事業計画書等
3. **スケジュール確認** - 申請期限と事業実施期間

### **STEP 2: 申請書作成**
1. **事業計画書** - 具体的で実現可能な内容
2. **見積書取得** - 複数業者からの相見積もり
3. **経費明細** - 対象経費の詳細リスト

### **STEP 3: 申請・審査**
1. **電子申請** - 指定システムからの提出
2. **審査期間** - 通常1-3ヶ月
3. **結果通知** - 採択・不採択の連絡

### **STEP 4: 事業実施**
1. **交付決定後** - 事業開始（重要！）
2. **実績報告** - 完了後の報告書提出
3. **補助金入金** - 確定検査後の入金

## ⚠️ 重要なポイント
- **交付決定前の発注は補助対象外**
- **実績報告は必須**
- **事業期間内の完了が必要**
""",
            'recommended_subsidies': [],
            'confidence_score': 0.9,
            'model_used': 'fallback-process'
        }
    
    def _generate_general_response(self, message):
        """一般的な回答"""
        return {
            'answer': f"""
ご質問ありがとうございます。

補助金に関するご相談でしたら、以下のような内容でお手伝いできます：

## 🤝 ご提供できるサポート
- **補助金の検索・推奨** - 事業に最適な制度をご提案
- **申請手続きのご案内** - ステップバイステップでサポート
- **申請のコツ・ポイント** - 採択率向上のアドバイス
- **スケジュール管理** - 申請期限の管理支援

## 💬 より具体的なアドバイスのために
以下の情報をお聞かせください：
- 事業の種類や業界
- 企業規模（従業員数など）
- 投資予定の内容
- 希望するタイミング

お気軽にご質問ください！
""",
            'recommended_subsidies': [],
            'confidence_score': 0.6,
            'model_used': 'fallback-general'
        }
    
    def _save_conversation_turn(self, session_id, user_message, assistant_response, intent_analysis, user_context):
        """会話ターンの保存"""
        timestamp = timezone.now()
        
        # ユーザーメッセージ
        ConversationHistory.objects.create(
            session_id=session_id,
            message_type='user',
            content=user_message,
            intent_analysis=intent_analysis,
            user_context=user_context or {},
            timestamp=timestamp
        )
        
        # アシスタント回答
        ConversationHistory.objects.create(
            session_id=session_id,
            message_type='assistant',
            content=assistant_response.get('answer', ''),
            metadata={
                'confidence_score': assistant_response.get('confidence_score', 0),
                'recommended_subsidies': assistant_response.get('recommended_subsidies', []),
                'model_used': assistant_response.get('model_used', 'unknown'),
                'intent_detected': assistant_response.get('intent_detected', ''),
                'context_utilized': assistant_response.get('context_utilized', False)
            },
            timestamp=timestamp + timedelta(seconds=1)
                )