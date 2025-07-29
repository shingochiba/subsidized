# diagnosis_chat.py - チャット機能の診断用スクリプトを作成してください

import os
import sys
import django
import requests
import json

# Django設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
django.setup()

from django.conf import settings
from advisor.models import ConversationHistory, SubsidyType

def test_dify_api():
    """Dify API接続テスト"""
    print("\n=== Dify API 接続テスト ===")
    
    try:
        api_url = getattr(settings, 'DIFY_API_URL', '')
        api_key = getattr(settings, 'DIFY_API_KEY', '')
        
        print(f"API URL: {api_url}")
        print(f"API Key: {'設定済み' if api_key else '未設定'}")
        
        if not api_url or not api_key:
            print("❌ Dify API設定が不完全です")
            return False
        
        # テストリクエスト
        test_data = {
            "inputs": {},
            "query": "IT導入補助金について簡単に教えて",
            "response_mode": "blocking",
            "user": "test_user"
        }
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        url = f"{api_url}/chat-messages"
        print(f"\nリクエスト URL: {url}")
        
        response = requests.post(url, headers=headers, json=test_data, timeout=10)
        
        print(f"レスポンス ステータス: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'answer' in result:
                print(f"✅ API接続成功")
                print(f"回答例: {result['answer'][:100]}...")
                return True
            else:
                print(f"❌ 回答フィールドが見つかりません: {result}")
                return False
        else:
            print(f"❌ API接続失敗: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Dify APIテストエラー: {e}")
        return False

def test_chat_endpoint():
    """チャットエンドポイントテスト"""
    print("\n=== チャットエンドポイント テスト ===")
    
    try:
        import requests
        
        # ローカルAPIエンドポイントをテスト
        test_data = {
            'message': 'IT導入補助金について教えて',
            'session_id': 'test_session'
        }
        
        # Django開発サーバーが動いている前提
        url = 'http://127.0.0.1:8000/advisor/api/enhanced-chat/'
        
        print(f"テスト URL: {url}")
        
        response = requests.post(url, json=test_data, timeout=10)
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ エンドポイント正常")
            if 'response' in result:
                print(f"回答: {result['response'][:100]}...")
            return True
        else:
            print(f"❌ エンドポイントエラー: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Django開発サーバーが起動していません")
        return False
    except Exception as e:
        print(f"❌ エンドポイントテストエラー: {e}")
        return False

def check_database():
    """データベース接続テスト"""
    print("\n=== データベース接続テスト ===")
    
    try:
        # モデルアクセステスト
        subsidy_count = SubsidyType.objects.count()
        history_count = ConversationHistory.objects.count()
        
        print(f"✅ データベース接続成功")
        print(f"補助金制度数: {subsidy_count}")
        print(f"会話履歴数: {history_count}")
        return True
        
    except Exception as e:
        print(f"❌ データベースエラー: {e}")
        return False

def main():
    """メイン診断"""
    print("🔍 チャット機能診断スタート")
    print("=" * 50)
    
    results = []
    
    # テスト実行
    results.append(("データベース", check_database()))
    results.append(("Dify API", test_dify_api()))
    results.append(("チャットエンドポイント", test_chat_endpoint()))
    
    # 結果表示
    print("\n" + "=" * 50)
    print("📊 診断結果")
    print("=" * 50)
    
    success_count = 0
    for name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n成功率: {success_count}/{len(results)}")
    
    # 推奨対処法
    print("\n🚀 推奨対処法:")
    if success_count == 0:
        print("1. Django開発サーバーが起動しているか確認")
        print("2. .env ファイルの設定を確認")
        print("3. python manage.py runserver で再起動")
    elif success_count < len(results):
        print("1. 失敗した項目の詳細を確認")
        print("2. 設定ファイルやAPIキーを確認")
        print("3. ネットワーク接続を確認")
    else:
        print("1. ブラウザのキャッシュをクリア")
        print("2. JavaScript コンソールでエラーを確認")

if __name__ == "__main__":
    main()