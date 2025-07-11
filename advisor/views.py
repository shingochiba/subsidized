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
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json

from .models import SubsidyType, AdoptionStatistics, AdoptionTips
from .services import AIAdvisorService, ConversationManager, AdoptionAnalysisService


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

# advisor/views.py の QuestionAPIView を以下のように更新

@method_decorator(csrf_exempt, name='dispatch')
class QuestionAPIView(View):
    """質問処理API（文脈認識対応）"""
    
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
            
            # AI分析（session_idを渡して文脈認識を有効化）
            ai_service = AIAdvisorService()
            result = ai_service.analyze_question(
                question_text, 
                user_context, 
                session_id=session_id  # ← 重要: session_idを追加
            )
            
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


class AdoptionAnalysisView(View):
    """採択率分析画面"""
    
    def get(self, request, subsidy_id=None):
        analysis_service = AdoptionAnalysisService()
        
        # 補助金一覧を取得
        subsidies = SubsidyType.objects.all()
        
        # 特定の補助金が指定されている場合
        selected_subsidy = None
        statistics_data = None
        tips_data = None
        
        if subsidy_id:
            selected_subsidy = get_object_or_404(SubsidyType, id=subsidy_id)
            
            # 統計データを取得
            statistics_data = analysis_service.get_adoption_statistics(subsidy_id)
            
            # ティップスを取得
            tips_data = analysis_service.get_adoption_tips(subsidy_id)
        else:
            # 全体統計を取得
            statistics_data = analysis_service.get_adoption_statistics()
        
        context = {
            'subsidies': subsidies,
            'selected_subsidy': selected_subsidy,
            'statistics_data': statistics_data,
            'tips_data': tips_data,
        }
        
        return render(request, 'advisor/adoption_analysis.html', context)

@api_view(['GET'])
def adoption_statistics_api(request, subsidy_id=None):
    """採択統計データAPI"""
    analysis_service = AdoptionAnalysisService()
    
    years = int(request.GET.get('years', 3))
    statistics = analysis_service.get_adoption_statistics(subsidy_id, years)
    
    return Response(statistics)

@api_view(['GET'])
def adoption_tips_api(request, subsidy_id):
    """採択ティップスAPI"""
    analysis_service = AdoptionAnalysisService()
    tips = analysis_service.get_adoption_tips(subsidy_id)
    
    return Response(tips)

@method_decorator(csrf_exempt, name='dispatch')
class AdoptionProbabilityView(View):
    """採択可能性分析API"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            subsidy_id = data.get('subsidy_id')
            user_context = data.get('context', {})
            
            if not subsidy_id:
                return JsonResponse({'error': '補助金IDが必要です'}, status=400)
            
            subsidy = get_object_or_404(SubsidyType, id=subsidy_id)
            analysis_service = AdoptionAnalysisService()
            
            # 採択可能性を計算
            probability = analysis_service.calculate_adoption_probability(
                request.user if request.user.is_authenticated else None,
                subsidy,
                user_context
            )
            
            # スコアカードを生成（ログインユーザーのみ）
            scorecard = None
            if request.user.is_authenticated:
                scorecard = analysis_service.generate_scorecard(
                    request.user, subsidy, user_context
                )
            
            # 成功要因分析を取得
            success_factors = analysis_service.get_success_factors_analysis(subsidy)
            
            response_data = {
                'probability': round(probability, 1),
                'subsidy_name': subsidy.name,
                'scorecard': scorecard,
                'success_factors': success_factors,
                'recommendations': self._generate_recommendations(probability, user_context)
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"Error in AdoptionProbabilityView: {e}")
            return JsonResponse({'error': 'システムエラーが発生しました'}, status=500)
    
    def _generate_recommendations(self, probability, user_context):
        """確率に基づく推奨アクションを生成"""
        recommendations = []
        
        if probability >= 70:
            recommendations.append({
                'type': 'success',
                'title': '申請をお勧めします',
                'content': '採択可能性が高いです。申請書類の最終確認を行い、期限内に申請してください。'
            })
        elif probability >= 50:
            recommendations.append({
                'type': 'warning',
                'title': '改善後の申請を推奨',
                'content': '採択の可能性はありますが、いくつかの改善により確率を高めることができます。'
            })
        else:
            recommendations.append({
                'type': 'info',
                'title': '事業計画の見直しを推奨',
                'content': '現状では採択が困難な可能性があります。事業計画の根本的な見直しを検討してください。'
            })
        
        # 企業規模に応じた推奨
        company_size = user_context.get('company_size', '')
        if '小規模' in company_size:
            recommendations.append({
                'type': 'info',
                'title': '小規模事業者向けサポート',
                'content': '商工会議所の申請サポートを活用することで、採択率が向上する可能性があります。'
            })
        
        return recommendations

@login_required
@api_view(['GET'])
def user_application_history(request):
    """ユーザーの申請履歴API"""
    from .models import UserApplicationHistory
    
    history = UserApplicationHistory.objects.filter(
        user=request.user
    ).select_related('subsidy_type').order_by('-application_date')
    
    data = []
    for app in history:
        data.append({
            'id': app.id,
            'subsidy_name': app.subsidy_type.name,
            'application_date': app.application_date.isoformat(),
            'status': app.status,
            'status_display': app.get_status_display(),
            'result_date': app.result_date.isoformat() if app.result_date else None,
            'requested_amount': app.requested_amount,
            'feedback': app.feedback
        })
    
    return Response(data)

@method_decorator(csrf_exempt, name='dispatch')
class ApplicationHistoryView(View):
    """申請履歴の登録・更新"""
    
    @method_decorator(login_required)
    def post(self, request):
        try:
            from .models import UserApplicationHistory
            
            data = json.loads(request.body)
            
            # 新規申請履歴を作成
            history = UserApplicationHistory.objects.create(
                user=request.user,
                subsidy_type_id=data['subsidy_id'],
                application_date=data['application_date'],
                application_round=data.get('application_round', 1),
                status=data.get('status', 'preparing'),
                business_type_at_application=data.get('business_type', ''),
                company_size_at_application=data.get('company_size', ''),
                requested_amount=data.get('requested_amount')
            )
            
            return JsonResponse({
                'success': True,
                'history_id': history.id
            })
            
        except Exception as e:
            print(f"Error in ApplicationHistoryView: {e}")
            return JsonResponse({'error': 'システムエラーが発生しました'}, status=500)

@api_view(['GET'])
def industry_comparison(request):
    """業種別採択率比較API"""
    analysis_service = AdoptionAnalysisService()
    
    # 各補助金の業種別統計を取得
    subsidies = SubsidyType.objects.all()
    comparison_data = {}
    
    for subsidy in subsidies:
        success_factors = analysis_service.get_success_factors_analysis(subsidy)
        if success_factors and success_factors['industry_success_rates']:
            comparison_data[subsidy.name] = success_factors['industry_success_rates']
    
    return Response(comparison_data)