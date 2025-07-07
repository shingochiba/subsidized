import requests
import json
import uuid
from django.conf import settings
from .models import SubsidyType, Answer, ConversationHistory

class DifyAIAdvisorService:
    """DifyのGPT-4を使用するAIアドバイザーサービス（修正版）"""
    
    def __init__(self):
        # settings.pyから正しく値を取得
        self.dify_api_url = settings.DIFY_API_URL
        self.dify_api_key = settings.DIFY_API_KEY
        
        # デバッグ用：設定値を確認
        print(f"Initializing DifyAIAdvisorService:")
        print(f"  API URL: {self.dify_api_url}")
        print(f"  API Key: {self.dify_api_key[:10]}..." if self.dify_api_key else "  API Key: (empty)")
        
        self.headers = {
            'Authorization': f'Bearer {self.dify_api_key}',
            'Content-Type': 'application/json'
        }
    
    def analyze_question(self, question_text, user_context=None):
        """DifyのGPT-4を使用して質問を分析"""
        
        if not self.dify_api_key:
            print("Warning: DIFY_API_KEY not set, using mock response")
            return self._generate_mock_response(question_text)
        
        try:
            # 補助金データをコンテキストとして準備
            subsidies_context = self._prepare_subsidies_context()
            
            # 日本語での構造化クエリを作成
            structured_query = self._build_japanese_query(question_text, user_context, subsidies_context)
            
            # Dify API呼び出し
            dify_response = self._call_dify_api(structured_query)
            
            if dify_response and 'answer' in dify_response:
                return self._process_dify_response(dify_response, question_text)
            else:
                print("Dify API call failed or no answer, falling back to mock")
                return self._generate_mock_response(question_text)
                
        except Exception as e:
            print(f"Dify integration error: {e}")
            return self._generate_mock_response(question_text)
    
    def _call_dify_api(self, query_text):
        """修正されたDify API呼び出し"""
        try:
            # 成功した形式: inputs={} + query
            request_data = {
                "inputs": {},
                "query": query_text,
                "response_mode": "blocking",
                "user": f"django_user_{hash(query_text) % 10000}"
            }
            
            # 正しいURL構築
            url = f"{self.dify_api_url}/chat-messages"
            
            print(f"Sending request to: {url}")
            print(f"Request headers: {self.headers}")
            print(f"Request data preview: {json.dumps(request_data, ensure_ascii=False)[:200]}...")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=request_data,
                timeout=60
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"Response received successfully")
                return response_data
            else:
                print(f"Dify API Error: {response.status_code}")
                print(f"Response text: {response.text}")
                return None
                
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error to Dify API: {e}")
            print(f"Attempted URL: {url}")
            return None
        except requests.exceptions.Timeout:
            print("Dify API timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Dify API request error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in Dify API call: {e}")
            return None
    
    def _build_japanese_query(self, question, user_context, subsidies_context):
        """日本語での構造化クエリを作成"""
        business_type = user_context.get('business_type', '未設定') if user_context else '未設定'
        company_size = user_context.get('company_size', '未設定') if user_context else '未設定'
        
        return f"""以下は日本の補助金に関する質問です。日本語で回答してください。

# ユーザー情報
- 事業種別: {business_type}
- 企業規模: {company_size}

# 質問
{question}

# 利用可能な補助金一覧
{subsidies_context}

# 回答要求
以下の形式で日本語で詳細に回答してください：

## 推奨補助金
最適な補助金を1-3個選択

## 推奨理由  
なぜその補助金が適しているか具体的に説明

## 申請手順
1. 具体的な手順
2. 必要書類
3. 提出方法

## 重要な注意点
申請時の注意事項

## 次のアクション
推奨する具体的な行動

必ず日本語で回答してください。"""
    
    def _process_dify_response(self, dify_response, original_question):
        """Difyレスポンスの処理"""
        try:
            answer_text = dify_response.get('answer', '')
            
            if not answer_text:
                print("No answer in Dify response")
                return self._generate_mock_response(original_question)
            
            print(f"Processing Dify answer: {answer_text[:100]}...")
            
            recommended_subsidies = self._extract_recommended_subsidies_from_text(answer_text)
            confidence_score = self._calculate_confidence_score(answer_text)
            formatted_answer = self._format_answer(answer_text)
            
            return {
                'answer': formatted_answer,
                'recommended_subsidies': recommended_subsidies,
                'confidence_score': confidence_score,
                'model_used': 'dify-gpt4'
            }
            
        except Exception as e:
            print(f"Error processing Dify response: {e}")
            return self._generate_mock_response(original_question)
    
    def _extract_recommended_subsidies_from_text(self, answer_text):
        """回答テキストから推奨補助金を抽出"""
        subsidies = SubsidyType.objects.all()
        recommended = []
        
        for subsidy in subsidies:
            if (subsidy.name in answer_text or 
                subsidy.name.replace('2025', '').replace('補助金', '') in answer_text):
                recommended.append(subsidy)
        
        if not recommended:
            answer_lower = answer_text.lower()
            if 'it' in answer_lower or 'システム' in answer_text or 'デジタル' in answer_text:
                it_subsidy = subsidies.filter(name__contains='IT導入').first()
                if it_subsidy:
                    recommended.append(it_subsidy)
        
        return recommended[:3]
    
    def _calculate_confidence_score(self, answer_text):
        """回答の信頼度スコアを計算"""
        score = 0.8  # Dify使用時のベーススコア
        
        if any(char in answer_text for char in 'あいうえおかきくけこ'):
            score += 0.1
        if len(answer_text) > 500:
            score += 0.05
        if '推奨' in answer_text or '申請手順' in answer_text:
            score += 0.05
            
        return min(score, 1.0)
    
    def _format_answer(self, answer_text):
        """回答テキストをフォーマット"""
        formatted = answer_text.replace('##', '## ')
        formatted = formatted.replace('###', '### ')
        return formatted
    
    def _prepare_subsidies_context(self):
        """補助金データをコンテキスト用にフォーマット"""
        subsidies = SubsidyType.objects.all()
        context_parts = []
        
        for subsidy in subsidies:
            context_parts.append(f"""
【{subsidy.name}】
- 対象: {subsidy.target_business}
- 最大額: {subsidy.max_amount:,}円
- 補助率: {subsidy.subsidy_rate}
- 期間: {subsidy.application_period}
- 要件: {subsidy.requirements[:100]}...
""")
        
        return '\n'.join(context_parts)
    
    def _generate_mock_response(self, question_text):
        """フォールバック用のモックレスポンス"""
        subsidies = SubsidyType.objects.all()
        question_lower = question_text.lower()
        
        recommended = []
        if 'it' in question_lower or 'システム' in question_lower or 'デジタル' in question_lower:
            it_subsidy = subsidies.filter(name__contains='IT導入').first()
            if it_subsidy:
                recommended.append(it_subsidy)
        
        if not recommended and subsidies:
            recommended.append(subsidies.first())
        
        mock_answer = f"""## 📋 推奨補助金

{recommended[0].name if recommended else 'IT導入補助金2025'}

## 🎯 推奨理由

ご質問の内容から、こちらの補助金が適していると判断いたします。
（注：Dify接続準備中 - 設定完了後により詳細な回答が可能になります）

## 📝 申請手順

1. **申請前準備**
   - 必要書類の確認
   - 事業計画の検討

2. **申請書類作成**
   - 申請書の記入
   - 見積書の取得

3. **申請提出**
   - オンライン申請
   - 書類提出

## ⚠️ 重要な注意点

- 申請期限の確認が重要です
- 交付決定前の発注は補助対象外です
- 詳細は公式サイトでご確認ください

## 💡 次のアクション

まずは公式サイトで最新の申請要領を確認することをお勧めします。
"""
        
        return {
            'answer': mock_answer,
            'recommended_subsidies': recommended,
            'confidence_score': 0.6,
            'model_used': 'mock-fallback'
        }

# 既存のサービスクラスをDify版に置き換え
AIAdvisorService = DifyAIAdvisorService

class ConversationManager:
    """会話履歴管理（既存のまま）"""
    
    @staticmethod
    def save_conversation(session_id, user, message_type, content):
        ConversationHistory.objects.create(
            session_id=session_id,
            user=user,
            message_type=message_type,
            content=content
        )
    
    @staticmethod
    def get_conversation_history(session_id, limit=10):
        return ConversationHistory.objects.filter(
            session_id=session_id
        ).order_by('-timestamp')[:limit]