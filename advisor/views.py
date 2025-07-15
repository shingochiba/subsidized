# advisor/views.py - 完全版
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
    管理ダッシュボード（スタッフ専用）
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
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
    補助金統計ページ
    """
    from django.db.models import Count, Avg, Max, Min
    
    # 基本統計
    subsidy_stats = SubsidyType.objects.aggregate(
        total_count=Count('id'),
        avg_amount=Avg('max_amount'),
        max_amount=Max('max_amount'),
        min_amount=Min('max_amount')
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
            'target_business_type': getattr(s, 'target_business_type', getattr(s, 'target_business', '')),
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