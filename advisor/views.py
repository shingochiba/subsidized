# advisor/views.py - is_activeフィールドエラー修正版

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, date, timedelta
import json
import uuid
import traceback
import random

# モデルのインポート
from .models import (
    Question, Answer, SubsidyType, ConversationHistory,
    AdoptionStatistics, AdoptionTips, UserApplicationHistory
)

# サービスのインポート
from .services import AIAdvisorService, ConversationManager

# 条件付きインポート
try:
    from .services import AdoptionAnalysisService
except ImportError:
    AdoptionAnalysisService = None
    print("⚠️ AdoptionAnalysisService が見つかりません。")

try:
    from .services.enhanced_adoption_analysis import EnhancedAdoptionAnalysisService
except ImportError:
    EnhancedAdoptionAnalysisService = None
    print("⚠️ EnhancedAdoptionAnalysisService が見つかりません。基本機能を使用します。")

try:
    from .services.detailed_response_service import DetailedResponseService
except ImportError:
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
                session_id=session_id,
                business_type=user_context.get('business_type', ''),
                company_size=user_context.get('company_size', '')
            )
            
            # 回答生成（サービス優先順位: Detailed > AI）
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
                ai_model_used=result.get('model_used', 'detailed-response')
            )
            
            # 推奨補助金を関連付け
            if result.get('recommended_subsidies'):
                answer.recommended_subsidies.set(result['recommended_subsidies'])
            
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
                        'description': subsidy.description[:100] + '...' if len(subsidy.description or '') > 100 else subsidy.description,
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
            
            return JsonResponse(error_response, status=200)


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


# =============================================================================
# 🆕 採択率分析機能（is_activeフィールド修正版）
# =============================================================================

class AdoptionAnalysisView(View):
    """採択率分析メインビュー（修正版）"""
    
    def get(self, request, subsidy_id=None):
        # 🔧 修正: is_activeフィールドを削除し、全補助金を取得
        context = {
            'subsidies': SubsidyType.objects.all(),  # is_active=True を削除
            'selected_subsidy': None
        }
        
        # URLから特定の補助金が指定されている場合
        if subsidy_id:
            context['selected_subsidy'] = get_object_or_404(SubsidyType, id=subsidy_id)
        
        return render(request, 'advisor/adoption_analysis.html', context)


@api_view(['GET'])
def adoption_statistics_api(request, subsidy_id=None):
    """採択率統計API（JSON Serializable修正版）"""
    try:
        print(f"📊 采択率統計API呼び出し: subsidy_id={subsidy_id}")
        
        if subsidy_id:
            # 特定補助金の統計
            subsidy = get_object_or_404(SubsidyType, id=subsidy_id)
            
            # 統計データを直接取得
            stats = AdoptionStatistics.objects.filter(
                subsidy_type=subsidy
            ).order_by('-year', '-round_number')
            
            if not stats.exists():
                # データが存在しない場合のダミーデータ
                dummy_data = {
                    'subsidy_info': {
                        'id': subsidy.id,
                        'name': subsidy.name,
                        'description': subsidy.description or '',
                        'target_business': subsidy.target_business or ''
                    },
                    'yearly_summary': {
                        2024: {
                            'adoption_rate': 60.0,
                            'total_applications': 1000,
                            'total_adoptions': 600,
                            'rounds': 1
                        },
                        2023: {
                            'adoption_rate': 58.0,
                            'total_applications': 950,
                            'total_adoptions': 551,
                            'rounds': 1
                        }
                    },
                    'detailed_statistics': [
                        {
                            'year': 2024,
                            'round': 1,
                            'total_applications': 1000,
                            'total_adoptions': 600,
                            'adoption_rate': 60.0,
                            'small_business_rate': 65.0,
                            'medium_business_rate': 55.0
                        },
                        {
                            'year': 2023,
                            'round': 1,
                            'total_applications': 950,
                            'total_adoptions': 551,
                            'adoption_rate': 58.0,
                            'small_business_rate': 63.0,
                            'medium_business_rate': 53.0
                        }
                    ],
                    'message': 'サンプルデータです。実際のデータを投入してください。'
                }
                print(f"🔧 ダミーデータを返します: {subsidy.name}")
                return Response({
                    'status': 'success',
                    'data': dummy_data,
                    'timestamp': datetime.now().isoformat()
                })
            
            # 実際のデータが存在する場合
            yearly_summary = {}
            detailed_stats = []
            
            for stat in stats:
                year = stat.year
                if year not in yearly_summary:
                    yearly_summary[year] = {
                        'adoption_rate': 0,
                        'total_applications': 0,
                        'total_adoptions': 0,
                        'rounds': 0
                    }
                
                yearly_summary[year]['total_applications'] += stat.total_applications
                yearly_summary[year]['total_adoptions'] += stat.total_adoptions
                yearly_summary[year]['rounds'] += 1
                
                detailed_stats.append({
                    'year': stat.year,
                    'round': stat.round_number,
                    'total_applications': stat.total_applications,
                    'total_adoptions': stat.total_adoptions,
                    'adoption_rate': float(stat.adoption_rate),
                    'small_business_rate': float(stat.small_business_adoption_rate),
                    'medium_business_rate': float(stat.medium_business_adoption_rate)
                })
            
            # 年度別採択率を計算
            for year_data in yearly_summary.values():
                if year_data['total_applications'] > 0:
                    year_data['adoption_rate'] = round(
                        year_data['total_adoptions'] / year_data['total_applications'] * 100, 1
                    )
            
            response_data = {
                'subsidy_info': {
                    'id': subsidy.id,
                    'name': subsidy.name,
                    'description': subsidy.description or '',
                    'target_business': subsidy.target_business or ''
                },
                'yearly_summary': yearly_summary,
                'detailed_statistics': detailed_stats,
                'analysis_date': datetime.now().isoformat()
            }
            
        else:
            # 全補助金の統計
            all_subsidies = SubsidyType.objects.all()
            overall_data = {}
            
            for subsidy in all_subsidies:
                stats = AdoptionStatistics.objects.filter(subsidy_type=subsidy)
                
                if stats.exists():
                    total_apps = sum(stat.total_applications for stat in stats)
                    total_adoptions = sum(stat.total_adoptions for stat in stats)
                    avg_rate = (total_adoptions / total_apps * 100) if total_apps > 0 else 0
                    
                    overall_data[subsidy.name] = {
                        'subsidy_info': {
                            'id': subsidy.id,
                            'name': subsidy.name,
                            'description': subsidy.description or '',
                            'target_business': subsidy.target_business or ''
                        },
                        'adoption_rate': round(avg_rate, 1),
                        'total_applications': total_apps,
                        'total_adoptions': total_adoptions,
                        'data_points': stats.count()
                    }
                else:
                    # データがない場合のデフォルト値
                    overall_data[subsidy.name] = {
                        'subsidy_info': {
                            'id': subsidy.id,
                            'name': subsidy.name,
                            'description': subsidy.description or '',
                            'target_business': subsidy.target_business or ''
                        },
                        'adoption_rate': 50.0,
                        'total_applications': 0,
                        'total_adoptions': 0,
                        'data_points': 0,
                        'note': 'データ不足のため推定値'
                    }
            
            response_data = {
                'overall_stats': {
                    'adoption_rate': 55.0,  # 全体平均の推定値
                    'total_applications': sum(item['total_applications'] for item in overall_data.values()),
                    'total_adoptions': sum(item['total_adoptions'] for item in overall_data.values()),
                    'trend': 'stable'
                },
                'subsidy_breakdown': overall_data,
                'analysis_date': datetime.now().isoformat()
            }
        
        print(f"✅ 統計データ返却成功")
        return Response({
            'status': 'success',
            'data': response_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ 統計API エラー: {e}")
        import traceback
        traceback.print_exc()
        
        # エラー時も有用な情報を返す
        error_response = {
            'status': 'error',
            'message': str(e),
            'data': {
                'overall_stats': {
                    'adoption_rate': 50.0,
                    'total_applications': 0,
                    'total_adoptions': 0,
                    'trend': 'unknown'
                },
                'note': 'エラーが発生しました。デフォルト値を表示しています。'
            }
        }
        
        return Response(error_response, status=200)  # 500ではなく200で返してフロントエンドのエラーを防ぐ


@api_view(['GET'])
def adoption_tips_api(request, subsidy_id):
    """採択率向上ティップスAPI（強化版）"""
    try:
        subsidy = get_object_or_404(SubsidyType, id=subsidy_id)
        
        # 強化サービスが利用可能な場合
        if EnhancedAdoptionAnalysisService:
            service = EnhancedAdoptionAnalysisService()
            user_profile = _get_user_profile(request)
            tips = service.get_strategic_tips(subsidy, user_profile)
        
        # フォールバック: 基本サービス
        elif AdoptionAnalysisService:
            service = AdoptionAnalysisService()
            tips = service.get_adoption_tips(subsidy_id)
        
        # デフォルトティップス
        else:
            tips = _get_default_tips()
        
        return Response({
            'status': 'success',
            'data': tips,
            'subsidy_name': subsidy.name
        })
    
    except Exception as e:
        print(f"💡 ティップスAPI エラー: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AdoptionProbabilityView(View):
    """採択確率計算API（強化版）"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # リクエストデータの検証
            required_fields = ['business_type', 'company_size']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'status': 'error',
                        'message': f'{field} is required'
                    }, status=400)
            
            # 強化サービスが利用可能な場合
            if EnhancedAdoptionAnalysisService:
                service = EnhancedAdoptionAnalysisService()
                result = service.calculate_adoption_probability(
                    user_profile=data,
                    subsidy_id=data.get('subsidy_id')
                )
            
            # フォールバック: 基本計算
            else:
                result = _calculate_basic_probability(data)
            
            return JsonResponse({
                'status': 'success',
                'probability': result['probability'],
                'assessment': result['assessment'],
                'improvement_suggestions': result['improvement_suggestions'],
                'calculation_details': result.get('calculation_details', {})
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        
        except Exception as e:
            print(f"🧮 確率計算API エラー: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


@api_view(['GET'])
def industry_comparison(request):
    """業種別比較分析API（強化版）"""
    try:
        # 強化サービスが利用可能な場合
        if EnhancedAdoptionAnalysisService:
            service = EnhancedAdoptionAnalysisService()
            comparison_data = service.get_industry_comparison()
        
        # フォールバック: 基本データ
        else:
            comparison_data = _get_basic_industry_comparison()
        
        return Response({
            'status': 'success',
            'data': comparison_data,
            'analysis_date': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"🏭 業種比較API エラー: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@api_view(['GET'])
def user_application_history(request):
    """ユーザーの申請履歴API（強化版）"""
    try:
        # 強化サービスが利用可能な場合
        if EnhancedAdoptionAnalysisService:
            service = EnhancedAdoptionAnalysisService()
            history_analysis = service.get_user_history_analysis(request.user)
        
        # フォールバック: 基本履歴
        else:
            history_analysis = _get_basic_user_history(request.user)
        
        return Response({
            'status': 'success',
            'data': history_analysis
        })
    
    except Exception as e:
        print(f"👤 ユーザー履歴API エラー: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ApplicationHistoryView(View):
    """申請履歴管理ビュー（強化版）"""
    
    @method_decorator(login_required)
    def get(self, request):
        """申請履歴画面を表示"""
        history = UserApplicationHistory.objects.filter(
            user=request.user
        ).select_related('subsidy_type').order_by('-application_date')
        
        context = {
            'application_history': history,
            'subsidies': SubsidyType.objects.all(),  # 🔧 修正: is_active=True を削除
            'total_applications': history.count(),
            'adopted_count': history.filter(status='adopted').count(),
            'success_rate': (
                history.filter(status='adopted').count() / history.count() * 100
                if history.exists() else 0
            )
        }
        
        return render(request, 'advisor/application_history.html', context)
    
    @method_decorator(login_required)
    def post(self, request):
        """新規申請履歴を登録"""
        try:
            data = json.loads(request.body)
            
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
            print(f"📝 申請履歴登録エラー: {e}")
            return JsonResponse({'error': 'システムエラーが発生しました'}, status=500)


# =============================================================================
# 🆕 補助金予測機能
# =============================================================================

class SubsidyPredictionView(View):
    """補助金予測カレンダー画面"""
    
    def get(self, request):
        """予測カレンダーページを表示"""
        context = {
            'calendar_data': {},
            'upcoming_subsidies': [],
            'subsidies': SubsidyType.objects.all(),
            'current_year': datetime.now().year,
            'current_date': date.today(),
            'message': '公募予測機能は準備中です。しばらくお待ちください。'
        }
        
        try:
            return render(request, 'advisor/subsidy_prediction.html', context)
        except:
            # テンプレートが存在しない場合の簡易レスポンス
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>公募予測 - 補助金アドバイザー</title>
                <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-body text-center">
                                    <h4 class="card-title">
                                        <i class="fas fa-calendar-alt"></i> 公募予測機能
                                    </h4>
                                    <p class="card-text">この機能は現在準備中です。</p>
                                    <div class="mt-4">
                                        <a href="/" class="btn btn-primary">
                                            <i class="fas fa-home"></i> ホームに戻る
                                        </a>
                                        <a href="/analysis/" class="btn btn-outline-secondary">
                                            <i class="fas fa-chart-line"></i> 採択率分析へ
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            return HttpResponse(html_content)


# 予測機能のスタブAPI群（将来の拡張用）
@api_view(['GET'])
def prediction_calendar_api(request):
    """予測カレンダーAPI（準備中）"""
    return Response({'message': '準備中です'})

@api_view(['GET'])
def upcoming_subsidies_api(request):
    """今後の補助金API（準備中）"""
    return Response({'message': '準備中です'})

@api_view(['GET'])
def subsidy_trend_api(request, subsidy_id):
    """補助金トレンドAPI（準備中）"""
    return Response({'message': '準備中です'})

@method_decorator(csrf_exempt, name='dispatch')
class GeneratePredictionsView(View):
    """予測生成API（準備中）"""
    def post(self, request):
        return JsonResponse({'message': '準備中です'})

@api_view(['GET'])
def prediction_summary_api(request):
    """予測サマリーAPI（準備中）"""
    return Response({'message': '準備中です'})


# =============================================================================
# 🆕 デバッグ・テスト用エンドポイント
# =============================================================================

@api_view(['GET'])
def test_adoption_data(request):
    """採択率データのテスト用API"""
    try:
        stats = AdoptionStatistics.objects.all().count()
        tips = AdoptionTips.objects.all().count()
        subsidies = SubsidyType.objects.all().count()
        
        # サンプルデータの生成状況確認
        sample_stats = list(AdoptionStatistics.objects.select_related('subsidy_type')
                          .values('subsidy_type__name', 'year', 'adoption_rate')
                          .order_by('-year', 'subsidy_type__name')[:10])
        
        return Response({
            'status': 'success',
            'data_counts': {
                'adoption_statistics': stats,
                'adoption_tips': tips,
                'subsidy_types': subsidies
            },
            'sample_statistics': sample_stats,
            'test_timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)


@api_view(['POST'])
def create_sample_adoption_data(request):
    """サンプル採択率データ生成API"""
    if not request.user.is_staff:
        return Response({
            'status': 'error',
            'message': 'Staff access required'
        }, status=403)
    
    try:
        subsidies = SubsidyType.objects.all()
        
        if not subsidies.exists():
            return Response({
                'status': 'error',
                'message': '補助金データが存在しません。先にload_subsidiesコマンドを実行してください。'
            }, status=400)
        
        created_count = 0
        
        for subsidy in subsidies:
            for year in [2023, 2024]:
                for round_num in [1, 2]:
                    # 既存データがある場合はスキップ
                    if AdoptionStatistics.objects.filter(
                        subsidy_type=subsidy, 
                        year=year, 
                        round_number=round_num
                    ).exists():
                        continue
                    
                    # ランダムな統計データを生成
                    total_apps = random.randint(500, 2000)
                    adoption_rate = random.uniform(35.0, 75.0)
                    total_adoptions = int(total_apps * adoption_rate / 100)
                    
                    stat = AdoptionStatistics.objects.create(
                        subsidy_type=subsidy,
                        year=year,
                        round_number=round_num,
                        total_applications=total_apps,
                        total_adoptions=total_adoptions,
                        adoption_rate=round(adoption_rate, 1),
                        small_business_applications=int(total_apps * 0.6),
                        small_business_adoptions=int(total_adoptions * 0.65),
                        medium_business_applications=int(total_apps * 0.4),
                        medium_business_adoptions=int(total_adoptions * 0.35)
                    )
                    
                    created_count += 1
        
        return Response({
            'status': 'success',
            'message': f'サンプル統計データ {created_count}件を作成しました',
            'created_count': created_count
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@api_view(['GET'])
def system_status(request):
    """システム全体の状況確認API"""
    try:
        status_info = {
            'services': {},
            'data_status': {},
            'system_info': {
                'timestamp': datetime.now().isoformat(),
                'dify_configured': bool(getattr(settings, 'DIFY_API_KEY', None)),
                'dify_url': getattr(settings, 'DIFY_API_URL', 'Not configured')
            }
        }
        
        # サービスの可用性チェック
        status_info['services']['enhanced_adoption'] = {
            'available': EnhancedAdoptionAnalysisService is not None,
            'description': '強化採択率分析サービス'
        }
        
        status_info['services']['detailed_response'] = {
            'available': DetailedResponseService is not None,
            'description': '詳細回答サービス'
        }
        
        status_info['services']['ai_advisor'] = {
            'available': True,
            'description': '基本AIアドバイザー'
        }
        
        # データ状況チェック
        status_info['data_status'] = {
            'subsidies': {
                'count': SubsidyType.objects.count(),
                'latest': SubsidyType.objects.order_by('-created_at').first().name if SubsidyType.objects.exists() else None
            },
            'statistics': {
                'count': AdoptionStatistics.objects.count(),
                'latest_year': AdoptionStatistics.objects.order_by('-year').first().year if AdoptionStatistics.objects.exists() else None
            },
            'tips': {
                'count': AdoptionTips.objects.count(),
                'categories': list(AdoptionTips.objects.values_list('category', flat=True).distinct())
            }
        }
        
        # 機能利用可能性
        status_info['features_available'] = {
            'adoption_analysis': status_info['data_status']['statistics']['count'] > 0,
            'strategic_tips': status_info['data_status']['tips']['count'] > 0,
            'probability_calculation': status_info['data_status']['statistics']['count'] > 0,
            'industry_comparison': status_info['data_status']['statistics']['count'] > 0,
            'enhanced_features': EnhancedAdoptionAnalysisService is not None
        }
        
        return Response(status_info)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'error_message': str(e),
            'error_type': type(e).__name__
        }, status=500)


@api_view(['GET'])
def chat_service_status(request):
    """チャットサービスの状況確認"""
    try:
        status_info = {
            'services': {
                'detailed_response': DetailedResponseService is not None,
                'ai_advisor': True,
                'enhanced_adoption': EnhancedAdoptionAnalysisService is not None
            },
            'data_status': {
                'subsidies': SubsidyType.objects.count(),
                'statistics': AdoptionStatistics.objects.count(),
                'tips': AdoptionTips.objects.count()
            },
            'test_questions': [
                {
                    'question': 'IT導入補助金の採択率を教えて',
                    'intent': 'adoption_rate',
                    'description': '採択率統計の表示テスト'
                },
                {
                    'question': 'ものづくり補助金の申請方法は？',
                    'intent': 'application_process',
                    'description': '申請プロセスの説明テスト'
                },
                {
                    'question': '採択率を上げるコツを教えて',
                    'intent': 'success_tips',
                    'description': 'ティップス表示のテスト'
                }
            ],
            'urls': {
                'adoption_analysis': '/analysis/',
                'api_statistics': '/api/adoption-statistics/',
                'chat': '/'
            }
        }
        
        return Response(status_info)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'details': str(e)
        }, status=500)


# ヘルスチェック機能
@csrf_exempt
def health_check(request):
    """ヘルスチェックエンドポイント"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '2.0.0'
    })


# =============================================================================
# ヘルパー関数群
# =============================================================================

def _get_user_profile(request):
    """リクエストからユーザープロファイルを取得"""
    return getattr(request.user, 'profile', None) if request.user.is_authenticated else None

def _generate_dummy_statistics(subsidy_id=None):
    """ダミー統計データの生成"""
    if subsidy_id:
        subsidy = get_object_or_404(SubsidyType, id=subsidy_id)
        return {
            'subsidy_info': {
                'id': subsidy.id,
                'name': subsidy.name,
                'description': subsidy.description or ''
            },
            'yearly_summary': {
                2024: {'adoption_rate': 60.0, 'total_applications': 1000},
                2023: {'adoption_rate': 58.0, 'total_applications': 950}
            },
            'message': 'ダミーデータです'
        }
    else:
        return {
            'overall_stats': {
                'adoption_rate': 55.0,
                'total_applications': 5000,
                'trend': 'stable'
            },
            'message': 'ダミーデータです'
        }

def _get_default_tips():
    """デフォルトティップスの取得"""
    return {
        '事前準備': [
            {
                'title': '十分な準備期間を確保する',
                'content': '申請には最低2-3ヶ月の準備期間が必要です。',
                'importance': 4,
                'effective_timing': '申請検討時'
            }
        ],
        '申請書作成': [
            {
                'title': '具体的な数値目標を設定する',
                'content': '曖昧な表現ではなく、具体的な改善効果を数値で示すことが重要です。',
                'importance': 5,
                'effective_timing': '申請書作成時'
            }
        ]
    }

def _calculate_basic_probability(data):
    """基本的な採択確率計算"""
    probability = 50.0  # ベース確率
    
    # 業種による調整
    business_type = data.get('business_type', '')
    if 'IT' in business_type:
        probability += 10
    elif '製造' in business_type:
        probability += 8
    
    # 企業規模による調整
    company_size = data.get('company_size', '')
    if '小規模' in company_size:
        probability += 5
    
    return {
        'probability': min(85.0, max(15.0, probability)),
        'assessment': {
            'level': 'good' if probability >= 60 else 'fair',
            'message': '基本計算による推定値です'
        },
        'improvement_suggestions': ['専門家への相談をお勧めします']
    }

def _get_basic_industry_comparison():
    """基本的な業種別比較データ"""
    return {
        '製造業': {'adoption_rate': 65.0, 'difficulty': 'medium'},
        'IT・情報通信業': {'adoption_rate': 70.0, 'difficulty': 'low'},
        'サービス業': {'adoption_rate': 55.0, 'difficulty': 'medium'},
        '建設業': {'adoption_rate': 60.0, 'difficulty': 'medium'}
    }

def _get_basic_user_history(user):
    """基本的なユーザー履歴分析"""
    history = UserApplicationHistory.objects.filter(user=user)
    
    return {
        'total_applications': history.count(),
        'adopted_count': history.filter(status='adopted').count(),
        'success_rate': 0.0,
        'message': '履歴が不足しています' if history.count() == 0 else '基本分析です'
    }


# テスト用エンドポイント
@api_view(['POST'])
def test_enhanced_chat(request):
    """強化されたチャット機能のテスト用エンドポイント"""
    try:
        data = request.data
        question_text = data.get('question', '')
        user_context = data.get('context', {})
        
        if not question_text:
            return Response({'error': '質問を入力してください'}, status=400)
        
        print(f"🧪 テスト質問: {question_text}")
        
        # 利用可能な最高のサービスを使用
        if DetailedResponseService:
            service = DetailedResponseService()
            result = service.analyze_question(question_text, user_context)
        else:
            service = AIAdvisorService()
            result = service.analyze_question(question_text, user_context)
        
        return Response({
            'question': question_text,
            'answer': result['answer'],
            'recommended_subsidies': [
                {'id': s.id, 'name': s.name} 
                for s in result.get('recommended_subsidies', [])
            ],
            'analysis': {
                'confidence_score': result.get('confidence_score', 0.0),
                'model_used': result.get('model_used', 'unknown')
            }
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)