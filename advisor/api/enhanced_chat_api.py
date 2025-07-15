from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import json
import uuid

from ..services.enhanced_chat_service import EnhancedChatService
from ..services.subsidy_prediction_service import SubsidyPredictionService
from ..models import ConversationHistory, UserAlert

@api_view(['POST'])
@csrf_exempt
def enhanced_chat_conversation(request):
    """
    強化されたチャット会話エンドポイント
    
    POST /api/enhanced-chat/
    {
        "message": "ユーザーのメッセージ",
        "session_id": "オプション：セッションID",
        "user_context": {
            "business_type": "事業種別",
            "company_size": "企業規模",
            "region": "地域"
        }
    }
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
        
        # チャットサービスの初期化
        chat_service = EnhancedChatService()
        
        # 会話処理
        response = chat_service.process_conversation(
            message=message,
            session_id=session_id,
            user_context=user_context
        )
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'response': response,
            'timestamp': timezone.now().isoformat(),
            'user_context': user_context
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
        
    except Exception as e:
        # エラーログ出力（本番環境では適切なログシステムを使用）
        print(f"Enhanced chat API error: {e}")
        
        return JsonResponse({
            'success': False,
            'error': '処理中にエラーが発生しました。もう一度お試しください。',
            'debug_info': str(e) if hasattr(request, 'debug') and request.debug else None
        }, status=500)

@api_view(['GET'])
def subsidy_predictions(request):
    """
    補助金予測データエンドポイント
    
    GET /api/subsidy-predictions/?months=12
    """
    
    try:
        # パラメータ取得
        months_ahead = int(request.GET.get('months', 12))
        
        # 範囲制限
        if months_ahead < 1 or months_ahead > 24:
            return JsonResponse({
                'success': False,
                'error': '月数は1-24の範囲で指定してください'
            }, status=400)
        
        # 予測サービスの初期化
        prediction_service = SubsidyPredictionService()
        
        # データ取得
        predictions = prediction_service.predict_next_opportunities(months_ahead)
        calendar_data = prediction_service.generate_prediction_calendar()
        trends = prediction_service.analyze_subsidy_trends()
        
        # ユーザー固有のアラート
        alerts = []
        if request.user.is_authenticated:
            alerts_qs = UserAlert.objects.filter(
                user=request.user,
                is_dismissed=False
            ).order_by('-created_at')[:20]
            
            alerts = [
                {
                    'id': alert.id,
                    'type': alert.alert_type,
                    'title': alert.title,
                    'message': alert.message,
                    'priority': alert.priority,
                    'action_required': alert.action_required,
                    'deadline': alert.deadline.isoformat() if alert.deadline else None,
                    'is_read': alert.is_read,
                    'created_at': alert.created_at.isoformat()
                }
                for alert in alerts_qs
            ]
        else:
            # 未認証ユーザー向けの一般的なアラート
            alerts = prediction_service.setup_alert_system({})
        
        return JsonResponse({
            'success': True,
            'data': {
                'predictions': predictions,
                'calendar': calendar_data,
                'alerts': alerts,
                'trends': trends,
                'metadata': {
                    'months_ahead': months_ahead,
                    'total_predictions': len(predictions),
                    'generated_at': timezone.now().isoformat()
                }
            }
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': '月数は数値で指定してください'
        }, status=400)
        
    except Exception as e:
        print(f"Prediction API error: {e}")
        
        return JsonResponse({
            'success': False,
            'error': '予測データの取得中にエラーが発生しました'
        }, status=500)

@api_view(['GET'])
def prediction_calendar(request):
    """
    予測カレンダー専用エンドポイント
    
    GET /api/prediction-calendar/?year=2025&month=7
    """
    
    try:
        # パラメータ取得
        year = request.GET.get('year')
        month = request.GET.get('month')
        
        prediction_service = SubsidyPredictionService()
        
        if year and month:
            # 特定月のデータ
            try:
                year = int(year)
                month = int(month)
                
                if month < 1 or month > 12:
                    raise ValueError("Invalid month")
                
                # 特定月の予測データを取得（実装は予測サービス内で）
                calendar_data = prediction_service.generate_prediction_calendar()
                month_key = f"{year}-{month:02d}"
                
                specific_month_data = calendar_data.get(month_key, {
                    'month': f"{year}年{month}月",
                    'opportunities': [],
                    'total_opportunities': 0,
                    'high_priority_count': 0
                })
                
                return JsonResponse({
                    'success': True,
                    'calendar': {month_key: specific_month_data},
                    'requested_month': f"{year}-{month:02d}"
                })
                
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': '年月は正しい数値で指定してください'
                }, status=400)
        else:
            # 全カレンダーデータ
            calendar_data = prediction_service.generate_prediction_calendar()
            
            return JsonResponse({
                'success': True,
                'calendar': calendar_data
            })
        
    except Exception as e:
        print(f"Calendar API error: {e}")
        
        return JsonResponse({
            'success': False,
            'error': 'カレンダーデータの取得中にエラーが発生しました'
        }, status=500)

@api_view(['GET'])
def conversation_history(request):
    """
    会話履歴取得エンドポイント
    
    GET /api/conversation-history/?session_id=xxx&limit=20
    """
    
    try:
        session_id = request.GET.get('session_id')
        limit = int(request.GET.get('limit', 20))
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'session_idが必要です'
            }, status=400)
        
        # 会話履歴取得
        history = ConversationHistory.objects.filter(
            session_id=session_id
        ).order_by('-timestamp')[:limit]
        
        history_data = [
            {
                'id': h.id,
                'message_type': h.message_type,
                'content': h.content,
                'timestamp': h.timestamp.isoformat(),
                'metadata': h.metadata,
                'intent_analysis': h.intent_analysis,
                'user_context': h.user_context
            }
            for h in history
        ]
        
        return JsonResponse({
            'success': True,
            'history': list(reversed(history_data)),  # 時系列順に並び替え
            'session_id': session_id,
            'total_messages': len(history_data)
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'limitは数値で指定してください'
        }, status=400)
        
    except Exception as e:
        print(f"History API error: {e}")
        
        return JsonResponse({
            'success': False,
            'error': '履歴の取得中にエラーが発生しました'
        }, status=500)

@api_view(['POST'])
@login_required
def mark_alert_read(request):
    """
    アラートを既読にするエンドポイント
    
    POST /api/mark-alert-read/
    {
        "alert_id": 123
    }
    """
    
    try:
        data = json.loads(request.body)
        alert_id = data.get('alert_id')
        
        if not alert_id:
            return JsonResponse({
                'success': False,
                'error': 'alert_idが必要です'
            }, status=400)
        
        # アラートの取得と更新
        try:
            alert = UserAlert.objects.get(id=alert_id, user=request.user)
            alert.is_read = True
            alert.read_at = timezone.now()
            alert.save()
            
            return JsonResponse({
                'success': True,
                'message': 'アラートを既読にしました'
            })
            
        except UserAlert.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '指定されたアラートが見つかりません'
            }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
        
    except Exception as e:
        print(f"Mark alert read API error: {e}")
        
        return JsonResponse({
            'success': False,
            'error': 'アラートの更新中にエラーが発生しました'
        }, status=500)

@api_view(['GET'])
def api_status(request):
    """
    API稼働状況確認エンドポイント
    
    GET /api/status/
    """
    
    return JsonResponse({
        'success': True,
        'status': 'operational',
        'timestamp': timezone.now().isoformat(),
        'version': '2.0.0',
        'features': {
            'enhanced_chat': True,
            'predictions': True,
            'calendar': True,
            'alerts': True,
            'history': True
        }
    })