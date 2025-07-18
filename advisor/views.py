# advisor/views.py - 完全版（文脈対応機能付き）
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

# === 文脈対応版 Enhanced Chat API ===


@csrf_exempt
def debug_conversation_history(request):
    """会話履歴のデバッグ用エンドポイント（GET: テンプレート表示, API: JSON応答）"""
    
    if request.method == 'GET':
        session_id = request.GET.get('session_id')
        
        # session_idが指定されていない場合はテンプレートを表示
        if not session_id:
            return render(request, 'advisor/debug_history.html', {
                'page_title': '会話履歴デバッグ',
                'description': 'セッション別会話履歴の詳細表示・分析ツール'
            })
        
        # session_idが指定されている場合はJSON応答
        try:
            # 会話履歴を取得
            history = ConversationHistory.objects.filter(
                session_id=session_id
            ).order_by('timestamp')
            
            if not history.exists():
                return JsonResponse({
                    'error': f'セッションID "{session_id}" の会話履歴が見つかりません',
                    'session_id': session_id,
                    'total_messages': 0,
                    'history': []
                }, status=404)
            
            history_data = []
            for h in history:
                history_data.append({
                    'id': h.id,
                    'session_id': h.session_id,
                    'message_type': h.message_type,
                    'content': h.content,
                    'timestamp': h.timestamp.isoformat(),
                    'user_context': getattr(h, 'user_context', {})
                })
            
            # 統計情報の計算
            user_messages = [h for h in history_data if h['message_type'] == 'user']
            assistant_messages = [h for h in history_data if h['message_type'] == 'assistant']
            
            # 会話時間の計算
            duration_minutes = 0
            if len(history_data) > 1:
                first_time = timezone.datetime.fromisoformat(history_data[0]['timestamp'].replace('Z', '+00:00'))
                last_time = timezone.datetime.fromisoformat(history_data[-1]['timestamp'].replace('Z', '+00:00'))
                duration_minutes = (last_time - first_time).total_seconds() / 60
            
            response_data = {
                'session_id': session_id,
                'total_messages': len(history_data),
                'user_messages_count': len(user_messages),
                'assistant_messages_count': len(assistant_messages),
                'duration_minutes': round(duration_minutes, 1),
                'first_message_time': history_data[0]['timestamp'] if history_data else None,
                'last_message_time': history_data[-1]['timestamp'] if history_data else None,
                'history': history_data
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"Debug history error: {e}")
            return JsonResponse({
                'error': f'履歴取得中にエラーが発生しました: {str(e)}',
                'session_id': session_id
            }, status=500)
    
    else:
        return JsonResponse({
            'error': 'GET method required'
        }, status=405)





@csrf_exempt
def enhanced_chat_api(request):
    """Enhanced Chat API - メッセージ順序修正版"""
    
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
        
        print(f"=== Enhanced Chat API Debug (Fixed) ===")
        print(f"💬 Current Message: {message}")
        print(f"🆔 Session ID: {session_id}")
        print(f"👤 User Context: {user_context}")
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'メッセージが入力されていません'
            }, status=400)
        
        # Step 1: 現在のメッセージを保存（履歴分析前に）
        print(f"💾 Saving current user message first...")
        current_user_message = ConversationHistory.objects.create(
            session_id=session_id,
            message_type='user',
            content=message,
            user_context=user_context,
            timestamp=timezone.now()
        )
        print(f"✅ Current user message saved: ID={current_user_message.id}")
        
        # Step 2: 会話履歴の分析（現在のメッセージを含む）
        conversation_context = analyze_conversation_history_fixed(session_id, message)
        print(f"🔍 Analyzed context: {conversation_context}")
        
        # Step 3: 文脈を考慮した応答生成
        response_text = generate_contextual_response_fixed(message, conversation_context, user_context)
        
        # Step 4: アシスタントメッセージを保存
        assistant_conversation = ConversationHistory.objects.create(
            session_id=session_id,
            message_type='assistant',
            content=response_text,
            user_context={'generated_response': True},
            timestamp=timezone.now()
        )
        print(f"✅ Assistant message saved: ID={assistant_conversation.id}")
        
        # Step 5: 最終確認
        total_history = ConversationHistory.objects.filter(session_id=session_id).count()
        print(f"📚 Total history count: {total_history}")
        print("✅ Contextual response generated successfully")
        print("=== End Debug ===")
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'response': {
                'answer': response_text,
                'recommended_subsidies': [],
                'confidence_score': 0.9,
                'model_used': 'context-aware-fixed',
                'context_used': True,
                'conversation_flow': conversation_context.get('flow_type', 'continuation'),
                'debug_info': {
                    'current_message': message,
                    'previous_messages': conversation_context.get('message_count', 0),
                    'recent_topics': conversation_context.get('recent_topics', []),
                    'flow_type': conversation_context.get('flow_type', 'unknown')
                }
            },
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Enhanced Chat API Error: {e}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': f'サーバーエラーが発生しました: {str(e)}'
        }, status=500)

def determine_current_message_flow(message):
    """現在のメッセージのフローを判定"""
    
    message_lower = message.lower()
    print(f"🔍 Determining flow for current message: '{message_lower}'")
    
    # 質問のタイプを判定
    flow_patterns = {
        'adoption_tips': ['採択率', '通る', '受かる', '成功', '勝率'],
        'detail_request': ['詳しく', 'もっと', '具体的', '教えて'],
        'process_inquiry': ['申請', '手続き', 'やり方', '方法'],
        'amount_inquiry': ['いくら', '金額', '予算', '費用']
    }
    
    for flow_type, keywords in flow_patterns.items():
        found_keywords = [kw for kw in keywords if kw in message_lower]
        if found_keywords:
            print(f"   ✅ Flow: {flow_type} (keywords: {found_keywords})")
            return flow_type
    
    print(f"   → Flow: unknown (no specific pattern)")
    return 'unknown'

def analyze_conversation_history_fixed(session_id, current_message):
    """会話履歴を分析して文脈を理解（修正版）"""
    
    print(f"📊 Analyzing conversation history for session: {session_id}")
    print(f"📝 Current message: '{current_message}'")
    
    # 現在のメッセージより前の履歴を取得
    previous_history = ConversationHistory.objects.filter(
        session_id=session_id
    ).order_by('-timestamp')[:6]  # 最新6件（現在のメッセージは除く）
    
    print(f"📚 Found {previous_history.count()} previous messages")
    
    context = {
        'recent_messages': [],
        'recent_topics': [],
        'discussed_subsidies': [],
        'flow_type': 'initial',
        'user_interests': [],
        'message_count': previous_history.count() + 1,  # 現在のメッセージを含む
        'current_message': current_message
    }
    
    # Step 1: 現在のメッセージを最優先で分析
    print(f"🎯 Analyzing current message: '{current_message}'")
    current_topics = extract_topics_from_message_debug(current_message)
    current_subsidies = extract_subsidy_names_debug(current_message)
    current_flow = determine_current_message_flow(current_message)
    
    print(f"   Current topics: {current_topics}")
    print(f"   Current subsidies: {current_subsidies}")
    print(f"   Current flow: {current_flow}")
    
    # Step 2: 過去の履歴から文脈を抽出
    historical_topics = []
    historical_subsidies = []
    
    for entry in previous_history:
        print(f"   Processing historical: [{entry.message_type}] {entry.content[:50]}...")
        
        context['recent_messages'].append({
            'type': entry.message_type,
            'content': entry.content[:100],
            'timestamp': entry.timestamp
        })
        
        # 過去のトピック・補助金を収集
        if entry.message_type == 'user':
            h_topics = extract_topics_from_message_debug(entry.content)
            historical_topics.extend(h_topics)
        
        h_subsidies = extract_subsidy_names_debug(entry.content)
        historical_subsidies.extend(h_subsidies)
    
    # Step 3: 文脈の決定（現在 > 過去の順）
    if current_topics:
        # 現在のメッセージにトピックがある場合は最優先
        context['recent_topics'] = current_topics + list(set(historical_topics))
        print(f"   ✅ Using current topics as primary: {current_topics}")
    else:
        # 現在のメッセージにトピックがない場合は過去から継承
        context['recent_topics'] = list(set(historical_topics))
        print(f"   📚 Inheriting historical topics: {historical_topics}")
    
    # 補助金名も同様
    if current_subsidies:
        context['discussed_subsidies'] = current_subsidies + list(set(historical_subsidies))
    else:
        context['discussed_subsidies'] = list(set(historical_subsidies))
    
    # フローは現在のメッセージを基準に
    if current_flow != 'unknown':
        context['flow_type'] = current_flow
        print(f"   🎯 Using current flow: {current_flow}")
    elif len(previous_history) <= 1:
        context['flow_type'] = 'initial'
        print(f"   🌱 Setting as initial conversation")
    else:
        context['flow_type'] = 'continuation'
        print(f"   ➡️ Setting as continuation")
    
    # 重複削除
    context['recent_topics'] = list(dict.fromkeys(context['recent_topics']))  # 順序保持で重複削除
    context['discussed_subsidies'] = list(dict.fromkeys(context['discussed_subsidies']))
    
    print(f"📋 Final context summary:")
    print(f"   - Topics (current first): {context['recent_topics']}")
    print(f"   - Subsidies: {context['discussed_subsidies']}")
    print(f"   - Flow: {context['flow_type']}")
    
    return context



def extract_topics_from_message_debug(message):
    """メッセージからトピック（補助金種別）を抽出（デバッグ版）"""
    
    topics = []
    message_lower = message.lower()
    
    print(f"🔍 Extracting topics from: '{message_lower}'")
    
    # キーワードマッピング
    topic_keywords = {
        '省力化': ['省力化', '人手不足', '自動化', 'ai', 'iot', 'ロボット'],
        'IT導入': ['it導入', 'ＩＴ導入', 'デジタル化', 'システム', 'ソフトウェア'],
        'ものづくり': ['ものづくり', '製造', '設備投資', '機械', '工場'],
        '小規模事業者': ['小規模', '持続化', '販路開拓', '認知度'],
        '事業再構築': ['再構築', '転換', '新事業', '多角化'],
    }
    
    for topic, keywords in topic_keywords.items():
        found_keywords = []
        for keyword in keywords:
            if keyword in message_lower:
                found_keywords.append(keyword)
        
        if found_keywords:
            topics.append(topic)
            print(f"   ✅ Found topic '{topic}' with keywords: {found_keywords}")
    
    return topics


def extract_subsidy_names_debug(content):
    """コンテンツから補助金名を抽出（デバッグ版）"""
    
    subsidies = []
    content_lower = content.lower()
    
    # 主要な補助金名
    subsidy_names = [
        'IT導入補助金',
        '省力化投資補助金', 
        'ものづくり補助金',
        '小規模事業者持続化補助金',
        '事業再構築補助金'
    ]
    
    for name in subsidy_names:
        if name.lower() in content_lower:
            subsidies.append(name)
            print(f"   🎯 Found subsidy name: {name}")
    
    return subsidies



def determine_conversation_flow_debug(recent_messages):
    """会話の流れを判定（修正版）"""
    
    print(f"🎭 Determining conversation flow from {len(recent_messages)} messages")
    
    # 最新のユーザーメッセージを分析
    latest_user_msg = None
    for msg in recent_messages:
        if msg['type'] == 'user':
            latest_user_msg = msg['content'].lower()
            print(f"   Latest user message: '{latest_user_msg}'")
            break
    
    if not latest_user_msg:
        print("   → Flow: initial (no user message found)")
        return 'initial'
    
    # 質問のタイプを判定（メッセージ数の条件を削除）
    flow_patterns = {
        'adoption_tips': ['採択率', '通る', '受かる', '成功', '勝率'],
        'detail_request': ['詳しく', 'もっと', '具体的', '教えて'],
        'process_inquiry': ['申請', '手続き', 'やり方', '方法'],
        'amount_inquiry': ['いくら', '金額', '予算', '費用']
    }
    
    for flow_type, keywords in flow_patterns.items():
        found_keywords = [kw for kw in keywords if kw in latest_user_msg]
        if found_keywords:
            print(f"   ✅ Flow: {flow_type} (keywords: {found_keywords})")
            return flow_type
    
    # メッセージ数による判定は最後に
    if len(recent_messages) <= 1:
        print("   → Flow: initial (very few messages)")
        return 'initial'
    else:
        print("   → Flow: continuation (no specific pattern)")
        return 'continuation'


def generate_contextual_response_fixed(message, context, user_context):
    """文脈を考慮した応答を生成（修正版）"""
    
    recent_topics = context.get('recent_topics', [])
    flow_type = context.get('flow_type', 'initial')
    discussed_subsidies = context.get('discussed_subsidies', [])
    current_message = context.get('current_message', message)
    
    print(f"🎯 Generating contextual response:")
    print(f"   Current message: {current_message}")
    print(f"   Flow type: {flow_type}")
    print(f"   Recent topics (priority order): {recent_topics}")
    print(f"   Discussed subsidies: {discussed_subsidies}")
    
    # 文脈に応じた応答生成
    if flow_type == 'adoption_tips' and recent_topics:
        # 採択率向上のアドバイス
        primary_topic = recent_topics[0]  # 最優先トピック
        print(f"   ✅ Generating adoption tips for: {primary_topic}")
        return generate_adoption_tips_response(primary_topic, current_message)
    
    elif flow_type == 'detail_request' and recent_topics:
        # 詳細情報の提供
        primary_topic = recent_topics[0]
        print(f"   ✅ Generating detailed response for: {primary_topic}")
        return generate_detailed_response(primary_topic, current_message)
    
    elif flow_type == 'process_inquiry' and recent_topics:
        # 申請プロセスの説明
        primary_topic = recent_topics[0]
        print(f"   ✅ Generating process response for: {primary_topic}")
        return generate_process_response(primary_topic, current_message)
    
    elif flow_type == 'amount_inquiry' and recent_topics:
        # 金額・予算の説明
        primary_topic = recent_topics[0]
        print(f"   ✅ Generating amount response for: {primary_topic}")
        return generate_amount_response(primary_topic, current_message)
    
    else:
        # 新しいトピックまたは一般的な質問
        print(f"   ✅ Generating general/new topic response")
        return generate_simple_response_for_api(current_message)
    


def generate_adoption_tips_response(topic, message):
    """採択率向上のアドバイスを生成"""
    
    if topic == '省力化':
        return """## 🎯 省力化投資補助金の採択率向上のコツ

### 📈 採択されやすいポイント

#### 1. **省力化効果の定量化**
- 「作業時間50%削減」「人件費月30万円削減」など具体的数値
- 導入前後の比較表を作成
- ROI（投資回収期間）を明確に示す

#### 2. **人手不足の深刻さをアピール**
- 現在の人手不足状況を具体的に記載
- 求人活動の状況（応募者数、採用の困難さ）
- 事業への影響（売上機会の損失など）

#### 3. **技術的な革新性**
- AI・IoT・ロボティクスなど最新技術の活用
- 従来手法との違いを明確に説明
- 業界での先進性をアピール

#### 4. **事業計画の実現可能性**
- 段階的導入スケジュール
- リスク対策の明記
- 過去の設備投資実績

#### 5. **地域・業界への波及効果**
- 同業他社への波及効果
- 地域雇用への貢献
- 技術普及への寄与

### 📋 提出書類の品質向上
- **事業計画書**: 論理的で読みやすい構成
- **収支計画**: 保守的で現実的な数値
- **見積書**: 複数業者からの相見積もり

**採択率は約50-60%**です。これらのポイントを押さえて申請しましょう！"""

    elif topic == 'IT導入':
        return """## 🎯 IT導入補助金の採択率向上のコツ

### 📈 採択されやすいポイント

#### 1. **生産性向上効果の明確化**
- 業務時間短縮の具体的な時間数
- 売上向上の見込み数値
- コスト削減効果の算出

#### 2. **デジタル化の必要性**
- 現在の業務の非効率性
- 競合他社との差別化
- 顧客サービス向上の必要性

#### 3. **適切なITツールの選定**
- 業務に最適化されたツール
- 実績のあるベンダー
- サポート体制の充実

#### 4. **SECURITY ACTIONの実施**
- ★一つ星または★★二つ星の取得
- セキュリティ対策の明記
- 情報管理体制の整備

#### 5. **導入後の活用計画**
- 従業員への研修計画
- 段階的な機能活用
- 効果測定の方法

### 📋 重要な準備事項
- **gBizIDプライム**の事前取得
- **労働生産性向上**の3年計画
- **ITツール事業者**との事前相談

**採択率は約60-70%**です。事前準備をしっかりと行いましょう！"""

    else:
        return generate_general_adoption_tips(topic)


def generate_detailed_response(topic, message):
    """詳細情報を提供"""
    
    if topic == '省力化':
        return """## 🤖 省力化投資補助金 詳細ガイド

### 📋 制度概要
**正式名称**: 中小企業省力化投資補助事業
**実施主体**: 中小企業庁
**予算規模**: 1,000億円（令和5年度補正）

### 💰 補助内容

#### 補助上限・率
- **従業員数5名以下**: 200万円
- **従業員数6-20名**: 500万円  
- **従業員数21名以上**: 1,000万円
- **補助率**: 1/2以内

#### 対象経費
✅ **対象となる経費**
- AI・IoT・ロボット等の機械装置
- 専用ソフトウェア
- 制御・検査システム
- 設置・調整費用

❌ **対象外の経費**
- 汎用的なパソコン・タブレット
- 既存システムの改修費
- 保守・メンテナンス費用
- 人件費・土地建物費

### 🏢 対象事業者
- **中小企業・小規模事業者**
- **業種**: 製造業、建設業、運輸業、小売業等
- **条件**: 人手不足に直面している事業者

### 📅 申請スケジュール
- **公募開始**: 年2-3回
- **申請期間**: 約6-8週間
- **審査期間**: 約2-3ヶ月
- **事業期間**: 交付決定後12ヶ月以内

### 📈 期待される効果
- **労働生産性**: 年平均3%以上向上
- **人手不足解消**: 作業の自動化・効率化
- **売上拡大**: 生産能力向上による受注増加

### ⚠️ 注意点
- 交付決定前の発注・契約は補助対象外
- 3年間の事業継続義務
- 年次報告書の提出が必要

詳しい申請要件は最新の公募要領でご確認ください！"""

    elif topic == 'IT導入':
        return """## 🖥️ IT導入補助金 詳細ガイド

### 📋 制度概要
**正式名称**: IT導入補助金2024
**実施主体**: 一般社団法人サービスデザイン推進協議会
**目的**: 中小企業・小規模事業者のITツール導入支援

### 💰 補助内容

#### 通常枠（A・B類型）
- **A類型**: 5万円～150万円未満（補助率1/2）
- **B類型**: 150万円～450万円以下（補助率1/2）

#### デジタル化基盤導入枠
- **デジタル化基盤導入類型**: 5万円～350万円
  - 5万円～50万円：補助率3/4
  - 50万円超～350万円：補助率2/3

#### セキュリティ対策推進枠
- **上限額**: 100万円
- **補助率**: 1/2以内

### 🛠️ 対象ITツール

#### A類型
- 会計ソフト、受発注ソフト
- 決済ソフト、ECソフト

#### B類型  
- 上記に加えて
- 顧客管理、在庫管理
- 人事・給与管理システム

#### デジタル化基盤導入類型
- 会計・受発注・決済・ECソフト
- PC・タブレット・プリンター
- レジ・券売機

### 📋 申請要件

#### 必須条件
1. **gBizIDプライム**の取得
2. **SECURITY ACTION**の実施
3. **労働生産性向上計画**の策定

#### 申請の流れ
1. ITツール・IT導入支援事業者の選定
2. 交付申請の提出
3. ITツール導入・支払い
4. 実績報告書の提出

### 📈 導入効果例
- **業務時間短縮**: 月40時間削減
- **売上向上**: 年10%増加
- **顧客満足度向上**: レスポンス時間50%短縮

### ⚠️ 重要なポイント
- IT導入支援事業者との連携必須
- 3年間の生産性向上報告義務
- セキュリティ対策の継続実施

最新の対象ITツールは公式サイトでご確認ください！"""

    else:
        return generate_general_detailed_response(topic)


def generate_process_response(topic, message):
    """申請プロセスの説明"""
    
    if topic == '省力化':
        return """## 📋 省力化投資補助金 申請プロセス

### STEP 1: 事前準備（公募開始前）

#### 🔍 情報収集
- 最新の公募要領を確認
- 対象設備の調査・選定
- 複数業者からの見積もり取得

#### 📊 計画策定
- 省力化効果の試算
- 投資回収計画の作成
- 3年間の事業計画策定

### STEP 2: 申請書類作成（4-6週間）

#### 📝 必要書類
1. **事業計画書**
   - 現状分析と課題
   - 導入設備の詳細
   - 省力化効果の説明

2. **経費明細書**
   - 設備・工事費の内訳
   - 見積書の添付
   - 経費の妥当性説明

3. **添付書類**
   - 決算書（直近2期分）
   - 登記事項証明書
   - 従業員数を証明する書類

### STEP 3: 申請・審査（8-12週間）

#### 📤 申請手続き
- 電子申請システムからの提出
- 必要書類のアップロード
- 申請内容の最終確認

#### 🔍 審査項目
1. **政策的意義**（30点）
   - 人手不足解消への貢献
   - 地域経済への波及効果

2. **技術的優位性**（25点）
   - 技術の革新性
   - 導入効果の確実性

3. **事業化能力**（25点）
   - 事業計画の実現可能性
   - 経営基盤の安定性

4. **費用対効果**（20点）
   - 投資効率の妥当性
   - 価格の適正性

### STEP 4: 交付決定・事業実施

#### ✅ 交付決定後の手続き
1. **事業開始届**の提出
2. 設備の発注・契約
3. 設備導入・設置工事
4. 検収・支払い

#### 📊 実績報告
- **実績報告書**の提出
- **証拠書類**の添付
- **確定検査**の実施

### STEP 5: 補助金の受給

#### 💰 補助金の入金
- 確定検査完了後
- 通常1-2ヶ月で入金
- 補助金額の確定通知

#### 📈 事後管理
- **年次報告書**の提出（3年間）
- **処分制限**の遵守
- **情報開示**への協力

### ⏰ スケジュール目安
- **準備期間**: 2-3ヶ月
- **申請～交付決定**: 3-4ヶ月  
- **事業実施期間**: 12ヶ月以内
- **実績報告～入金**: 2-3ヶ月

**総期間**: 約18-24ヶ月

早めの準備開始をおすすめします！"""

    else:
        return generate_general_process_response(topic)


def generate_amount_response(topic, message):
    """金額・予算の説明"""
    
    if topic == '省力化':
        return """## 💰 省力化投資補助金の金額詳細

### 📊 補助上限額（従業員数別）

#### 小規模事業者
- **従業員5名以下**: **最大200万円**
- 補助率: 1/2
- 最低投資額: 400万円～

#### 中小企業
- **従業員6-20名**: **最大500万円**  
- **従業員21名以上**: **最大1,000万円**
- 補助率: 1/2
- 最低投資額: 1,000万円～2,000万円～

### 💡 実際の投資例

#### ケース1: 製造業（従業員15名）
- **導入設備**: AI検査システム
- **総投資額**: 800万円
- **補助金額**: 400万円（上限500万円以内）
- **自己負担**: 400万円

#### ケース2: 建設業（従業員30名）
- **導入設備**: 自動測量ドローン + AI解析
- **総投資額**: 1,500万円  
- **補助金額**: 750万円（上限1,000万円以内）
- **自己負担**: 750万円

#### ケース3: 小売業（従業員8名）
- **導入設備**: 自動梱包システム
- **総投資額**: 600万円
- **補助金額**: 300万円（上限500万円以内）
- **自己負担**: 300万円

### 📋 対象経費の詳細

#### ✅ 補助対象経費
- **機械装置費**: AI・IoT機器、ロボット
- **システム構築費**: 専用ソフトウェア、制御系
- **設置工事費**: 据付・配線・調整作業

#### ❌ 対象外経費  
- 汎用パソコン・タブレット
- 既存システム改修費
- 保守・メンテナンス契約
- 消耗品・予備品

### 💸 資金調達のポイント

#### 自己資金の確保
- 総投資額の50%以上の準備が必要
- 運転資金への影響を考慮
- 設備投資後のキャッシュフローを試算

#### 金融機関との連携
- 設備資金融資の活用
- 補助金を担保とした融資制度
- 事業計画書の共有で融資交渉を有利に

### 📈 投資回収の目安

#### 一般的な回収期間
- **人件費削減効果**: 年200-500万円
- **売上向上効果**: 年300-800万円
- **投資回収期間**: 2-4年

#### ROI（投資収益率）試算
- **良好な案件**: ROI 25-40%
- **標準的な案件**: ROI 15-25%
- **最低ライン**: ROI 10%以上

### 💡 予算計画のコツ
1. **保守的な効果試算**で計画
2. **予備費10-20%**を確保
3. **段階的導入**でリスク分散
4. **税務上の減価償却**も考慮

設備投資は企業の将来を左右する重要な決定です。慎重な計画を立てましょう！"""

    else:
        return generate_general_amount_response(topic)


def generate_general_response(message):
    """一般的な質問への応答"""
    
    return generate_simple_response_for_api(message)


def generate_general_adoption_tips(topic):
    """一般的な採択率向上アドバイス"""
    
    return f"""## 🎯 {topic}関連補助金の採択率向上のコツ

### 📈 基本的なポイント

#### 1. **事業計画の明確性**
- 現状分析と課題の具体的な記載
- 解決策の論理的な説明
- 期待される効果の定量化

#### 2. **実現可能性の証明**
- 過去の実績や経験
- 専門家やパートナーとの連携
- リスク対策の明記

#### 3. **政策目標との整合性**
- 国の施策方針との合致
- 地域経済への貢献
- 業界全体への波及効果

### 📋 申請書類の品質向上
- 読みやすい構成と文章
- 図表やグラフの効果的な活用  
- 誤字脱字のない正確な記載

より具体的なアドバイスが必要でしたら、詳しい状況をお聞かせください！"""


def generate_general_detailed_response(topic):
    """一般的な詳細応答"""
    
    return f"""## 📋 {topic}関連補助金について

申し訳ございませんが、{topic}に関する詳細情報については、具体的な補助金名を教えていただけますでしょうか？

### 💡 主要な補助金制度
- **IT導入補助金**: デジタル化支援
- **省力化投資補助金**: 人手不足解消・自動化  
- **ものづくり補助金**: 設備投資・革新的開発
- **小規模事業者持続化補助金**: 販路開拓支援

具体的な補助金名でお尋ねいただければ、詳しい情報をご提供できます！"""


def generate_general_process_response(topic):
    """一般的なプロセス応答"""
    
    return f"""## 📋 {topic}関連補助金の申請プロセス

### 基本的な申請の流れ

#### STEP 1: 事前準備
- 公募要領の確認
- 申請要件のチェック
- 必要書類の準備

#### STEP 2: 申請書作成
- 事業計画書の作成
- 経費明細書の準備
- 添付書類の収集

#### STEP 3: 申請・審査
- 電子申請システムでの提出
- 審査期間（通常2-3ヶ月）
- 結果通知

#### STEP 4: 事業実施
- 交付決定後の事業開始
- 実績報告書の提出
- 補助金の受給

より詳しいプロセスについては、具体的な補助金名を教えてください！"""


def generate_general_amount_response(topic):
    """一般的な金額応答"""
    
    return f"""## 💰 {topic}関連補助金の金額について

### 主要補助金の金額範囲

#### IT導入補助金
- **通常枠**: 5万円～450万円
- **デジタル化基盤導入枠**: 5万円～350万円

#### 省力化投資補助金  
- **上限**: 200万円～1,000万円（従業員数による）

#### ものづくり補助金
- **一般型**: 最大1,250万円
- **グローバル展開型**: 最大3,000万円

#### 小規模事業者持続化補助金
- **通常枠**: 最大50万円
- **特別枠**: 最大200万円

具体的な補助金について詳しく知りたい場合は、補助金名を教えてください！"""


def generate_simple_response_for_api(message):
    """シンプルな応答生成（既存のキーワードベース）"""
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ['it導入', 'ＩＴ導入', 'デジタル化', 'システム']):
        return """## 🖥️ IT導入補助金について

IT導入補助金は、中小企業・小規模事業者のITツール導入を支援する制度です。

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


def save_conversation_message(session_id, message_type, content, context):
    """会話メッセージを保存"""
    
    try:
        ConversationHistory.objects.create(
            session_id=session_id,
            message_type=message_type,
            content=content,
            user_context=context,
            timestamp=timezone.now()
        )
    except Exception as e:
        print(f"会話保存エラー: {e}")
        # エラーが発生しても処理を続行

# === その他の管理・統計機能（既存のまま） ===

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

def session_list(request):
    """セッション一覧表示"""
    from django.db.models import Count, Max, Min
    
    # セッション別の統計を取得
    sessions = ConversationHistory.objects.values('session_id').annotate(
        message_count=Count('id'),
        first_message=Min('timestamp'),
        last_message=Max('timestamp'),
        user_messages=Count('id', filter=models.Q(message_type='user')),
        assistant_messages=Count('id', filter=models.Q(message_type='assistant'))
    ).order_by('-last_message')[:50]  # 最新50セッション
    
    # 各セッションの詳細を追加
    session_list = []
    for session in sessions:
        session_id = session['session_id']
        
        # 最初のユーザーメッセージを取得（セッションの内容を推測）
        first_user_message = ConversationHistory.objects.filter(
            session_id=session_id,
            message_type='user'
        ).first()
        
        # 会話時間を計算
        duration_minutes = 0
        if session['first_message'] and session['last_message']:
            duration = session['last_message'] - session['first_message']
            duration_minutes = int(duration.total_seconds() / 60)
        
        session_list.append({
            'session_id': session_id,
            'message_count': session['message_count'],
            'user_messages': session['user_messages'],
            'assistant_messages': session['assistant_messages'],
            'first_message_time': session['first_message'],
            'last_message_time': session['last_message'],
            'duration_minutes': duration_minutes,
            'preview': first_user_message.content[:100] if first_user_message else '（内容なし）',
            'debug_url': f"/advisor/debug/history/?session_id={session_id}"
        })
    
    context = {
        'page_title': 'セッション一覧',
        'sessions': session_list,
        'total_sessions': len(session_list)
    }
    
    return render(request, 'advisor/session_list.html', context)