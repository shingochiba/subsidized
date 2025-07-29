# debug_chat.py
# チャット機能のデバッグ用スクリプト

import os
import sys
import django

# Django設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
django.setup()

def test_database_connection():
    """データベース接続テスト"""
    print("=== データベース接続テスト ===")
    try:
        from advisor.models import SubsidyType
        count = SubsidyType.objects.count()
        print(f"✅ データベース接続成功: 補助金データ {count}件")
        
        if count > 0:
            first_subsidy = SubsidyType.objects.first()
            print(f"✅ 最初の補助金: {first_subsidy.name}")
            return True
        else:
            print("⚠️ 補助金データが存在しません")
            return False
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        return False

def test_ai_service():
    """AIサービステスト"""
    print("\n=== AIサービステスト ===")
    try:
        from advisor.services import AIAdvisorService
        service = AIAdvisorService()
        print("✅ AIAdvisorService初期化成功")
        
        # 簡単なテスト
        test_question = "IT導入補助金について教えて"
        result = service.analyze_question(test_question, {})
        print(f"✅ 質問分析成功: {result.get('answer', 'No answer')[:100]}...")
        return True
    except Exception as e:
        print(f"❌ AIサービスエラー: {e}")
        return False

def test_conversation_manager():
    """会話管理テスト"""
    print("\n=== 会話管理テスト ===")
    try:
        from advisor.services import ConversationManager
        session_id = "test_session_123"
        
        ConversationManager.save_conversation(
            session_id=session_id,
            user=None,
            message_type='user',
            content='テストメッセージ'
        )
        
        history = ConversationManager.get_conversation_history(session_id)
        print(f"✅ 会話管理成功: 履歴 {len(history)}件")
        return True
    except Exception as e:
        print(f"❌ 会話管理エラー: {e}")
        return False

def test_api_endpoint():
    """API エンドポイントテスト"""
    print("\n=== API エンドポイントテスト ===")
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # 補助金一覧API
        response = client.get('/api/subsidies/')
        if response.status_code == 200:
            print("✅ 補助金一覧API成功")
        else:
            print(f"❌ 補助金一覧API失敗: {response.status_code}")
            return False
            
        # チャットAPI（POSTテスト）
        response = client.post('/api/question/', {
            'question': 'IT導入補助金について教えて',
            'business_type': '製造業',
            'company_size': '中小企業'
        })
        
        if response.status_code == 200:
            print("✅ チャットAPI成功")
            return True
        else:
            print(f"❌ チャットAPI失敗: {response.status_code}")
            try:
                content = response.content.decode('utf-8')
                print(f"レスポンス内容: {content[:200]}...")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ API テストエラー: {e}")
        return False

def check_required_files():
    """必要ファイルの存在確認"""
    print("\n=== 必要ファイル確認 ===")
    
    required_files = [
        'advisor/services/__init__.py',
        'advisor/services/ai_advisor.py',
        'advisor/models.py',
        'advisor/views.py',
        'templates/advisor/chat.html'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} が見つかりません")
            all_exist = False
    
    return all_exist

def check_settings():
    """設定確認"""
    print("\n=== 設定確認 ===")
    try:
        from django.conf import settings
        
        print(f"DEBUG: {settings.DEBUG}")
        print(f"DATABASE: {settings.DATABASES['default']['ENGINE']}")
        
        if hasattr(settings, 'DIFY_API_URL'):
            print(f"DIFY_API_URL: {settings.DIFY_API_URL}")
        else:
            print("⚠️ DIFY_API_URL が設定されていません")
            
        return True
    except Exception as e:
        print(f"❌ 設定確認エラー: {e}")
        return False

def main():
    """メイン診断関数"""
    print("🔍 補助金アドバイザー チャット機能診断")
    print("=" * 50)
    
    results = []
    
    # 各テストを実行
    results.append(("データベース接続", test_database_connection()))
    results.append(("必要ファイル", check_required_files()))
    results.append(("設定", check_settings()))
    results.append(("AIサービス", test_ai_service()))
    results.append(("会話管理", test_conversation_manager()))
    results.append(("API エンドポイント", test_api_endpoint()))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 診断結果サマリー")
    print("=" * 50)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n総合結果: {success_count}/{len(results)} 成功")
    
    if success_count == len(results):
        print("\n🎉 すべてのテストが成功しました！")
        print("チャット機能は正常に動作するはずです。")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")
        print("失敗した項目を確認して修正してください。")
    
    # 推奨アクション
    print("\n🚀 次のアクション:")
    if success_count < len(results):
        print("1. 失敗したテストの詳細を確認")
        print("2. 必要なファイルやサービスを修正")
        print("3. python manage.py runserver でサーバーを再起動")
    else:
        print("1. ブラウザでチャット機能をテスト")
        print("2. サーバーログでエラーを確認")

if __name__ == "__main__":
    main()