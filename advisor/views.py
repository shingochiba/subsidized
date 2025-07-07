from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
import uuid

from .models import Question, Answer, SubsidyType
from .services import AIAdvisorService, ConversationManager

class ChatView(View):
    """メインのチャット画面"""
    
    def get(self, request):
        # セッションIDを生成
        if 'session_id' not in request.session:
            request.session['session_id'] = str(uuid.uuid4())
        
        # 会話履歴を取得
        conversation_history = ConversationManager.get_conversation_history(
            request.session['session_id']
        )
        
        context = {
            'session_id': request.session['session_id'],
            'conversation_history': conversation_history
        }
        return render(request, 'advisor/chat.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class QuestionAPIView(View):
    """質問処理API"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            question_text = data.get('question', '')
            session_id = data.get('session_id', '')
            user_context = data.get('context', {})
            
            if not question_text:
                return JsonResponse({'error': '質問を入力してください'}, status=400)
            
            # 質問を保存
            question = Question.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                question_text=question_text,
                business_type=user_context.get('business_type', ''),
                company_size=user_context.get('company_size', '')
            )
            
            # 会話履歴に保存
            ConversationManager.save_conversation(
                session_id, 
                request.user if request.user.is_authenticated else None,
                'user', 
                question_text
            )
            
            # AI分析
            ai_service = AIAdvisorService()
            result = ai_service.analyze_question(question_text, user_context)
            
            # 回答を保存
            answer = Answer.objects.create(
                question=question,
                answer_text=result['answer'],
                confidence_score=result['confidence_score'],
                ai_model_used=result['model_used']
            )
            
            # 推奨補助金を関連付け
            answer.recommended_subsidies.set(result['recommended_subsidies'])
            
            # 会話履歴に保存
            ConversationManager.save_conversation(
                session_id,
                request.user if request.user.is_authenticated else None,
                'ai',
                result['answer']
            )
            
            # レスポンス
            response_data = {
                'answer': result['answer'],
                'recommended_subsidies': [
                    {
                        'id': s.id,
                        'name': s.name,
                        'description': s.description,
                        'max_amount': s.max_amount,
                        'subsidy_rate': s.subsidy_rate
                    } for s in result['recommended_subsidies']
                ],
                'confidence_score': result['confidence_score'],
                'question_id': question.id
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"Error in QuestionAPIView: {e}")
            return JsonResponse({'error': 'システムエラーが発生しました'}, status=500)

@api_view(['GET'])
def subsidy_list(request):
    """補助金一覧API"""
    subsidies = SubsidyType.objects.all()
    data = [
        {
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'target_business': s.target_business,
            'application_period': s.application_period,
            'max_amount': s.max_amount,
            'subsidy_rate': s.subsidy_rate,
            'requirements': s.requirements
        } for s in subsidies
    ]
    return Response(data)

@api_view(['GET'])
def conversation_history(request, session_id):
    """会話履歴取得API"""
    history = ConversationManager.get_conversation_history(session_id)
    data = [
        {
            'message_type': h.message_type,
            'content': h.content,
            'timestamp': h.timestamp.isoformat()
        } for h in history
    ]
    return Response(data)