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
import requests
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor


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
    
class EnhancedChatService:
    """強化されたチャット機能 - LLM連携、文脈認識、リアルタイム対応"""
    
    def __init__(self):
        self.dify_api_url = settings.DIFY_API_URL
        self.dify_api_key = settings.DIFY_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.dify_api_key}',
            'Content-Type': 'application/json'
        }
        
    def process_conversation(self, message, session_id, user_context=None):
        """
        文脈を考慮した高度な会話処理
        - 過去の会話履歴を分析
        - 質問の意図を自動判別
        - リアルタイムストリーミング対応
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
        self._save_conversation_turn(session_id, message, response)
        
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
    
    def _detect_question_intent(self, message, context):
        """AIを使用した質問意図の自動判別"""
        intent_patterns = {
            'search_subsidy': ['補助金', '助成金', '支援', 'どんな'],
            'application_process': ['申請', '手続き', 'やり方', '方法'],
            'eligibility_check': ['対象', '条件', '要件', '使える'],
            'timing_inquiry': ['いつ', 'タイミング', '期限', '時期'],
            'amount_inquiry': ['金額', 'いくら', '予算', '費用'],
            'success_tips': ['コツ', 'ポイント', '成功', 'アドバイス'],
            'follow_up': ['続き', 'さらに', 'もっと', '詳しく']
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
            
            dify_response = self._call_dify_streaming_api(enhanced_query)
            
            if dify_response:
                return self._process_streaming_response(dify_response, intent, context)
        
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

    def _call_dify_streaming_api(self, query_text):
        """Difyストリーミング API呼び出し（リアルタイム対応）"""
        try:
            request_data = {
                "inputs": {},
                "query": query_text,
                "response_mode": "streaming",  # ストリーミングモード
                "user": f"enhanced_chat_{uuid.uuid4().hex[:8]}"
            }
            
            url = f"{self.dify_api_url}/chat-messages"
            
            response = requests.post(
                url,
                headers=self.headers,
                json=request_data,
                timeout=30,
                stream=True  # ストリーミング対応
            )
            
            if response.status_code == 200:
                return self._handle_streaming_response(response)
            else:
                print(f"Dify Streaming API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Dify Streaming API error: {e}")
            return None
    
    def _handle_streaming_response(self, response):
        """ストリーミングレスポンスの処理"""
        accumulated_text = ""
        
        for line in response.iter_lines():
            if line:
                try:
                    # Server-Sent Events形式の処理
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data = json.loads(line_text[6:])
                        if 'answer' in data:
                            accumulated_text += data['answer']
                        elif 'event' in data and data['event'] == 'message_end':
                            break
                except json.JSONDecodeError:
                    continue
        
        return {'answer': accumulated_text} if accumulated_text else None
    
    def _save_conversation_turn(self, session_id, user_message, assistant_response):
        """会話ターンの保存"""
        timestamp = timezone.now()
        
        # ユーザーメッセージ
        ConversationHistory.objects.create(
            session_id=session_id,
            message_type='user',
            content=user_message,
            timestamp=timestamp
        )
        
        # アシスタント回答
        ConversationHistory.objects.create(
            session_id=session_id,
            message_type='assistant',
            content=assistant_response.get('answer', ''),
            metadata=json.dumps({
                'confidence_score': assistant_response.get('confidence_score', 0),
                'recommended_subsidies': assistant_response.get('recommended_subsidies', []),
                'model_used': assistant_response.get('model_used', 'enhanced_chat')
            }),
            timestamp=timestamp + timedelta(seconds=1)
        )


class SubsidyPredictionService:
    """AIによる補助金公募予測とスケジュール管理"""
    
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.prediction_cache = {}
        
    def predict_next_opportunities(self, months_ahead=12):
        """
        今後12ヶ月の補助金公募スケジュールを予測
        過去データから機械学習で予測
        """
        
        # 過去データの準備
        historical_data = self._prepare_historical_data()
        
        # 予測モデルの訓練
        if not self.model:
            self._train_prediction_model(historical_data)
        
        # 予測実行
        predictions = []
        current_date = timezone.now().date()
        
        for month_offset in range(1, months_ahead + 1):
            target_date = current_date + timedelta(days=30 * month_offset)
            
            month_predictions = self._predict_for_month(target_date, historical_data)
            predictions.extend(month_predictions)
        
        return self._format_prediction_results(predictions)
    
    def _prepare_historical_data(self):
        """過去の公募データを分析用に準備"""
        subsidies = SubsidyType.objects.all()
        historical_patterns = []
        
        for subsidy in subsidies:
            # 過去の公募パターンを分析
            pattern_data = self._extract_subsidy_patterns(subsidy)
            historical_patterns.extend(pattern_data)
        
        return pd.DataFrame(historical_patterns)
    
    def _extract_subsidy_patterns(self, subsidy):
        """個別補助金の公募パターンを抽出"""
        patterns = []
        
        # 基本的な年間パターン（実際のデータがない場合の推定）
        if "事業再構築" in subsidy.name:
            # 事業再構築補助金：年3-4回
            application_months = [1, 4, 7, 10]
        elif "ものづくり" in subsidy.name:
            # ものづくり補助金：年2-3回
            application_months = [2, 6, 10]
        elif "小規模事業者" in subsidy.name:
            # 小規模事業者持続化補助金：年4回
            application_months = [3, 6, 9, 12]
        elif "IT導入" in subsidy.name:
            # IT導入補助金：年2回
            application_months = [1, 7]
        else:
            # その他：年1-2回
            application_months = [4, 9]
        
        for month in application_months:
            patterns.append({
                'subsidy_id': subsidy.id,
                'subsidy_name': subsidy.name,
                'application_month': month,
                'budget_range': subsidy.max_amount,
                'target_business_type': subsidy.target_business_type,
                'application_difficulty': self._estimate_difficulty(subsidy),
                'success_rate': self._estimate_success_rate(subsidy),
                'preparation_time_weeks': self._estimate_preparation_time(subsidy)
            })
        
        return patterns
    
    def _train_prediction_model(self, historical_data):
        """機械学習モデルの訓練"""
        if len(historical_data) == 0:
            return
        
        # 特徴量の準備
        features = ['application_month', 'budget_range', 'application_difficulty', 'preparation_time_weeks']
        
        # カテゴリカル変数のエンコーディング
        categorical_features = ['subsidy_name', 'target_business_type']
        
        for feature in categorical_features:
            if feature in historical_data.columns:
                le = LabelEncoder()
                historical_data[f'{feature}_encoded'] = le.fit_transform(historical_data[feature].astype(str))
                self.label_encoders[feature] = le
                features.append(f'{feature}_encoded')
        
        # モデル訓練
        X = historical_data[features]
        y = historical_data['success_rate']
        
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X, y)
    
    def _predict_for_month(self, target_date, historical_data):
        """特定月の公募予測"""
        month = target_date.month
        predictions = []
        
        # 該当月に公募の可能性がある補助金を予測
        month_candidates = historical_data[historical_data['application_month'] == month]
        
        for _, row in month_candidates.iterrows():
            prediction = {
                'subsidy_name': row['subsidy_name'],
                'predicted_date': target_date,
                'confidence': self._calculate_prediction_confidence(row, target_date),
                'estimated_budget': row['budget_range'],
                'preparation_deadline': target_date - timedelta(weeks=row['preparation_time_weeks']),
                'success_probability': row['success_rate'],
                'recommendation_priority': self._calculate_priority_score(row)
            }
            predictions.append(prediction)
        
        return predictions
    
    def generate_prediction_calendar(self):
        """予測カレンダーの生成"""
        predictions = self.predict_next_opportunities()
        
        calendar_data = {}
        
        for pred in predictions:
            month_key = pred['predicted_date'].strftime('%Y-%m')
            
            if month_key not in calendar_data:
                calendar_data[month_key] = {
                    'month': pred['predicted_date'].strftime('%Y年%m月'),
                    'opportunities': [],
                    'total_opportunities': 0,
                    'high_priority_count': 0
                }
            
            calendar_data[month_key]['opportunities'].append(pred)
            calendar_data[month_key]['total_opportunities'] += 1
            
            if pred['recommendation_priority'] >= 0.7:
                calendar_data[month_key]['high_priority_count'] += 1
        
        return calendar_data
    
    def setup_alert_system(self, user_preferences):
        """アラート機能の設定"""
        alerts = []
        predictions = self.predict_next_opportunities(months_ahead=6)
        
        for pred in predictions:
            # 準備期限が近い場合のアラート
            days_to_prep_deadline = (pred['preparation_deadline'] - timezone.now().date()).days
            
            if days_to_prep_deadline <= 30 and pred['confidence'] >= 0.6:
                alerts.append({
                    'type': 'preparation_deadline',
                    'priority': 'high' if days_to_prep_deadline <= 14 else 'medium',
                    'message': f"{pred['subsidy_name']}の準備期限まで{days_to_prep_deadline}日です",
                    'subsidy_name': pred['subsidy_name'],
                    'deadline': pred['preparation_deadline'],
                    'action_required': '申請準備を開始してください'
                })
            
            # 高確率案件のアラート
            if pred['confidence'] >= 0.8 and pred['success_probability'] >= 0.3:
                alerts.append({
                    'type': 'high_opportunity',
                    'priority': 'medium',
                    'message': f"{pred['subsidy_name']}の公募が予想されます（信頼度: {pred['confidence']:.0%}）",
                    'subsidy_name': pred['subsidy_name'],
                    'predicted_date': pred['predicted_date'],
                    'action_required': '詳細情報の確認をお勧めします'
                })
        
        return sorted(alerts, key=lambda x: x['priority'] == 'high', reverse=True)
    
    def analyze_subsidy_trends(self):
        """補助金トレンド分析"""
        current_date = timezone.now().date()
        
        trends = {
            'seasonal_patterns': self._analyze_seasonal_patterns(),
            'budget_trends': self._analyze_budget_trends(),
            'competition_analysis': self._analyze_competition_trends(),
            'success_rate_trends': self._analyze_success_rate_trends(),
            'emerging_opportunities': self._identify_emerging_opportunities()
        }
        
        return trends
    
    def _analyze_seasonal_patterns(self):
        """季節パターンの分析"""
        monthly_activity = {month: 0 for month in range(1, 13)}
        
        subsidies = SubsidyType.objects.all()
        for subsidy in subsidies:
            patterns = self._extract_subsidy_patterns(subsidy)
            for pattern in patterns:
                monthly_activity[pattern['application_month']] += 1
        
        # 活発な月の特定
        peak_months = sorted(monthly_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'monthly_distribution': monthly_activity,
            'peak_months': [f"{month}月" for month, _ in peak_months],
            'peak_activity_score': sum(count for _, count in peak_months) / sum(monthly_activity.values())
        }
    
    def _calculate_prediction_confidence(self, subsidy_data, target_date):
        """予測信頼度の計算"""
        base_confidence = 0.7  # 基本信頼度
        
        # 過去の実績による調整
        if subsidy_data['success_rate'] > 0.2:
            base_confidence += 0.1
        
        # 季節性による調整
        current_month = target_date.month
        if current_month in [1, 4, 7, 10]:  # 四半期始まり
            base_confidence += 0.1
        
        return min(base_confidence, 0.95)
    
    def _calculate_priority_score(self, subsidy_data):
        """推奨優先度スコアの計算"""
        score = 0.0
        
        # 成功率
        score += subsidy_data['success_rate'] * 0.4
        
        # 予算規模
        if subsidy_data['budget_range'] > 1000:  # 1000万円以上
            score += 0.3
        elif subsidy_data['budget_range'] > 500:  # 500万円以上
            score += 0.2
        else:
            score += 0.1
        
        # 申請難易度（逆算）
        score += (5 - subsidy_data['application_difficulty']) * 0.1
        
        # 準備時間
        if subsidy_data['preparation_time_weeks'] <= 4:
            score += 0.2
        elif subsidy_data['preparation_time_weeks'] <= 8:
            score += 0.1
        
        return min(score, 1.0)
    
    def _estimate_difficulty(self, subsidy):
        """申請難易度の推定（1-5スケール）"""
        if subsidy.max_amount > 5000:  # 5000万円以上
            return 5  # 非常に難しい
        elif subsidy.max_amount > 1000:  # 1000万円以上
            return 4  # 難しい
        elif subsidy.max_amount > 500:  # 500万円以上
            return 3  # 普通
        elif subsidy.max_amount > 100:  # 100万円以上
            return 2  # やや易しい
        else:
            return 1  # 易しい
    
    def _estimate_success_rate(self, subsidy):
        """成功率の推定"""
        if "小規模" in subsidy.name:
            return 0.4  # 比較的高い
        elif "IT導入" in subsidy.name:
            return 0.35
        elif "ものづくり" in subsidy.name:
            return 0.3
        elif "事業再構築" in subsidy.name:
            return 0.2  # 競争激しい
        else:
            return 0.25  # 平均的
    
    def _estimate_preparation_time(self, subsidy):
        """準備期間の推定（週単位）"""
        if subsidy.max_amount > 1000:  # 1000万円以上
            return 12  # 3ヶ月
        elif subsidy.max_amount > 500:  # 500万円以上
            return 8   # 2ヶ月
        else:
            return 4   # 1ヶ月