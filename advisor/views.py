# advisor/views.py 完全修正版

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
import json
import uuid
import traceback  # インポート追加

from .models import (
    Question, Answer, SubsidyType, ConversationHistory,
    AdoptionStatistics, AdoptionTips, UserApplicationHistory
)
from .services import AIAdvisorService, ConversationManager

# 新しい詳細回答サービスをインポート
try:
    from .services.detailed_response_service import DetailedResponseService
except ImportError:
    # フォールバック: 既存のサービスを使用
    DetailedResponseService = None
    print("⚠️ DetailedResponseService が見つかりません。既存のサービスを使用します。")

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
    """質問処理API（詳細回答対応版）"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            question_text = data.get('question', '')
            session_id = data.get('session_id', '')
            user_context = data.get('context', {})
            
            if not question_text:
                return JsonResponse({'error': '質問を入力してください'}, status=400)
            
            print(f"🤖 質問受信: {question_text}")
            print(f"📋 ユーザーコンテキスト: {user_context}")
            
            # 質問をデータベースに保存
            user = request.user if request.user.is_authenticated else None
            question = Question.objects.create(
                question_text=question_text,
                user=user,
                business_type=user_context.get('business_type', ''),
                company_size=user_context.get('company_size', ''),
                user_context=user_context
            )
            
            # 回答生成
            if DetailedResponseService:
                # 詳細回答サービスを使用
                detailed_service = DetailedResponseService()
                result = detailed_service.analyze_question(
                    question_text=question_text,
                    user_context=user_context
                )
            else:
                # フォールバック: 既存のサービスを使用
                ai_service = AIAdvisorService()
                result = ai_service.analyze_question(
                    question_text=question_text,
                    user_context=user_context
                )
            
            print(f"🎯 使用モデル: {result.get('model_used', 'unknown')}")
            print(f"📊 信頼度: {result.get('confidence_score', 0.0)}")
            
            # 回答をデータベースに保存
            answer = Answer.objects.create(
                question=question,
                answer_text=result['answer'],
                confidence_score=result.get('confidence_score', 0.8),
                model_used=result.get('model_used', 'detailed-response')
            )
            
            # 会話履歴に保存
            ConversationManager.save_conversation(
                session_id=session_id,
                user=user,
                message_type='user',
                content=question_text
            )
            
            ConversationManager.save_conversation(
                session_id=session_id,
                user=user,
                message_type='ai',
                content=result['answer']
            )
            
            # 推奨補助金リスト
            recommended_subsidies = []
            if result.get('recommended_subsidies'):
                for subsidy in result['recommended_subsidies']:
                    recommended_subsidies.append({
                        'id': subsidy.id,
                        'name': subsidy.name,
                        'description': subsidy.description[:100] + '...' if len(subsidy.description) > 100 else subsidy.description,
                        'max_amount': subsidy.max_amount,
                        'subsidy_rate': subsidy.subsidy_rate
                    })
            
            response_data = {
                'answer': result['answer'],
                'recommended_subsidies': recommended_subsidies,
                'confidence_score': result.get('confidence_score', 0.8),
                'question_id': question.id,
                'answer_id': answer.id,
                'model_used': result.get('model_used', 'detailed-response'),
                'session_id': session_id
            }
            
            print(f"✅ 回答生成完了: 信頼度{result.get('confidence_score', 0.8):.0%}")
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"❌ Error in QuestionAPIView: {e}")
            print(f"📍 Traceback: {traceback.format_exc()}")
            
            # エラー時も適切な回答を返す
            error_response = {
                'answer': '申し訳ございません。一時的にシステムに問題が発生しています。しばらく時間をおいてから再度お試しください。',
                'recommended_subsidies': [],
                'confidence_score': 0.0,
                'model_used': 'error-fallback',
                'error': True
            }
            
            return JsonResponse(error_response, status=200)  # 500ではなく200で返す

# 既存のAPI関数
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

# ヘルスチェック機能
@csrf_exempt
def health_check(request):
    """ヘルスチェックエンドポイント"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })

# 詳細回答テスト用のエンドポイント
@api_view(['POST'])
def test_detailed_response(request):
    """詳細回答のテスト用エンドポイント"""
    try:
        data = request.data
        question_text = data.get('question', '')
        user_context = data.get('context', {})
        
        if not question_text:
            return Response({'error': '質問を入力してください'}, status=400)
        
        # 詳細回答サービスを使用
        if DetailedResponseService:
            detailed_service = DetailedResponseService()
            result = detailed_service.analyze_question(
                question_text=question_text,
                user_context=user_context
            )
        else:
            # フォールバック
            ai_service = AIAdvisorService()
            result = ai_service.analyze_question(
                question_text=question_text,
                user_context=user_context
            )
        
        return Response({
            'question': question_text,
            'answer': result['answer'],
            'model_used': result.get('model_used', 'unknown'),
            'confidence_score': result.get('confidence_score', 0.0),
            'recommended_subsidies': [
                {
                    'id': s.id,
                    'name': s.name
                } for s in result.get('recommended_subsidies', [])
            ]
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

# 既存の採択率分析関連のビューもここに含めることができます
# （AdoptionAnalysisView, adoption_statistics_api, 等）

# 採択率分析画面
class AdoptionAnalysisView(View):
    """採択率分析画面"""
    
    def get(self, request, subsidy_id=None):
        try:
            from .services import AdoptionAnalysisService
            analysis_service = AdoptionAnalysisService()
        except ImportError:
            # サービスが見つからない場合の対応
            analysis_service = None
        
        # 補助金一覧を取得
        subsidies = SubsidyType.objects.all()
        
        # 特定の補助金が指定されている場合
        selected_subsidy = None
        statistics_data = None
        tips_data = None
        
        if subsidy_id:
            selected_subsidy = get_object_or_404(SubsidyType, id=subsidy_id)
            
            if analysis_service:
                # 統計データを取得
                statistics_data = analysis_service.get_adoption_statistics(subsidy_id)
                # ティップスを取得
                tips_data = analysis_service.get_adoption_tips(subsidy_id)
        else:
            if analysis_service:
                # 全体統計を取得
                statistics_data = analysis_service.get_adoption_statistics()
        
        context = {
            'subsidies': subsidies,
            'selected_subsidy': selected_subsidy,
            'statistics_data': statistics_data,
            'tips_data': tips_data,
        }
        
        return render(request, 'advisor/adoption_analysis.html', context)

# 他の既存ビューも必要に応じて追加
@api_view(['GET'])
def adoption_statistics_api(request, subsidy_id=None):
    """採択統計データAPI"""
    try:
        from .services import AdoptionAnalysisService
        analysis_service = AdoptionAnalysisService()
        
        years = int(request.GET.get('years', 3))
        statistics = analysis_service.get_adoption_statistics(subsidy_id, years)
        
        return Response(statistics)
    except ImportError:
        return Response({'error': 'AdoptionAnalysisService が利用できません'}, status=500)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def adoption_tips_api(request, subsidy_id):
    """採択ティップスAPI"""
    try:
        from .services import AdoptionAnalysisService
        analysis_service = AdoptionAnalysisService()
        tips = analysis_service.get_adoption_tips(subsidy_id)
        
        return Response(tips)
    except ImportError:
        return Response({'error': 'AdoptionAnalysisService が利用できません'}, status=500)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def test_adoption_data(request):
    """採択率データのテスト用エンドポイント"""
    try:
        # データベースの状況を確認
        subsidies_count = SubsidyType.objects.count()
        statistics_count = AdoptionStatistics.objects.count()
        tips_count = AdoptionTips.objects.count()
        
        # サンプルデータ
        sample_subsidies = []
        for subsidy in SubsidyType.objects.all()[:5]:
            sample_subsidies.append({
                'id': subsidy.id,
                'name': subsidy.name,
                'description': subsidy.description or '',
                'max_amount': subsidy.max_amount
            })
        
        sample_statistics = []
        for stat in AdoptionStatistics.objects.all()[:5]:
            sample_statistics.append({
                'subsidy': stat.subsidy_type.name,
                'year': stat.year,
                'round': stat.round_number,
                'adoption_rate': stat.adoption_rate,
                'total_applications': stat.total_applications
            })
        
        # エラーチェック項目
        issues = []
        if subsidies_count == 0:
            issues.append('補助金データが存在しません。python manage.py load_subsidies を実行してください。')
        
        if statistics_count == 0:
            issues.append('採択統計データが存在しません。python manage.py load_adoption_data を実行してください。')
        
        return Response({
            'status': 'success' if len(issues) == 0 else 'warning',
            'data_counts': {
                'subsidies': subsidies_count,
                'statistics': statistics_count,
                'tips': tips_count
            },
            'sample_subsidies': sample_subsidies,
            'sample_statistics': sample_statistics,
            'issues': issues,
            'message': f'補助金{subsidies_count}件、統計{statistics_count}件、ティップス{tips_count}件のデータが存在します'
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)