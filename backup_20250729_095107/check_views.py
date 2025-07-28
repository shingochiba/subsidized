# check_views.py - views.py の関数確認スクリプト

import os
import sys
import django

# Django設定の初期化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
django.setup()

def check_views_functions():
    """views.py の関数一覧を確認"""
    print("🔍 advisor/views.py の関数確認")
    print("=" * 60)
    
    try:
        from advisor import views
        
        # views モジュールの全ての関数を取得
        all_functions = [name for name in dir(views) if callable(getattr(views, name)) and not name.startswith('_')]
        
        print(f"📊 views.py内の関数数: {len(all_functions)}")
        print("\n📋 関数一覧:")
        
        required_functions = [
            'enhanced_chat_api',
            'analyze_question', 
            'enhanced_chat_interface',
            'index'
        ]
        
        for func_name in all_functions:
            status = "✅" if func_name in required_functions else "📝"
            print(f"  {status} {func_name}")
        
        print("\n🎯 必須関数チェック:")
        missing_functions = []
        
        for func_name in required_functions:
            if hasattr(views, func_name):
                print(f"  ✅ {func_name} - 存在")
            else:
                print(f"  ❌ {func_name} - 見つかりません")
                missing_functions.append(func_name)
        
        if missing_functions:
            print(f"\n⚠️ 不足している関数: {missing_functions}")
            print("\n🔧 解決方法:")
            for func in missing_functions:
                if func == 'enhanced_chat_api':
                    print("  1. enhanced_chat_api 関数を views.py に追加")
                    print("     (緊急修正版のコードを使用)")
        else:
            print("\n🎉 すべての必須関数が存在します！")
            
        return missing_functions
        
    except ImportError as e:
        print(f"❌ views.py インポートエラー: {e}")
        return ['ALL']
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return ['UNKNOWN']

def test_function_call():
    """関数の実行テスト"""
    print("\n🧪 関数実行テスト")
    print("=" * 60)
    
    try:
        from advisor import views
        
        # enhanced_chat_api のテスト
        if hasattr(views, 'enhanced_chat_api'):
            print("✅ enhanced_chat_api 関数が呼び出し可能")
            
            # Django リクエストオブジェクトのモック
            from django.test import RequestFactory
            factory = RequestFactory()
            
            # POSTリクエストのテスト
            request = factory.post('/api/enhanced-chat/', 
                                 data='{"message": "テスト"}',
                                 content_type='application/json')
            
            try:
                response = views.enhanced_chat_api(request)
                print(f"✅ enhanced_chat_api レスポンス: {response.status_code}")
                
                if hasattr(response, 'content'):
                    import json
                    content = json.loads(response.content)
                    print(f"📝 レスポンス内容: {content.get('success', 'N/A')}")
                    
            except Exception as e:
                print(f"❌ enhanced_chat_api 実行エラー: {e}")
        else:
            print("❌ enhanced_chat_api 関数が見つかりません")
            
    except Exception as e:
        print(f"❌ 関数テストエラー: {e}")

def check_imports():
    """必要なインポートの確認"""
    print("\n📦 インポート確認")
    print("=" * 60)
    
    required_imports = [
        'JsonResponse',
        'csrf_exempt', 
        'timezone',
        'json',
        'uuid'
    ]
    
    try:
        import advisor.views as views_module
        import inspect
        
        # views.py のソースコードを取得
        source = inspect.getsource(views_module)
        
        for import_name in required_imports:
            if import_name in source:
                print(f"✅ {import_name} - インポート済み")
            else:
                print(f"❌ {import_name} - インポート不足")
                
    except Exception as e:
        print(f"❌ インポート確認エラー: {e}")

def main():
    missing_functions = check_views_functions()
    
    if not missing_functions:
        test_function_call()
    
    check_imports()
    
    print("\n" + "=" * 60)
    print("🎯 次のアクション")
    print("=" * 60)
    
    if 'enhanced_chat_api' in missing_functions:
        print("1. 以下のコードを advisor/views.py の最後に追加:")
        print("""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import uuid

@csrf_exempt
def enhanced_chat_api(request):
    \"\"\"Enhanced Chat API - 緊急修正版\"\"\"
    
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
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'メッセージが入力されていません'
            }, status=400)
        
        # 簡単なキーワード応答
        if 'it導入' in message.lower():
            response_text = "IT導入補助金は、中小企業のITツール導入を支援する制度です。補助上限は450万円で、会計ソフトやECサイト構築などが対象となります。"
        else:
            response_text = "ご質問ありがとうございます。補助金について詳しくご案内いたします。"
        
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
        return JsonResponse({
            'success': False,
            'error': f'エラーが発生しました: {str(e)}'
        }, status=500)
""")
        print("\n2. ファイルを保存")
        print("3. python manage.py runserver で再起動")
    else:
        print("1. すべての関数が存在するので、別の問題の可能性があります")
        print("2. サーバーログを確認してください")
        print("3. ブラウザの開発者ツールでネットワークエラーを確認")

if __name__ == "__main__":
    main()