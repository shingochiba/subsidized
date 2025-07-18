# advisor/views.py - 完全版（エラー修正済み）
# 補助金アドバイザーのビュー関数

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
import uuid

# モデルのインポート
from django.db import models
from .models import (
    SubsidyType, Answer, ConversationHistory, AdoptionStatistics, 
    AdoptionTips
)

# 新しいモデル（マイグレーション後に利用可能）
try:
    from .models import SubsidyPrediction, UserAlert, TrendAnalysis
    NEW_MODELS_AVAILABLE = True
except ImportError:
    # マイグレーション前のフォールバック
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

def index(request):
    """
    メインページ
    補助金一覧と基本統計を表示
    """
    subsidies = SubsidyType.objects.all()
    
    # 基本統計
    basic_stats = {
        'total_subsidies': subsidies.count(),
        'total_conversations': ConversationHistory.objects.count(),
        'active_sessions': ConversationHistory.objects.values('session_id').distinct().count(),
    }
    
    # 最新の予測データ（利用可能な場合）
    recent_predictions = []
    if NEW_MODELS_AVAILABLE and SubsidyPrediction:
        try:
            recent_predictions = SubsidyPrediction.objects.filter(
                predicted_date__gte=timezone.now().date()
            ).order_by('predicted_date')[:5]
        except Exception as e:
            print(f"Prediction query error: {e}")
            recent_predictions = []
    
    # 最新の会話履歴
    recent_conversations = ConversationHistory.objects.filter(
        message_type='user'
    ).order_by('-timestamp')[:5]
    
    context = {
        'page_title': '補助金アドバイザー',
        'subsidies': subsidies,
        'recent_predictions': recent_predictions,
        'recent_conversations': recent_conversations,
        'stats': basic_stats,
        'new_features_available': NEW_MODELS_AVAILABLE,
        'enhanced_services_available': ENHANCED_SERVICES_AVAILABLE,
    }
    
    return render(request, 'advisor/index.html', context)

def chat_interface(request):
    """
    既存のチャットインターフェース（後方互換性）
    """
    context = {
        'page_title': '補助金AI相談',
        'description': 'AIとの対話で最適な補助金を見つけます',
        'chat_type': 'basic',
        'enhanced_available': ENHANCED_SERVICES_AVAILABLE
    }
    return render(request, 'advisor/chat.html', context)

def enhanced_chat_interface(request):
    """
    強化されたチャットインターフェース
    """
    if not ENHANCED_SERVICES_AVAILABLE:
        # フォールバック：基本チャットにリダイレクト
        context = {
            'page_title': '補助金AI相談',
            'description': 'AIとの対話で最適な補助金を見つけます',
            'message': '強化版チャット機能は準備中です。基本版をご利用ください。',
            'chat_type': 'basic',
            'enhanced_available': False
        }
        return render(request, 'advisor/chat.html', context)
    
    context = {
        'page_title': '補助金AI相談（強化版）',
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
        'enhanced_available': True
    }
    return render(request, 'advisor/enhanced_chat.html', context)

def prediction_dashboard(request):
    """
    補助金予測ダッシュボード
    """
    
    if not NEW_MODELS_AVAILABLE or not ENHANCED_SERVICES_AVAILABLE:
        # 機能が利用できない場合
        context = {
            'page_title': '補助金予測ダッシュボード',
            'prediction_available': False,
            'error_message': '予測機能は準備中です。マイグレーションの実行が必要です。',
            'setup_instructions': [
                'python manage.py makemigrations advisor',
                'python manage.py migrate',
                'python manage.py update_predictions --months 12'
            ]
        }
        return render(request, 'advisor/prediction_dashboard.html', context)
    
    # サービスが利用可能な場合
    try:
        prediction_service = SubsidyPredictionService()
        
        # 予測データの取得
        predictions = prediction_service.predict_next_opportunities(months_ahead=6)
        calendar_data = prediction_service.generate_prediction_calendar()
        trends = prediction_service.analyze_subsidy_trends()
        
        # アラート情報
        alerts = []
        if request.user.is_authenticated and UserAlert:
            try:
                alerts = UserAlert.objects.filter(
                    user=request.user,
                    is_dismissed=False
                ).order_by('-created_at')[:10]
            except Exception as e:
                print(f"Alert query error: {e}")
                alerts = []
        
        # 予測統計
        prediction_stats = {
            'total_predictions': len(predictions),
            'high_priority_count': len([p for p in predictions if p.get('recommendation_priority', 0) >= 0.7]),
            'next_30_days': len([p for p in predictions if 
                (timezone.datetime.strptime(str(p.get('predicted_date', '')), '%Y-%m-%d').date() 
                 - timezone.now().date()).days <= 30
            ]) if predictions else 0
        }
        
        context = {
            'page_title': '補助金予測ダッシュボード',
            'predictions': predictions,
            'calendar_data': calendar_data,
            'trends': trends,
            'alerts': alerts,
            'prediction_stats': prediction_stats,
            'months_ahead': 6,
            'prediction_available': True
        }
        
    except Exception as e:
        # 予測機能でエラーが発生した場合
        print(f"Prediction service error: {e}")
        context = {
            'page_title': '補助金予測ダッシュボード',
            'predictions': [],
            'calendar_data': {},
            'trends': {},
            'alerts': [],
            'months_ahead': 6,
            'prediction_available': False,
            'error_message': f'予測機能でエラーが発生しました: {str(e)}',
            'debug_mode': True if hasattr(request, 'debug') and request.debug else False
        }
    
    return render(request, 'advisor/prediction_dashboard.html', context)

@login_required
def user_alerts(request):
    """
    ユーザーアラート管理ページ
    """
    
    if not NEW_MODELS_AVAILABLE or not UserAlert:
        # UserAlertモデルが利用できない場合
        context = {
            'alerts': [],
            'unread_count': 0,
            'page_title': 'アラート管理',
            'message': 'アラート機能は準備中です。新しいモデルのマイグレーションが必要です。',
            'alerts_available': False
        }
    else:
        try:
            alerts = UserAlert.objects.filter(user=request.user).order_by('-created_at')
            unread_count = alerts.filter(is_read=False).count()
            
            # アラート統計
            alert_stats = {
                'total_alerts': alerts.count(),
                'unread_count': unread_count,
                'high_priority_count': alerts.filter(priority='high').count(),
                'dismissed_count': alerts.filter(is_dismissed=True).count(),
            }
            
            context = {
                'alerts': alerts,
                'alert_stats': alert_stats,
                'unread_count': unread_count,
                'page_title': 'アラート管理',
                'alerts_available': True
            }
            
        except Exception as e:
            print(f"Alert query error: {e}")
            context = {
                'alerts': [],
                'unread_count': 0,
                'page_title': 'アラート管理',
                'error_message': f'アラートデータの取得中にエラーが発生しました: {str(e)}',
                'alerts_available': False
            }
    
    return render(request, 'advisor/user_alerts.html', context)

def trend_analysis(request):
    """
    トレンド分析ページ
    """
    
    if not NEW_MODELS_AVAILABLE or not TrendAnalysis:
        # TrendAnalysisモデルが利用できない場合
        context = {
            'trend_data': None,
            'page_title': '補助金トレンド分析',
            'message': 'トレンド分析機能は準備中です。新しいモデルのマイグレーションが必要です。',
            'trends_available': False
        }
    else:
        try:
            latest_trend = TrendAnalysis.objects.order_by('-analysis_date').first()
            
            # 基本的なトレンド統計
            basic_trends = {
                'total_subsidies': SubsidyType.objects.count(),
                'average_amount': SubsidyType.objects.aggregate(
                    avg_amount=models.Avg('max_amount')
                ).get('avg_amount', 0),
                'most_common_target': SubsidyType.objects.values('target_business_type').annotate(
                    count=models.Count('target_business_type')
                ).order_by('-count').first()
            }
            
            context = {
                'trend_data': latest_trend,
                'basic_trends': basic_trends,
                'page_title': '補助金トレンド分析',
                'trends_available': True,
                'last_analysis_date': latest_trend.analysis_date if latest_trend else None
            }
            
        except Exception as e:
            print(f"Trend analysis error: {e}")
            context = {
                'trend_data': None,
                'page_title': '補助金トレンド分析',
                'error_message': f'トレンド分析データの取得中にエラーが発生しました: {str(e)}',
                'trends_available': False
            }
    
    return render(request, 'advisor/trend_analysis.html', context)

# API エンドポイント

@csrf_exempt
def analyze_question(request):
    """
    既存の質問分析API（後方互換性）
    """
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        # リクエストデータの解析
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        question = data.get('question', '').strip()
        user_context = {
            'business_type': data.get('business_type', ''),
            'company_size': data.get('company_size', ''),
            'region': data.get('region', ''),
        }
        
        if not question:
            return JsonResponse({
                'success': False,
                'error': '質問を入力してください'
            }, status=400)
        
        # サービスの選択と実行
        try:
            if ENHANCED_SERVICES_AVAILABLE and EnhancedChatService:
                # 強化されたサービスを使用
                advisor_service = EnhancedChatService()
                session_id = data.get('session_id', str(uuid.uuid4()))
                
                result = advisor_service.process_conversation(
                    message=question,
                    session_id=session_id,
                    user_context=user_context
                )
                
                # 会話履歴を保存
                ConversationManager.save_conversation(
                    session_id=session_id,
                    user=request.user if request.user.is_authenticated else None,
                    message_type='user',
                    content=question
                )
                
                ConversationManager.save_conversation(
                    session_id=session_id,
                    user=request.user if request.user.is_authenticated else None,
                    message_type='assistant',
                    content=result.get('answer', '')
                )
                
            else:
                # 既存のサービスを使用
                advisor_service = AIAdvisorService()
                result = advisor_service.analyze_question(question, user_context)
            
            return JsonResponse({
                'success': True,
                'result': result,
                'timestamp': timezone.now().isoformat(),
                'service_used': 'enhanced' if ENHANCED_SERVICES_AVAILABLE else 'basic'
            })
            
        except Exception as service_error:
            print(f"Service error: {service_error}")
            
            # フォールバック回答
            fallback_result = generate_fallback_response(question, user_context)
            
            return JsonResponse({
                'success': True,
                'result': fallback_result,
                'notice': 'システム更新中のため限定的な回答です',
                'timestamp': timezone.now().isoformat(),
                'service_used': 'fallback'
            })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        print(f"Analyze question error: {e}")
        return JsonResponse({
            'success': False,
            'error': '処理中にエラーが発生しました',
            'debug_info': str(e) if hasattr(request, 'debug') and request.debug else None
        }, status=500)

def generate_fallback_response(question, user_context):
    """
    フォールバック用の回答生成
    """
    business_type = user_context.get('business_type', '一般事業者')
    
    # 質問に応じた基本的な回答パターン
    if any(keyword in question.lower() for keyword in ['金額', 'いくら', '予算', '費用']):
        answer_type = 'amount'
    elif any(keyword in question.lower() for keyword in ['申請', '手続き', 'やり方', '方法']):
        answer_type = 'process'
    elif any(keyword in question.lower() for keyword in ['いつ', 'タイミング', '期限', '時期']):
        answer_type = 'timing'
    else:
        answer_type = 'general'
    
    if answer_type == 'amount':
        answer = f"""
## 💰 補助金の金額について

{business_type}向けの主要な補助金の金額をご案内します：

### 小規模事業者持続化補助金
- **通常枠**: 最大50万円
- **特別枠**: 最大200万円

### ものづくり補助金
- **一般型**: 最大1,000万円
- **グローバル展開型**: 最大3,000万円

### IT導入補助金
- **通常枠**: 最大450万円
- **デジタル化基盤導入枠**: 最大350万円

## 📝 重要なポイント
- 補助率は通常1/2〜2/3程度
- 事前に詳細な事業計画が必要
- 交付決定前の発注は対象外
"""
    
    elif answer_type == 'process':
        answer = f"""
## 📋 補助金申請の基本的な流れ

### STEP 1: 事前準備
1. **公募要領の確認** - 最新の申請要件をチェック
2. **必要書類の準備** - 決算書、事業計画書等
3. **見積書の取得** - 複数業者からの相見積もり

### STEP 2: 申請書作成
1. **事業計画書** - 具体的で実現可能な内容
2. **経費明細書** - 対象経費の詳細リスト
3. **添付書類** - 会社概要、財務諸表等

### STEP 3: 申請・審査
1. **電子申請** - 指定システムからの提出
2. **審査期間** - 通常1-3ヶ月
3. **結果通知** - 採択・不採択の連絡

### STEP 4: 事業実施・報告
1. **交付決定後の事業開始**
2. **実績報告書の提出**
3. **確定検査後の補助金入金**
"""
    
    elif answer_type == 'timing':
        answer = f"""
## 📅 補助金申請のタイミング

### 年間スケジュール目安

**春季（3-5月）**
- 小規模事業者持続化補助金
- ものづくり補助金（第1回）

**夏季（6-8月）**
- IT導入補助金
- 小規模事業者持続化補助金

**秋季（9-11月）**
- ものづくり補助金（第2回）
- 事業再構築補助金

**冬季（12-2月）**
- 小規模事業者持続化補助金
- 年度末特別枠

## ⏰ 申請準備のポイント
- 公募開始の2-3ヶ月前から準備開始
- 事業計画の検討に十分な時間を確保
- 必要書類の早期収集を推奨
"""
    
    else:
        answer = f"""
## 🎯 {business_type}様におすすめの補助金

ご質問「{question}」について、以下の補助金制度をご検討ください：

### 1. 小規模事業者持続化補助金
- **対象**: 販路開拓・生産性向上の取組
- **金額**: 最大200万円
- **申請時期**: 年4回程度

### 2. ものづくり補助金
- **対象**: 革新的な設備投資・システム構築
- **金額**: 最大1,000万円
- **申請時期**: 年2-3回

### 3. IT導入補助金
- **対象**: ITツール・システム導入
- **金額**: 最大450万円
- **申請時期**: 年2回

## 💡 次のステップ
より具体的なアドバイスをご希望の場合は、以下の情報をお聞かせください：
- 投資予定の設備や取組内容
- 予算規模
- 実施予定時期
"""
    
    return {
        'answer': answer,
        'recommended_subsidies': [],
        'confidence_score': 0.6,
        'model_used': 'fallback',
        'question_type': answer_type
    }

# 管理機能

@login_required
def admin_dashboard(request):
    """
    管理ダッシュボード（認証とスタッフ権限をチェック）
    """
    # 認証チェック
    if not request.user.is_authenticated:
        context = {
            'page_title': '管理ダッシュボード',
            'error_message': 'この機能を利用するにはログインが必要です。',
            'login_required': True
        }
        return render(request, 'advisor/admin_dashboard.html', context)
    
    # スタッフ権限チェック
    if not request.user.is_staff:
        context = {
            'page_title': '管理ダッシュボード',
            'error_message': 'この機能を利用するには管理者権限が必要です。',
            'permission_denied': True
        }
        return render(request, 'advisor/admin_dashboard.html', context)
    
    # 基本統計
    basic_stats = {
        'total_subsidies': SubsidyType.objects.count(),
        'total_conversations': ConversationHistory.objects.count(),
        'unique_sessions': ConversationHistory.objects.values('session_id').distinct().count(),
        'total_answers': Answer.objects.count(),
    }
    
    # 新機能の統計（利用可能な場合）
    advanced_stats = {}
    if NEW_MODELS_AVAILABLE:
        if SubsidyPrediction:
            try:
                advanced_stats['total_predictions'] = SubsidyPrediction.objects.count()
                advanced_stats['active_predictions'] = SubsidyPrediction.objects.filter(
                    predicted_date__gte=timezone.now().date()
                ).count()
            except Exception:
                pass
        
        if UserAlert:
            try:
                advanced_stats['total_alerts'] = UserAlert.objects.count()
                advanced_stats['unread_alerts'] = UserAlert.objects.filter(is_read=False).count()
            except Exception:
                pass
        
        if TrendAnalysis:
            try:
                latest_analysis = TrendAnalysis.objects.order_by('-analysis_date').first()
                advanced_stats['latest_analysis'] = latest_analysis.analysis_date if latest_analysis else None
            except Exception:
                pass
    
    # 最近のアクティビティ
    recent_conversations = ConversationHistory.objects.order_by('-timestamp')[:10]
    
    context = {
        'page_title': '管理ダッシュボード',
        'basic_stats': basic_stats,
        'advanced_stats': advanced_stats,
        'recent_conversations': recent_conversations,
        'new_models_available': NEW_MODELS_AVAILABLE,
        'enhanced_services_available': ENHANCED_SERVICES_AVAILABLE,
        'features_status': {
            'basic_chat': True,
            'enhanced_chat': ENHANCED_SERVICES_AVAILABLE,
            'predictions': NEW_MODELS_AVAILABLE and ENHANCED_SERVICES_AVAILABLE,
            'alerts': NEW_MODELS_AVAILABLE,
            'trends': NEW_MODELS_AVAILABLE,
        }
    }
    
    return render(request, 'advisor/admin_dashboard.html', context)

# 統計・分析ビュー

def subsidy_statistics(request):
    """
    補助金統計ページ（エラー修正済み）
    """
    from django.db.models import Count, Avg, Max, Min
    
    # 基本統計 - フィールド名衝突を回避
    subsidy_stats = SubsidyType.objects.aggregate(
        total_count=Count('id'),
        avg_amount=Avg('max_amount'),
        max_amount_value=Max('max_amount'),  # フィールド名を変更
        min_amount_value=Min('max_amount')   # フィールド名を変更
    )
    
    # 事業種別ごとの統計
    business_type_stats = SubsidyType.objects.values('target_business_type').annotate(
        count=Count('id'),
        avg_amount=Avg('max_amount')
    ).order_by('-count')
    
    # 会話統計
    conversation_stats = ConversationHistory.objects.aggregate(
        total_messages=Count('id'),
        unique_sessions=Count('session_id', distinct=True)
    )
    
    # 最近の傾向
    from datetime import timedelta
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

# API用のヘルパー関数

@api_view(['GET'])
def subsidy_list(request):
    """補助金一覧API（既存APIとの互換性）"""
    subsidies = SubsidyType.objects.all()
    data = [
        {
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'target_business_type': getattr(s, 'target_business_type', ''),
            'max_amount': s.max_amount,
            'requirements': s.requirements
        } for s in subsidies
    ]
    return Response(data)

@api_view(['GET'])
def conversation_history(request, session_id):
    """会話履歴取得API（既存APIとの互換性）"""
    history = ConversationManager.get_conversation_history(session_id)
    data = [
        {
            'message_type': h.message_type,
            'content': h.content,
            'timestamp': h.timestamp.isoformat()
        } for h in history
    ]
    return Response(data)

def get_user_session_info(request):
    """
    ユーザーセッション情報を取得
    """
    session_info = {
        'is_authenticated': request.user.is_authenticated,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'session_key': request.session.session_key,
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'ip_address': request.META.get('REMOTE_ADDR', ''),
    }
    
    return session_info

# カスタムエラーページ

def custom_404(request, exception):
    """
    カスタム404エラーページ
    """
    context = {
        'page_title': 'ページが見つかりません',
        'error_code': 404,
        'error_message': 'お探しのページは見つかりませんでした。',
        'suggestions': [
            'URLを確認してください',
            'メインページに戻る',
            'サイト内検索を利用する'
        ]
    }
    return render(request, 'advisor/error.html', context, status=404)

def custom_500(request):
    """
    カスタム500エラーページ
    """
    context = {
        'page_title': 'サーバーエラー',
        'error_code': 500,
        'error_message': 'サーバーで問題が発生しました。',
        'suggestions': [
            'しばらく時間をおいてから再度お試しください',
            '問題が続く場合は管理者にお問い合わせください'
        ]
    }
    return render(request, 'advisor/error.html', context, status=500)


@csrf_exempt
def enhanced_chat_api(request):
    """
    Enhanced Chat API エンドポイント（フォールバック対応）
    
    POST /advisor/api/enhanced-chat/
    """
    
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
        user_context = data.get('user_context', {})
        
        # 入力検証
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
        
        # サービスの選択
        try:
            # 強化版サービスを試行
            if ENHANCED_SERVICES_AVAILABLE and EnhancedChatService:
                chat_service = EnhancedChatService()
                result = chat_service.process_conversation(
                    message=message,
                    session_id=session_id,
                    user_context=user_context
                )
                service_type = 'enhanced'
            else:
                # フォールバック：既存サービスを使用
                advisor_service = AIAdvisorService()
                result = advisor_service.analyze_question(
                    question_text=message,
                    user_context=user_context
                )
                service_type = 'basic'
                
                # レスポンス形式を統一
                result = {
                    'answer': result.get('answer', '申し訳ございません。回答を生成できませんでした。'),
                    'recommended_subsidies': result.get('recommended_subsidies', []),
                    'confidence_score': result.get('confidence_score', 0.5),
                    'model_used': result.get('model_used', 'basic-fallback')
                }
            
            # 会話履歴を保存
            ConversationManager.save_conversation(
                session_id=session_id,
                user=request.user if request.user.is_authenticated else None,
                message_type='user',
                content=message
            )
            
            ConversationManager.save_conversation(
                session_id=session_id,
                user=request.user if request.user.is_authenticated else None,
                message_type='assistant',
                content=result.get('answer', '')
            )
            
            # 推奨補助金の情報を追加
            recommended_subsidies_info = []
            if result.get('recommended_subsidies'):
                for subsidy in result['recommended_subsidies']:
                    if hasattr(subsidy, 'name'):
                        recommended_subsidies_info.append({
                            'name': subsidy.name,
                            'description': subsidy.description,
                            'max_amount': subsidy.max_amount
                        })
            
            return JsonResponse({
                'success': True,
                'session_id': session_id,
                'response': {
                    'answer': result.get('answer', ''),
                    'recommended_subsidies': recommended_subsidies_info,
                    'confidence_score': result.get('confidence_score', 0.5),
                    'model_used': result.get('model_used', f'{service_type}-service')
                },
                'timestamp': timezone.now().isoformat(),
                'user_context': user_context,
                'service_type': service_type
            })
            
        except Exception as service_error:
            print(f"Service error: {service_error}")
            
            # 最終フォールバック：シンプルな応答
            simple_response = generate_simple_response(message)
            
            return JsonResponse({
                'success': True,
                'session_id': session_id,
                'response': {
                    'answer': simple_response,
                    'recommended_subsidies': [],
                    'confidence_score': 0.3,
                    'model_used': 'simple-fallback'
                },
                'timestamp': timezone.now().isoformat(),
                'user_context': user_context,
                'service_type': 'fallback'
            })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
        
    except Exception as e:
        print(f"Enhanced Chat API error: {e}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': 'サーバー内部エラーが発生しました'
        }, status=500)


def generate_simple_response(message):
    """
    シンプルな応答生成（最終フォールバック）
    """
    message_lower = message.lower()
    
    # キーワードベースの簡単な応答
    if any(keyword in message_lower for keyword in ['it導入', 'ＩＴ導入', 'デジタル化', 'システム']):
        return """
## 🖥️ IT導入補助金について

IT導入補助金は、中小企業・小規模事業者のITツール導入を支援する制度です。

### 主な特徴
- **補助上限**: 450万円
- **対象**: 会計ソフト、受発注システム、ECサイト等
- **補助率**: 1/2以内
- **必要条件**: gBizIDプライム取得、SECURITY ACTION実施

### 申請の流れ
1. gBizIDプライムの取得
2. SECURITY ACTIONの実施  
3. ITツールの選定
4. 申請書類の作成・提出

詳しい要件や申請方法については、最新の公募要領をご確認ください。
"""
    
    elif any(keyword in message_lower for keyword in ['省力化', '人手不足', '自動化', 'ai', 'iot']):
        return """
## 🤖 省力化投資補助金について

省力化投資補助金は、人手不足解消と生産性向上を支援する制度です。

### 主な特徴
- **補助上限**: 1,000万円
- **対象**: AI・IoT・ロボット等の省力化設備
- **補助率**: 1/2以内
- **目的**: 人手不足解消、生産性向上

### 重要なポイント
1. 省力化効果の定量的説明が必要
2. 3年間の事業継続が条件
3. 付加価値額の向上計画が必要

人手不足にお困りの場合は、ぜひご検討ください。
"""
    
    elif any(keyword in message_lower for keyword in ['小規模', '持続化', '販路開拓']):
        return """
## 🏢 小規模事業者持続化補助金について

小規模事業者の販路開拓等を支援する補助金です。

### 一般型の特徴
- **補助上限**: 50万円
- **対象**: 販路開拓、認知度向上の取組
- **補助率**: 2/3以内
- **申請**: 商工会議所等の支援が必要

### 創業型の特徴
- **補助上限**: 200万円
- **対象**: 創業5年以内の小規模事業者
- **用途**: 販路開拓、ブランディング等

小規模事業者の皆様の事業発展を支援する重要な制度です。
"""
    
    elif any(keyword in message_lower for keyword in ['ものづくり', '製造', '設備投資']):
        return """
## 🏭 ものづくり補助金について

革新的サービス開発・設備投資を支援する補助金です。

### 主な特徴
- **補助上限**: 1,250万円（デジタル枠）
- **対象**: 革新的な設備投資、サービス開発
- **補助率**: 1/2以内
- **条件**: 付加価値額年率平均3%以上向上

### 申請のポイント
1. 革新性・独自性の明確化
2. 具体的な成果目標の設定
3. 投資対効果の説明

製造業や革新的なサービス開発をお考えの方におすすめです。
"""
    
    else:
        return """
## 💡 補助金制度について

ご質問ありがとうございます。補助金制度について簡単にご説明します。

### 主要な補助金制度
- **IT導入補助金**: デジタル化支援
- **省力化投資補助金**: 人手不足解消・自動化
- **ものづくり補助金**: 設備投資・革新的開発
- **小規模事業者持続化補助金**: 販路開拓支援

### 選択のポイント
1. **事業規模**: 小規模事業者 vs 中小企業
2. **目的**: デジタル化 vs 設備投資 vs 販路拡大
3. **投資額**: 50万円～1,000万円超
4. **準備期間**: 4週間～14週間

より詳しい情報については、具体的な補助金名でお尋ねください。
例：「IT導入補助金について教えて」
"""

@csrf_exempt
def enhanced_chat_api(request):
    """Enhanced Chat API - 緊急修正版"""
    
    print(f"Enhanced Chat API called: {request.method}")  # デバッグ用
    
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
        
        print(f"Received message: {message}")  # デバッグ用
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'メッセージが入力されていません'
            }, status=400)
        
        # キーワードベースの応答生成
        response_text = generate_simple_response_for_api(message)
        
        print(f"Generated response length: {len(response_text)}")  # デバッグ用
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'response': {
                'answer': response_text,
                'recommended_subsidies': [],
                'confidence_score': 0.8,
                'model_used': 'emergency-fix'
            },
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        print(f"Enhanced Chat API Error: {e}")  # デバッグ用
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': f'サーバーエラーが発生しました: {str(e)}'
        }, status=500)

def generate_simple_response_for_api(message):
    """キーワードベースの簡単な応答生成"""
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ['it導入', 'ＩＴ導入', 'デジタル化']):
        return """## 🖥️ IT導入補助金について

IT導入補助金は、中小企業・小規模事業者のITツール導入を支援する補助金制度です。

### 📋 基本情報
- **補助上限額**: 450万円
- **補助率**: 1/2以内
- **対象者**: 中小企業・小規模事業者

### 💻 対象となるITツール
- 会計ソフト
- 受発注システム  
- 決済ソフト
- ECサイト構築ツール
- 顧客管理システム

### ✅ 申請の必須条件
1. **gBizIDプライム**の取得
2. **SECURITY ACTION**の実施
3. 労働生産性向上の計画策定

### 📈 導入効果
デジタル化により業務効率が向上し、売上アップや労働時間短縮が期待できます。

ご不明な点があれば、お気軽にお尋ねください！"""

    elif any(keyword in message_lower for keyword in ['省力化', '人手不足', '自動化']):
        return """## 🤖 省力化投資補助金について

省力化投資補助金は、人手不足解消と生産性向上を目的とした補助金制度です。

### 📋 基本情報
- **補助上限額**: 1,000万円
- **補助率**: 1/2以内
- **対象者**: 中小企業・小規模事業者

### 🔧 対象となる設備
- AI・IoT機器
- ロボット・自動化装置
- センサー・制御システム
- 省力化ソフトウェア

### ✅ 申請要件
1. **省力化効果**の定量的説明
2. **3年間の事業継続**
3. 付加価値額の向上計画

### 📈 期待される効果
人手不足の解消と同時に、作業効率の大幅な向上が見込めます。

具体的な設備についてもご相談ください！"""

    else:
        return """## 💡 補助金制度のご案内

ご質問ありがとうございます！主要な補助金制度をご紹介します。

### 🏆 人気の補助金制度

#### 🖥️ IT導入補助金
- デジタル化・業務効率化（上限450万円）

#### 🤖 省力化投資補助金  
- 人手不足解消・自動化（上限1,000万円）

#### 🏭 ものづくり補助金
- 設備投資・革新的開発（上限1,250万円）

#### 🏢 小規模事業者持続化補助金
- 販路開拓・認知度向上（上限50万円）

### 💬 お困りのことは？
- 「IT導入補助金について詳しく」
- 「人手不足を解消したい」
- 「設備投資を考えている」

具体的にお聞かせください！"""