# advisor/views.py - 完全統合修正版
# 補助金アドバイザーのビュー関数

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q, Count, Avg, Max, Min
from datetime import timedelta, datetime
import json
import uuid
import logging
from .models import ConversationHistory
from .services.context_aware_ai_advisor import ContextAwareAIAdvisorService
# モデルのインポート
from .models import (
    SubsidyType, Answer, ConversationHistory, AdoptionStatistics, 
    AdoptionTips
)
from django.utils.decorators import method_decorator
from django.views import View

logger = logging.getLogger(__name__)

# 新しいモデル（マイグレーション後に利用可能）
try:
    from .models import SubsidyPrediction, UserAlert, TrendAnalysis
    NEW_MODELS_AVAILABLE = True
except ImportError:
    SubsidyPrediction = None
    UserAlert = None
    TrendAnalysis = None
    NEW_MODELS_AVAILABLE = False

# サービスのインポート
from .services import AIAdvisorService, ConversationManager

# 新しいサービス（段階的に利用可能）
try:
    from .services.enhanced_chat_service import EnhancedChatService
    from .services.subsidy_prediction_service import SubsidyPredictionService
    ENHANCED_SERVICES_AVAILABLE = True
except ImportError:
    EnhancedChatService = None
    SubsidyPredictionService = None
    ENHANCED_SERVICES_AVAILABLE = False

# ========== メインページ・基本ビュー ==========

def index(request):
    """メインページ - 補助金一覧と基本統計を表示"""
    try:
        subsidies = SubsidyType.objects.all()
        
        # 基本統計
        basic_stats = {
            'total_subsidies': subsidies.count(),
            'total_conversations': ConversationHistory.objects.count(),
            'active_sessions': ConversationHistory.objects.values('session_id').distinct().count(),
        }
        
        # 最新の会話履歴
        recent_conversations = ConversationHistory.objects.filter(
            message_type='user'
        ).order_by('-timestamp')[:5]
        
        context = {
            'page_title': '補助金アドバイザー',
            'subsidies': subsidies,
            'recent_conversations': recent_conversations,
            'basic_stats': basic_stats,
            'enhanced_services_available': ENHANCED_SERVICES_AVAILABLE,
            'new_models_available': NEW_MODELS_AVAILABLE,
        }
        
        return render(request, 'advisor/index.html', context)
        
    except Exception as e:
        print(f"Index view error: {e}")
        context = {
            'page_title': '補助金アドバイザー',
            'error_message': 'データの取得中にエラーが発生しました。',
        }
        return render(request, 'advisor/index.html', context)

def chat_interface(request):
    """チャットインターフェース - 統一版（強化版を使用）"""
    context = {
        'page_title': '補助金AI相談',
        'description': 'AIとの自然な対話で最適な補助金を見つけます',
        'chat_type': 'enhanced',
        'enhanced_available': True,
        'is_unified': True
    }
    return render(request, 'advisor/enhanced_chat.html', context)

def enhanced_chat_interface(request):
    """強化されたチャットインターフェース"""
    context = {
        'page_title': '補助金AI相談',
        'description': 'AIとの自然な対話で最適な補助金を見つけます',
        'chat_type': 'enhanced',
        'features': [
            '文脈を理解した継続的な対話',
            'リアルタイム回答生成',
            '過去の会話履歴を考慮',
            '意図認識による最適化回答',
            '信頼度スコア表示',
            '推奨補助金の自動提案'
        ],
        'enhanced_available': True,
        'is_unified': True
    }
    return render(request, 'advisor/enhanced_chat.html', context)

# ========== API エンドポイント ==========

@csrf_exempt
def analyze_question(request):
    """質問分析API - 後方互換性用"""
    return enhanced_chat_api(request)

# advisor/views.py の enhanced_chat_api 関数を以下で置き換え

@csrf_exempt
def enhanced_chat_api(request):
    """統一チャットAPI - 文脈対応版"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        # リクエストデータの取得
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        conversation_context = data.get('conversation_context', [])
        context_string = data.get('context', '')
        
        print(f"受信メッセージ: {message}")
        print(f"セッションID: {session_id}")
        print(f"会話文脈: {conversation_context}")
        print(f"文脈文字列: {context_string}")
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'メッセージが入力されていません'
            }, status=400)
        
        # メッセージ長の制限
        if len(message) > 1000:
            return JsonResponse({
                'success': False,
                'error': 'メッセージは1000文字以内で入力してください'
            }, status=400)
        
        # 会話履歴を保存（ユーザーメッセージ）
        user_conversation = ConversationHistory.objects.create(
            session_id=session_id,
            content=message,
            message_type='user',
            timestamp=timezone.now()
        )
        
        # 文脈を考慮したプロンプトを構築
        enhanced_message = build_contextual_prompt(message, conversation_context, context_string)
        print(f"拡張メッセージ: {enhanced_message}")
        
        # AIレスポンスを生成
        advisor = AIAdvisorService()
        response = advisor.analyze_question(enhanced_message, {
            'session_id': session_id,
            'conversation_context': conversation_context,
            'original_message': message
        })
        
        # AIレスポンスを保存
        ai_conversation = ConversationHistory.objects.create(
            session_id=session_id,
            content=response.get('answer', ''),
            message_type='assistant',
            timestamp=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'response': response.get('answer', ''),
            'session_id': session_id,
            'category': response.get('category', ''),
            'suggestions': response.get('suggestions', []),
            'context_used': bool(conversation_context or context_string)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Enhanced chat error: {e}")
        return JsonResponse({
            'success': False,
            'error': f'チャット処理中にエラーが発生しました: {str(e)}'
        }, status=500)

def build_contextual_prompt(current_message, conversation_context, context_string):
    """文脈を考慮したプロンプトを構築"""
    
    # 基本プロンプト
    base_prompt = f"ユーザーからの質問: {current_message}\n\n"
    
    # 会話の文脈がある場合
    if conversation_context:
        base_prompt += "【会話の流れ】\n"
        for msg in conversation_context[-3:]:  # 最新3件のみ使用
            if msg.get('role') == 'user':
                base_prompt += f"ユーザー: {msg.get('content', '')}\n"
            elif msg.get('role') == 'assistant':
                base_prompt += f"AI: {msg.get('content', '')[:100]}...\n"  # 長い回答は短縮
        
        base_prompt += "\n【重要】上記の会話の流れを踏まえて、現在のユーザーの質問に答えてください。\n"
        
        # 特定のパターンを検出
        if len(conversation_context) >= 2:
            last_user_msg = None
            last_ai_msg = None
            
            for msg in reversed(conversation_context):
                if msg.get('role') == 'user' and last_user_msg is None:
                    last_user_msg = msg.get('content', '').lower()
                elif msg.get('role') == 'assistant' and last_ai_msg is None:
                    last_ai_msg = msg.get('content', '').lower()
                
                if last_user_msg and last_ai_msg:
                    break
            
            # IT導入補助金の採択率に関する質問の検出
            if (last_ai_msg and 'it導入補助金' in last_ai_msg and 
                current_message and ('採択率' in current_message or '率' in current_message or 
                                   '上げる' in current_message or '高める' in current_message)):
                base_prompt += "\n【特別指示】ユーザーはIT導入補助金の採択率を上げる方法について質問しています。IT導入補助金特有の採択率向上のコツを具体的に教えてください。\n"
    
    elif context_string:
        base_prompt += f"【会話の文脈】\n{context_string}\n\n上記の文脈を考慮して回答してください。\n"
    
    base_prompt += "\n補助金の専門家として、具体的で実用的なアドバイスを提供してください。"
    
    return base_prompt
def conversation_history(request, session_id):
    """会話履歴取得API"""
    try:
        limit = int(request.GET.get('limit', 50))
        
        history = ConversationHistory.objects.filter(
            session_id=session_id
        ).order_by('-timestamp')[:limit]
        
        if not history.exists():
            return JsonResponse({
                'success': False,
                'error': '指定されたセッションの履歴が見つかりません'
            }, status=404)
        
        history_data = []
        for message in history:
            history_data.append({
                'id': message.id,
                'message_type': message.message_type,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'user': message.user.username if message.user else 'ゲスト',
            })
        
        return JsonResponse({
            'success': True,
            'history': list(reversed(history_data)),
            'session_id': session_id,
            'total_messages': len(history_data)
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'limitパラメータは数値である必要があります'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'履歴取得中にエラーが発生しました: {str(e)}'
        }, status=500)

def subsidy_list(request):
    """補助金一覧API"""
    try:
        # フィルタリングパラメータ
        category = request.GET.get('category', '')
        business_type = request.GET.get('business_type', '')
        search = request.GET.get('search', '')
        
        # 基本クエリ
        subsidies = SubsidyType.objects.all()
        
        # フィルタリング
        if category:
            subsidies = subsidies.filter(category__icontains=category)
        if business_type:
            subsidies = subsidies.filter(target_business_type__icontains=business_type)
        if search:
            subsidies = subsidies.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(requirements__icontains=search)
            )
        
        subsidies = subsidies.order_by('-max_amount', 'name')
        
        # JSON レスポンス
        if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
            subsidy_data = []
            for subsidy in subsidies:
                subsidy_data.append({
                    'id': subsidy.id,
                    'name': subsidy.name,
                    'description': subsidy.description,
                    'max_amount': float(subsidy.max_amount) if subsidy.max_amount else 0,
                    'target_business_type': subsidy.target_business_type,
                    'requirements': subsidy.requirements,
                })
            
            return JsonResponse({
                'success': True,
                'subsidies': subsidy_data,
                'count': len(subsidy_data)
            })
        
        # HTML レスポンス
        stats = {
            'total_count': subsidies.count(),
            'avg_amount': subsidies.aggregate(avg=Avg('max_amount'))['avg'] or 0,
            'max_amount': subsidies.aggregate(max=Max('max_amount'))['max'] or 0,
        }
        
        context = {
            'subsidies': subsidies,
            'stats': stats,
            'filters': {'category': category, 'business_type': business_type, 'search': search},
            'page_title': '補助金一覧'
        }
        
        return render(request, 'advisor/subsidy_list.html', context)
        
    except Exception as e:
        print(f"Subsidy list error: {e}")
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
        else:
            return render(request, 'advisor/error.html', {'error': str(e)})

# ========== 統計・分析ページ ==========

def subsidy_statistics(request):
    """補助金統計ページ"""
    try:
        # 基本統計
        subsidy_stats = SubsidyType.objects.aggregate(
            total_count=Count('id'),
            avg_amount=Avg('max_amount'),
            max_amount_value=Max('max_amount'),
            min_amount_value=Min('max_amount')
        )
        
        # 事業種別ごとの統計
        business_type_stats = SubsidyType.objects.values('target_business_type').annotate(
            count=Count('id'),
            avg_amount=Avg('max_amount')
        ).order_by('-count')[:10]
        
        # 会話統計
        conversation_stats = ConversationHistory.objects.aggregate(
            total_messages=Count('id'),
            unique_sessions=Count('session_id', distinct=True)
        )
        
        # 最近の活動（過去30日）
        last_30_days = timezone.now() - timedelta(days=30)
        recent_activity = ConversationHistory.objects.filter(
            timestamp__gte=last_30_days
        ).extra(
            select={'day': 'date(timestamp)'}
        ).values('day').annotate(
            message_count=Count('id')
        ).order_by('day')
        
        context = {
            'page_title': '補助金統計',
            'subsidy_stats': subsidy_stats,
            'business_type_stats': business_type_stats,
            'conversation_stats': conversation_stats,
            'recent_activity': list(recent_activity),
        }
        
        return render(request, 'advisor/statistics.html', context)
        
    except Exception as e:
        print(f"Statistics error: {e}")
        return render(request, 'advisor/error.html', {'error': str(e)})

def prediction_dashboard(request):
    """予測ダッシュボード"""
    try:
        current_date = timezone.now()
        
        # 基本的な予測データ（ルールベース）
        predictions = []
        
        # IT導入補助金の予測
        it_subsidy = SubsidyType.objects.filter(name__icontains='IT').first()
        if it_subsidy:
            predictions.append({
                'subsidy_name': 'IT導入補助金',
                'prediction_type': '新規公募',
                'predicted_date': (current_date + timedelta(days=15)).strftime('%Y-%m-%d'),
                'confidence': 85,
                'description': 'IT導入補助金の次回公募開始が予測されます',
                'recommended_action': '事前準備として必要書類の整理を開始してください'
            })
        
        # その他の予測
        predictions.extend([
            {
                'subsidy_name': 'ものづくり補助金',
                'prediction_type': '締切延長',
                'predicted_date': (current_date + timedelta(days=7)).strftime('%Y-%m-%d'),
                'confidence': 72,
                'description': '申請締切の延長が予測されます',
                'recommended_action': '申請書類の最終確認を行ってください'
            },
            {
                'subsidy_name': '事業再構築補助金',
                'prediction_type': '採択発表',
                'predicted_date': (current_date + timedelta(days=30)).strftime('%Y-%m-%d'),
                'confidence': 90,
                'description': '第10回採択結果の発表が予測されます',
                'recommended_action': '採択後の準備を進めておいてください'
            }
        ])
        
        # 統計
        prediction_stats = {
            'total_predictions': len(predictions),
            'high_confidence': len([p for p in predictions if p['confidence'] >= 80]),
            'medium_confidence': len([p for p in predictions if 60 <= p['confidence'] < 80]),
            'low_confidence': len([p for p in predictions if p['confidence'] < 60]),
        }
        
        context = {
            'predictions': predictions,
            'prediction_stats': prediction_stats,
            'current_date': current_date.strftime('%Y-%m-%d'),
            'page_title': '予測ダッシュボード',
            'prediction_available': True
        }
        
        return render(request, 'advisor/prediction_dashboard.html', context)
        
    except Exception as e:
        print(f"Prediction dashboard error: {e}")
        return render(request, 'advisor/prediction_dashboard.html', {
            'page_title': '予測ダッシュボード',
            'prediction_available': False,
            'error_message': f'予測データの取得中にエラーが発生しました: {str(e)}'
        })

def user_alerts(request):
    """ユーザーアラート管理"""
    context = {
        'page_title': 'アラート管理',
        'alerts': [],
        'unread_count': 0,
        'alerts_available': NEW_MODELS_AVAILABLE,
        'message': 'アラート機能は準備中です。' if not NEW_MODELS_AVAILABLE else None
    }
    
    if NEW_MODELS_AVAILABLE and UserAlert:
        try:
            alerts = UserAlert.objects.filter(
                user=request.user if request.user.is_authenticated else None
            ).order_by('-created_at')[:20]
            
            unread_count = alerts.filter(is_read=False).count()
            
            context.update({
                'alerts': alerts,
                'unread_count': unread_count,
                'alerts_available': True,
                'message': None
            })
            
        except Exception as e:
            print(f"Alert query error: {e}")
            context['error_message'] = f'アラートデータの取得中にエラーが発生しました: {str(e)}'
    
    return render(request, 'advisor/user_alerts.html', context)

def trend_analysis(request):
    """トレンド分析ページ"""
    context = {
        'page_title': '補助金トレンド分析',
        'trends_available': NEW_MODELS_AVAILABLE,
        'message': 'トレンド分析機能は準備中です。新しいモデルのマイグレーションが必要です。' if not NEW_MODELS_AVAILABLE else None
    }
    
    if NEW_MODELS_AVAILABLE and TrendAnalysis:
        try:
            latest_trend = TrendAnalysis.objects.order_by('-analysis_date').first()
            
            # 基本的なトレンド統計
            basic_trends = {
                'total_subsidies': SubsidyType.objects.count(),
                'average_amount': SubsidyType.objects.aggregate(
                    avg_amount=Avg('max_amount')
                ).get('avg_amount', 0),
                'most_common_target': SubsidyType.objects.values('target_business_type').annotate(
                    count=Count('target_business_type')
                ).order_by('-count').first()
            }
            
            context.update({
                'trend_data': latest_trend,
                'basic_trends': basic_trends,
                'trends_available': True,
                'last_analysis_date': latest_trend.analysis_date if latest_trend else None,
                'message': None
            })
            
        except Exception as e:
            print(f"Trend analysis error: {e}")
            context['error_message'] = f'トレンドデータの取得中にエラーが発生しました: {str(e)}'
    
    return render(request, 'advisor/trend_analysis.html', context)

def admin_dashboard(request):
    """管理ダッシュボード"""
    if not request.user.is_staff:
        return HttpResponseForbidden("管理者権限が必要です")
    
    try:
        # 基本統計
        basic_stats = {
            'total_users': User.objects.count(),
            'total_conversations': ConversationHistory.objects.count(),
            'unique_sessions': ConversationHistory.objects.values('session_id').distinct().count(),
            'total_subsidies': SubsidyType.objects.count(),
        }
        
        # 最近の会話履歴
        recent_conversations = ConversationHistory.objects.order_by('-timestamp')[:10]
        
        context = {
            'page_title': '管理ダッシュボード',
            'basic_stats': basic_stats,
            'recent_conversations': recent_conversations,
            'features_status': {
                'basic_chat': True,
                'enhanced_chat': ENHANCED_SERVICES_AVAILABLE,
                'predictions': NEW_MODELS_AVAILABLE,
                'alerts': NEW_MODELS_AVAILABLE,
                'trends': NEW_MODELS_AVAILABLE,
            }
        }
        
        return render(request, 'advisor/admin_dashboard.html', context)
        
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        return render(request, 'advisor/error.html', {'error': str(e)})

# ========== ユーティリティ・その他 ==========

def custom_404(request, exception):
    """カスタム404エラーページ"""
    return render(request, 'advisor/error.html', {
        'error': 'ページが見つかりませんでした。',
        'error_code': '404'
    }, status=404)

def custom_500(request):
    """カスタム500エラーページ"""
    return render(request, 'advisor/error.html', {
        'error': 'サーバー内部エラーが発生しました。',
        'error_code': '500'
    }, status=500)

# ========== 互換性維持用エイリアス ==========

def chat(request):
    """chat_interface へのエイリアス（互換性維持）"""
    return chat_interface(request)




# ========================================
# advisor/views.py に追加する関数
# ========================================

def prediction_calendar(request):
    """公募予測カレンダー"""
    try:
        current_date = timezone.now()
        
        # カレンダー表示年月の取得
        year = int(request.GET.get('year', current_date.year))
        month = int(request.GET.get('month', current_date.month))
        
        # 月の基本情報
        from calendar import monthrange
        days_in_month = monthrange(year, month)[1]
        month_start = timezone.datetime(year, month, 1).date()
        month_end = timezone.datetime(year, month, days_in_month).date()
        
        # 予測データを生成
        predictions = generate_monthly_predictions(year, month)
        
        # 前月・次月の計算
        prev_month = month - 1
        prev_year = year
        if prev_month < 1:
            prev_month = 12
            prev_year -= 1
        
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        # 月名の日本語化
        month_names = ['', '1月', '2月', '3月', '4月', '5月', '6月',
                      '7月', '8月', '9月', '10月', '11月', '12月']
        
        # カレンダーグリッドの生成
        import calendar
        cal = calendar.Calendar(firstweekday=0)  # 月曜日始まり
        month_days = list(cal.itermonthdays(year, month))
        
        # 週ごとにグループ化
        weeks = []
        week = []
        for day in month_days:
            if len(week) == 7:
                weeks.append(week)
                week = []
            week.append(day)
        if week:
            weeks.append(week)
        
        context = {
            'current_year': year,
            'current_month': month,
            'current_month_name': month_names[month],
            'prev_year': prev_year,
            'prev_month': prev_month,
            'next_year': next_year,
            'next_month': next_month,
            'weeks': weeks,
            'predictions': predictions,
            'today': current_date.date(),
            'page_title': f'{year}年{month_names[month]} 公募予測カレンダー'
        }
        
        return render(request, 'advisor/prediction_calendar.html', context)
        
    except Exception as e:
        print(f"Prediction calendar error: {e}")
        return render(request, 'advisor/error.html', {'error': str(e)})

def statistics_dashboard(request):
    """統計ダッシュボード（詳細版）"""
    try:
        # 基本統計
        basic_stats = {
            'total_subsidies': SubsidyType.objects.count(),
            'total_conversations': ConversationHistory.objects.count(),
            'active_sessions': ConversationHistory.objects.values('session_id').distinct().count(),
        }
        
        # 補助金統計
        subsidy_stats = SubsidyType.objects.aggregate(
            avg_amount=Avg('max_amount'),
            max_amount_value=Max('max_amount'),
            min_amount_value=Min('max_amount')
        )
        
        # 事業種別統計
        business_type_stats = SubsidyType.objects.values('target_business_type').annotate(
            count=Count('id'),
            avg_amount=Avg('max_amount')
        ).order_by('-count')[:10]
        
        # 時系列データ（過去30日の会話数）
        last_30_days = timezone.now() - timedelta(days=30)
        daily_conversations = []
        
        for i in range(30):
            date = last_30_days + timedelta(days=i)
            count = ConversationHistory.objects.filter(
                timestamp__date=date.date(),
                message_type='user'
            ).count()
            daily_conversations.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        context = {
            'basic_stats': basic_stats,
            'subsidy_stats': subsidy_stats,
            'business_type_stats': business_type_stats,
            'daily_conversations': daily_conversations,
            'page_title': '統計ダッシュボード'
        }
        
        return render(request, 'advisor/statistics_dashboard.html', context)
        
    except Exception as e:
        print(f"Statistics dashboard error: {e}")
        return render(request, 'advisor/error.html', {'error': str(e)})

def generate_monthly_predictions(year, month):
    """指定月の予測データを生成"""
    predictions = {}
    
    # 実際の補助金データを取得
    subsidies = SubsidyType.objects.all()[:5]  # 最初の5つの補助金を使用
    
    for i, subsidy in enumerate(subsidies):
        # 簡単な予測ロジック
        day = (i * 7 + 5) % 28 + 1  # 5, 12, 19, 26日など
        key = f"{year}-{month:02d}-{day:02d}"
        
        predictions[key] = {
            'date': key,
            'subsidy_name': subsidy.name,
            'event_type': 'announcement' if i % 2 == 0 else 'deadline',
            'confidence': 75 + (i * 5),
            'description': f'{subsidy.name}の{"公募開始" if i % 2 == 0 else "申請締切"}が予測されます',
            'recommended_action': '事前準備として必要書類の整理を開始してください',
        }
    
    return predictions

def get_calendar_events_api(request):
    """カレンダーイベント取得API"""
    try:
        year = int(request.GET.get('year', timezone.now().year))
        month = int(request.GET.get('month', timezone.now().month))
        
        predictions = generate_monthly_predictions(year, month)
        
        events = []
        for prediction in predictions.values():
            events.append({
                'title': f"{prediction['subsidy_name']}",
                'start': prediction['date'],
                'description': prediction['description'],
                'confidence': prediction['confidence']
            })
        
        return JsonResponse({'success': True, 'events': events})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def prediction_detail_api(request):
    """予測詳細情報API"""
    try:
        date = request.GET.get('date')
        subsidy_name = request.GET.get('subsidy_name')
        
        if not date or not subsidy_name:
            return JsonResponse({'success': False, 'error': 'パラメータが不足しています'}, status=400)
        
        detail = {
            'subsidy_name': subsidy_name,
            'date': date,
            'description': f'{subsidy_name}の予測イベント',
            'confidence': 80,
            'tips': [
                '事前準備として必要書類を整理してください',
                '申請要件を詳しく確認してください'
            ]
        }
        
        return JsonResponse({'success': True, 'detail': detail})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def session_list(request):
    """
    セッション一覧表示ビュー - 実際のデータベースからの情報を表示
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("管理者権限が必要です")
    
    try:
        # セッションごとの統計情報を取得
        sessions_data = ConversationHistory.objects.values('session_id').annotate(
            message_count=Count('id'),
            last_activity=Max('timestamp'),
            user_messages=Count('id', filter=Q(message_type='user')),
            assistant_messages=Count('id', filter=Q(message_type='assistant'))
        ).order_by('-last_activity')[:100]  # 最新100セッション
        
        # セッション詳細情報を構築
        sessions = []
        for session_data in sessions_data:
            # 最初のメッセージを取得（セッション開始時刻として使用）
            first_message = ConversationHistory.objects.filter(
                session_id=session_data['session_id']
            ).order_by('timestamp').first()
            
            # 最後のユーザーメッセージを取得（プレビュー用）
            last_user_message = ConversationHistory.objects.filter(
                session_id=session_data['session_id'],
                message_type='user'
            ).order_by('-timestamp').first()
            
            # ユーザー情報を取得
            session_user = ConversationHistory.objects.filter(
                session_id=session_data['session_id'],
                user__isnull=False
            ).values('user__username').first()
            
            # セッションのステータス判定
            time_since_last = timezone.now() - session_data['last_activity']
            if time_since_last < timedelta(minutes=30):
                status = 'active'
                status_class = 'success'
            elif time_since_last < timedelta(hours=24):
                status = 'recent'
                status_class = 'warning'
            else:
                status = 'inactive'
                status_class = 'secondary'
            
            sessions.append({
                'session_id': session_data['session_id'],
                'user': session_user['user__username'] if session_user else 'ゲスト',
                'message_count': session_data['message_count'],
                'user_messages': session_data['user_messages'],
                'assistant_messages': session_data['assistant_messages'],
                'started_at': first_message.timestamp if first_message else None,
                'last_activity': session_data['last_activity'],
                'last_message_preview': last_user_message.content[:50] + '...' if last_user_message and len(last_user_message.content) > 50 else (last_user_message.content if last_user_message else ''),
                'status': status,
                'status_class': status_class,
                'time_since_last': time_since_last
            })
        
        # 統計情報
        total_sessions = len(sessions)
        active_sessions = len([s for s in sessions if s['status'] == 'active'])
        total_messages = sum(s['message_count'] for s in sessions)
        
        # 今日の活動統計
        today = timezone.now().date()
        today_sessions = ConversationHistory.objects.filter(
            timestamp__date=today
        ).values('session_id').distinct().count()
        
        context = {
            'sessions': sessions,
            'stats': {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'total_messages': total_messages,
                'today_sessions': today_sessions
            },
            'page_title': 'セッション一覧'
        }
        return render(request, 'advisor/session_list.html', context)
        
    except Exception as e:
        print(f"Session list error: {e}")
        return render(request, 'advisor/error.html', {'error': str(e)})

def debug_history(request):
    """
    会話履歴デバッグビュー
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("管理者権限が必要です")
    
    try:
        # クエリパラメータ
        session_id = request.GET.get('session_id', '')
        user_type = request.GET.get('user_type', 'all')
        days = int(request.GET.get('days', 7))
        
        # 基本クエリ
        conversations = ConversationHistory.objects.all()
        
        # フィルタリング
        if session_id:
            conversations = conversations.filter(session_id__icontains=session_id)
        
        if user_type != 'all':
            conversations = conversations.filter(message_type=user_type)
        
        # 日付フィルター
        start_date = timezone.now() - timedelta(days=days)
        conversations = conversations.filter(timestamp__gte=start_date)
        
        # 並び替え
        conversations = conversations.order_by('-timestamp')[:200]  # 最新200件
        
        # 統計情報
        stats = {
            'total_conversations': conversations.count(),
            'user_messages': conversations.filter(message_type='user').count(),
            'assistant_messages': conversations.filter(message_type='assistant').count(),
            'unique_sessions': conversations.values('session_id').distinct().count(),
        }
        
        context = {
            'conversations': conversations,
            'stats': stats,
            'filters': {
                'session_id': session_id,
                'user_type': user_type,
                'days': days
            },
            'page_title': '会話履歴デバッグ'
        }
        return render(request, 'advisor/debug_history.html', context)
        
    except Exception as e:
        print(f"Debug history error: {e}")
        return render(request, 'advisor/error.html', {'error': str(e)})

def export_session(request, session_id):
    """
    セッションエクスポート機能
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("管理者権限が必要です")
    
    try:
        # セッション履歴を取得
        history = ConversationHistory.objects.filter(
            session_id=session_id
        ).order_by('timestamp')
        
        if not history.exists():
            return JsonResponse({
                'success': False, 
                'error': '指定されたセッションが見つかりません'
            }, status=404)
        
        # エクスポートデータを構築
        export_data = {
            'session_id': session_id,
            'exported_at': timezone.now().isoformat(),
            'total_messages': history.count(),
            'messages': []
        }
        
        for message in history:
            export_data['messages'].append({
                'id': message.id,
                'timestamp': message.timestamp.isoformat(),
                'message_type': message.message_type,
                'content': message.content,
                'user': message.user.username if message.user else 'ゲスト',
            })
        
        # JSONレスポンスとして返す
        response = HttpResponse(
            json.dumps(export_data, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="session_{session_id}.json"'
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'エクスポート中にエラーが発生しました: {str(e)}'
        }, status=500)

@require_http_methods(["DELETE", "POST"])
def delete_session(request, session_id):
    """
    セッション削除機能（管理者のみ）
    """
    if not request.user.is_staff:
        return JsonResponse({
            'success': False, 
            'error': '管理者権限が必要です'
        }, status=403)
    
    try:
        # セッションの存在確認
        session_messages = ConversationHistory.objects.filter(session_id=session_id)
        
        if not session_messages.exists():
            return JsonResponse({
                'success': False, 
                'error': '指定されたセッションが見つかりません'
            }, status=404)
        
        # セッション削除
        deleted_count = session_messages.delete()[0]
        
        return JsonResponse({
            'success': True, 
            'message': f'セッション {session_id} を削除しました',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'削除中にエラーが発生しました: {str(e)}'
        }, status=500)

# 既存の prediction_calendar などの関数も追加
def prediction_calendar(request):
    """公募予測カレンダー"""
    try:
        current_date = timezone.now()
        year = int(request.GET.get('year', current_date.year))
        month = int(request.GET.get('month', current_date.month))
        
        # 基本的な予測データ
        predictions = {}
        
        # 簡単な予測データ生成
        subsidies = SubsidyType.objects.all()[:3]
        for i, subsidy in enumerate(subsidies):
            day = (i * 10 + 5) % 28 + 1
            key = f"{year}-{month:02d}-{day:02d}"
            predictions[key] = {
                'date': key,
                'subsidy_name': subsidy.name,
                'event_type': 'announcement' if i % 2 == 0 else 'deadline',
                'confidence': 75 + (i * 5),
                'description': f'{subsidy.name}の{"公募開始" if i % 2 == 0 else "申請締切"}が予測されます'
            }
        
        # 月名
        month_names = ['', '1月', '2月', '3月', '4月', '5月', '6月',
                      '7月', '8月', '9月', '10月', '11月', '12月']
        
        # 前月・次月
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        context = {
            'current_year': year,
            'current_month': month,
            'current_month_name': month_names[month],
            'prev_year': prev_year,
            'prev_month': prev_month,
            'next_year': next_year,
            'next_month': next_month,
            'predictions': predictions,
            'today': current_date.date(),
            'page_title': f'{year}年{month_names[month]} 公募予測カレンダー'
        }
        
        return render(request, 'advisor/prediction_calendar.html', context)
        
    except Exception as e:
        print(f"Prediction calendar error: {e}")
        return render(request, 'advisor/error.html', {'error': str(e)})

def statistics_dashboard(request):
    """統計ダッシュボード（詳細版）"""
    try:
        # 基本統計
        basic_stats = {
            'total_subsidies': SubsidyType.objects.count(),
            'total_conversations': ConversationHistory.objects.count(),
            'active_sessions': ConversationHistory.objects.values('session_id').distinct().count(),
        }
        
        context = {
            'basic_stats': basic_stats,
            'page_title': '統計ダッシュボード'
        }
        
        return render(request, 'advisor/statistics_dashboard.html', context)
        
    except Exception as e:
        print(f"Statistics dashboard error: {e}")
        return render(request, 'advisor/error.html', {'error': str(e)})

def get_calendar_events_api(request):
    """カレンダーイベント取得API"""
    try:
        year = int(request.GET.get('year', timezone.now().year))
        month = int(request.GET.get('month', timezone.now().month))
        
        events = [
            {
                'title': 'IT導入補助金公募開始',
                'start': f'{year}-{month:02d}-05',
                'description': 'IT導入補助金の新規公募が開始予定'
            }
        ]
        
        return JsonResponse({'success': True, 'events': events})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def prediction_detail_api(request):
    """予測詳細情報API"""
    try:
        date = request.GET.get('date')
        detail = {
            'date': date,
            'description': '予測イベントの詳細情報',
            'confidence': 80
        }
        
        return JsonResponse({'success': True, 'detail': detail})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContextAwareChatAPIView(View):
    """文脈を理解するチャットAPI"""
    
    def __init__(self):
        super().__init__()
        self.ai_service = ContextAwareAIAdvisorService()
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            session_id = data.get('session_id')
            conversation_context = data.get('conversation_context', [])
            
            logger.info(f"Context Aware Chat API - Session: {session_id}, Message: {message}")
            logger.info(f"Conversation Context: {conversation_context}")
            
            if not message:
                return JsonResponse({
                    'success': False,
                    'error': 'メッセージが空です'
                }, status=400)
            
            # 1. 会話履歴から文脈を取得
            context_history = self._get_conversation_history(session_id, limit=5)
            
            # 2. 前の会話から対象補助金を特定
            target_subsidy = self._extract_target_subsidy_from_context(
                context_history, conversation_context, message
            )
            
            # 3. 文脈を考慮した回答生成
            response = self.ai_service.analyze_question_with_context(
                question_text=message,
                conversation_history=context_history,
                target_subsidy=target_subsidy,
                user_context={
                    'session_id': session_id,
                    'previous_topics': self._extract_previous_topics(context_history)
                }
            )
            
            # 4. 会話履歴の保存
            self._save_conversation_turn(session_id, message, response)
            
            return JsonResponse({
                'success': True,
                'response': response.get('answer', ''),
                'context_detected': target_subsidy.name if target_subsidy else None,
                'confidence_score': response.get('confidence_score', 0.7),
                'model_used': response.get('model_used', 'context-aware'),
                'recommended_subsidies': [
                    {
                        'id': sub.id if hasattr(sub, 'id') else None,
                        'name': sub.name if hasattr(sub, 'name') else str(sub)
                    } for sub in response.get('recommended_subsidies', [])
                ]
            })
            
        except json.JSONDecodeError:
            logger.error("JSON decode error in context aware chat API")
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON format'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Context Aware Chat API Error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'サーバーエラーが発生しました'
            }, status=500)
    
    def _get_conversation_history(self, session_id, limit=5):
        """セッションの会話履歴を取得"""
        if not session_id:
            return []
        
        try:
            history = ConversationHistory.objects.filter(
                session_id=session_id
            ).order_by('-timestamp')[:limit * 2]  # user/assistant ペアなので2倍取得
            
            return [
                {
                    'role': h.message_type,
                    'content': h.content,
                    'timestamp': h.timestamp,
                    'intent_analysis': getattr(h, 'intent_analysis', {}),
                    'metadata': getattr(h, 'metadata', {})
                }
                for h in reversed(history)
            ]
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def _extract_target_subsidy_from_context(self, context_history, conversation_context, current_message):
        """文脈から対象補助金を特定"""
        from .models import SubsidyType
        
        # 現在のメッセージから補助金名を抽出
        current_target = self._detect_subsidy_in_text(current_message)
        if current_target:
            return current_target
        
        # 直前の会話から補助金名を抽出
        for context_msg in reversed(conversation_context[-3:]):  # 最新3件
            if context_msg.get('role') == 'user':
                target = self._detect_subsidy_in_text(context_msg.get('content', ''))
                if target:
                    logger.info(f"Found target subsidy from context: {target.name}")
                    return target
        
        # 会話履歴から補助金名を抽出
        for history_item in reversed(context_history[-3:]):
            if history_item.get('role') == 'user':
                target = self._detect_subsidy_in_text(history_item.get('content', ''))
                if target:
                    logger.info(f"Found target subsidy from history: {target.name}")
                    return target
        
        return None
    
    def _detect_subsidy_in_text(self, text):
        """テキストから補助金名を検出"""
        if not text:
            return None
        
        from .models import SubsidyType
        
        text_lower = text.lower()
        
        # 補助金名のパターンマッチング
        subsidy_patterns = {
            'IT導入補助金': ['it導入', 'IT導入', 'itツール', 'ITツール', 'ソフトウェア', 'デジタル化'],
            '事業再構築補助金': ['事業再構築', '再構築', '事業転換', '新分野展開', '業態転換'],
            'ものづくり補助金': ['ものづくり', '設備投資', '機械', '装置', '製造業'],
            '小規模事業者持続化補助金': ['持続化', '小規模事業者', '販路開拓', '広告宣伝'],
        }
        
        for subsidy_name, patterns in subsidy_patterns.items():
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    try:
                        return SubsidyType.objects.filter(name__icontains=subsidy_name.split('補助金')[0]).first()
                    except:
                        continue
        
        return None
    
    def _extract_previous_topics(self, context_history):
        """会話履歴から主要トピックを抽出"""
        topics = []
        
        for item in context_history:
            if item.get('role') == 'user':
                content = item.get('content', '')
                
                # キーワード抽出
                keywords = []
                if any(word in content.lower() for word in ['採択率', '成功率', '確率']):
                    keywords.append('採択率向上')
                if any(word in content.lower() for word in ['申請', '手続き', '方法']):
                    keywords.append('申請手続き')
                if any(word in content.lower() for word in ['要件', '条件', '対象']):
                    keywords.append('申請要件')
                if any(word in content.lower() for word in ['スケジュール', '期限', 'タイミング']):
                    keywords.append('申請時期')
                
                topics.extend(keywords)
        
        return list(set(topics))  # 重複除去
    
    def _save_conversation_turn(self, session_id, user_message, assistant_response):
        """会話ターンを保存"""
        from django.utils import timezone
        
        try:
            # ユーザーメッセージ保存
            ConversationHistory.objects.create(
                session_id=session_id,
                message_type='user',
                content=user_message,
                timestamp=timezone.now()
            )
            
            # アシスタント回答保存
            ConversationHistory.objects.create(
                session_id=session_id,
                message_type='assistant',
                content=assistant_response.get('answer', ''),
                metadata={
                    'confidence_score': assistant_response.get('confidence_score', 0),
                    'model_used': assistant_response.get('model_used', 'context-aware'),
                    'target_subsidy': assistant_response.get('target_subsidy'),
                    'context_utilized': True
                },
                timestamp=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")