# advisor/api/base.py - jsonインポート追加修正

import json  # この行を追加
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required

from ..models import SubsidyType, ConversationHistory, Answer
from ..services import AIAdvisorService, ConversationManager

@method_decorator(csrf_exempt, name='dispatch')
class BaseAPIView(View):
    """基本APIビューのベースクラス"""
    
    def get_user_context(self, request):
        """リクエストからユーザーコンテキストを取得"""
        user_context = {}
        
        if request.user.is_authenticated:
            user_context['user_id'] = request.user.id
            user_context['username'] = request.user.username
        
        # セッションからコンテキストを取得
        if hasattr(request, 'session'):
            user_context.update({
                'business_type': request.session.get('business_type', ''),
                'company_size': request.session.get('company_size', ''),
                'industry': request.session.get('industry', ''),
                'region': request.session.get('region', ''),
            })
        
        return user_context
    
    def get_session_id(self, request):
        """セッションIDを取得または生成"""
        if 'session_id' not in request.session:
            request.session['session_id'] = str(uuid.uuid4())
        return request.session['session_id']
    
    def save_conversation(self, request, user_message, ai_response):
        """会話履歴を保存"""
        session_id = self.get_session_id(request)
        
        # ユーザーメッセージを保存
        ConversationManager.save_conversation(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None,
            message_type='user',
            content=user_message
        )
        
        # AI回答を保存
        ConversationManager.save_conversation(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None,
            message_type='assistant',
            content=ai_response.get('answer', '')
        )

class EnhancedAPIView(BaseAPIView):
    """強化されたAPIビュー"""
    
    def post(self, request):
        try:
            # リクエストデータの解析
            if request.content_type == 'application/json':
                data = json.loads(request.body)  # ここでjsonモジュールを使用
            else:
                data = request.POST.dict()
            
            question_text = data.get('question', '')
            if not question_text:
                return JsonResponse({
                    'success': False,
                    'error': '質問内容が入力されていません'
                }, status=400)
            
            # ユーザーコンテキストの取得
            user_context = self.get_user_context(request)
            
            # AI分析サービスの呼び出し
            ai_service = AIAdvisorService()
            result = ai_service.analyze_question(question_text, user_context)
            
            # 会話履歴の保存
            self.save_conversation(request, question_text, result)
            
            # レスポンスの構築
            response_data = {
                'success': True,
                'answer': result.get('answer', ''),
                'recommended_subsidies': result.get('recommended_subsidies', []),
                'confidence_score': result.get('confidence_score', 0),
                'session_id': self.get_session_id(request),
                'model_used': result.get('model_used', 'unknown')
            }
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError as e:  # ここでもjsonモジュールを使用
            return JsonResponse({
                'success': False,
                'error': 'JSONデータの解析に失敗しました'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'処理中にエラーが発生しました: {str(e)}'
            }, status=500)

@api_view(['GET'])
def get_subsidy_types(request):
    """補助金種別一覧を取得"""
    try:
        subsidies = SubsidyType.objects.all()
        
        subsidy_data = []
        for subsidy in subsidies:
            subsidy_data.append({
                'id': subsidy.id,
                'name': subsidy.name,
                'description': subsidy.description,
                'max_amount': subsidy.max_amount,
                'target_business_type': subsidy.target_business_type,
                'requirements': subsidy.requirements
            })
        
        return Response({
            'success': True,
            'subsidies': subsidy_data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def get_conversation_history(request, session_id):
    """会話履歴を取得"""
    try:
        history = ConversationHistory.objects.filter(
            session_id=session_id
        ).order_by('timestamp')
        
        history_data = []
        for entry in history:
            history_data.append({
                'message_type': entry.message_type,
                'content': entry.content,
                'timestamp': entry.timestamp.isoformat(),
                'metadata': entry.metadata if hasattr(entry, 'metadata') else {}
            })
        
        return Response({
            'success': True,
            'history': history_data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# エラーハンドリング用のミドルウェア
class APIErrorHandler:
    """API用エラーハンドラー"""
    
    @staticmethod
    def handle_validation_error(error_message):
        """バリデーションエラーのハンドリング"""
        return JsonResponse({
            'success': False,
            'error': error_message,
            'error_type': 'validation'
        }, status=400)
    
    @staticmethod
    def handle_not_found_error(resource_name):
        """リソースが見つからない場合のハンドリング"""
        return JsonResponse({
            'success': False,
            'error': f'{resource_name}が見つかりません',
            'error_type': 'not_found'
        }, status=404)
    
    @staticmethod
    def handle_server_error(error_message):
        """サーバーエラーのハンドリング"""
        return JsonResponse({
            'success': False,
            'error': error_message,
            'error_type': 'server_error'
        }, status=500)

# デバッグ用ユーティリティ
def debug_request_data(request):
    """リクエストデータをデバッグ出力"""
    print(f"Request method: {request.method}")
    print(f"Request content type: {request.content_type}")
    print(f"Request headers: {dict(request.headers)}")
    
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                body_data = json.loads(request.body)  # ここでもjsonモジュールを使用
                print(f"Request JSON body: {body_data}")
            except json.JSONDecodeError:
                print(f"Request body (raw): {request.body}")
        else:
            print(f"Request POST data: {dict(request.POST)}")