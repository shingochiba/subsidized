from django.http import JsonResponse
from django.utils import timezone
from functools import wraps
import time
import json

def rate_limit(requests_per_minute=60):
    """
    簡易レート制限デコレーター
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # 実際の実装では Redis などを使用してレート制限を実装
            # ここでは簡単な例として session を使用
            
            current_time = time.time()
            session_key = f"rate_limit_{func.__name__}"
            
            if session_key not in request.session:
                request.session[session_key] = []
            
            # 1分以内のリクエスト履歴をフィルタ
            recent_requests = [
                req_time for req_time in request.session[session_key]
                if current_time - req_time < 60
            ]
            
            if len(recent_requests) >= requests_per_minute:
                return JsonResponse({
                    'success': False,
                    'error': 'レート制限に達しました。1分後にお試しください。'
                }, status=429)
            
            # 現在のリクエストを追加
            recent_requests.append(current_time)
            request.session[session_key] = recent_requests
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator

def api_error_handler(func):
    """
    API共通エラーハンドラー
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except Exception as e:
            # ログ出力（本番環境では適切なログシステムを使用）
            print(f"API Error in {func.__name__}: {e}")
            
            return JsonResponse({
                'success': False,
                'error': 'サーバーエラーが発生しました',
                'timestamp': timezone.now().isoformat()
            }, status=500)
    
    return wrapper

def validate_json_request(required_fields=None):
    """
    JSON リクエストの検証デコレーター
    """
    if required_fields is None:
        required_fields = []
    
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.content_type != 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Content-Type は application/json である必要があります'
                }, status=400)
            
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': '無効なJSON形式です'
                }, status=400)
            
            # 必須フィールドの確認
            missing_fields = [
                field for field in required_fields 
                if field not in data or not data[field]
            ]
            
            if missing_fields:
                return JsonResponse({
                    'success': False,
                    'error': f'必須フィールドが不足しています: {", ".join(missing_fields)}'
                }, status=400)
            
            # データをリクエストに追加
            request.json = data
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator