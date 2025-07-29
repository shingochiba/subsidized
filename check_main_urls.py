# check_main_urls.py - メインURLファイルの確認

import os
import sys
import django

# Django設定の初期化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
django.setup()

def check_main_urls():
    """メインのURLファイルを確認"""
    print("🔍 メインURL設定の確認")
    print("=" * 60)
    
    try:
        from django.conf import settings
        print(f"✅ ROOT_URLCONF: {settings.ROOT_URLCONF}")
        
        # メインのurlsファイルをインポート
        main_urls_module = __import__(settings.ROOT_URLCONF, fromlist=[''])
        
        print(f"📋 メインURLパターン数: {len(main_urls_module.urlpatterns)}")
        
        # 各URLパターンを確認
        advisor_found = False
        for i, pattern in enumerate(main_urls_module.urlpatterns):
            pattern_str = str(pattern.pattern)
            print(f"  {i+1}. {pattern_str}")
            
            if hasattr(pattern, 'url_patterns'):
                print(f"     → include() パターン")
                if 'advisor' in pattern_str:
                    advisor_found = True
                    print(f"     ✅ advisor関連のURLパターン発見")
            else:
                print(f"     → 直接パターン: {pattern.callback}")
        
        if not advisor_found:
            print("\n❌ advisor関連のURLパターンが見つかりません！")
            return False
        else:
            print("\n✅ advisor関連のURLパターンが存在します")
            return True
            
    except Exception as e:
        print(f"❌ メインURL確認エラー: {e}")
        return False

def check_url_resolution():
    """URL解決テスト"""
    print("\n🧪 URL解決テスト")
    print("=" * 60)
    
    from django.urls import reverse, NoReverseMatch
    
    test_urls = [
        ('advisor:index', '/advisor/'),
        ('advisor:enhanced_chat_interface', '/advisor/enhanced-chat/'),
        ('advisor:enhanced_chat_api', '/advisor/api/enhanced-chat/'),
    ]
    
    all_success = True
    
    for url_name, expected_path in test_urls:
        try:
            resolved_url = reverse(url_name)
            if resolved_url == expected_path:
                print(f"✅ {url_name} → {resolved_url}")
            else:
                print(f"⚠️ {url_name} → {resolved_url} (期待値: {expected_path})")
            
        except NoReverseMatch as e:
            print(f"❌ {url_name} → NoReverseMatch: {e}")
            all_success = False
        except Exception as e:
            print(f"❌ {url_name} → Error: {e}")
            all_success = False
    
    return all_success

def check_actual_request():
    """実際のHTTPリクエストテスト"""
    print("\n🌐 HTTPリクエストテスト")
    print("=" * 60)
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # enhanced-chat ページのGETテスト
        try:
            response = client.get('/advisor/enhanced-chat/')
            print(f"✅ GET /advisor/enhanced-chat/ → {response.status_code}")
            
            if response.status_code == 404:
                print("❌ enhanced-chat ページが404エラー")
                return False
                
        except Exception as e:
            print(f"❌ GET /advisor/enhanced-chat/ → Error: {e}")
            return False
        
        # enhanced-chat API のPOSTテスト
        try:
            import json
            response = client.post('/advisor/api/enhanced-chat/', 
                                 data=json.dumps({
                                     'message': 'テストメッセージ',
                                     'session_id': 'test_session'
                                 }),
                                 content_type='application/json')
            
            print(f"✅ POST /advisor/api/enhanced-chat/ → {response.status_code}")
            
            if response.status_code == 404:
                print("❌ enhanced-chat API が404エラー")
                return False
            elif response.status_code == 200:
                data = json.loads(response.content)
                print(f"📝 API レスポンス: success={data.get('success')}")
                
        except Exception as e:
            print(f"❌ POST /advisor/api/enhanced-chat/ → Error: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ HTTPテストエラー: {e}")
        return False

def suggest_fixes():
    """修正提案"""
    print("\n🔧 修正提案")
    print("=" * 60)
    
    # メインのURLファイルの場所を特定
    try:
        main_urls_path = 'subsidy_advisor_project/urls.py'
        
        if os.path.exists(main_urls_path):
            print(f"📁 メインURLファイル: {main_urls_path}")
            
            with open(main_urls_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("📋 現在の内容:")
            print(content)
            
            # advisor の include が正しいかチェック
            if "include('advisor.urls')" in content:
                if "path('advisor/', include('advisor.urls'))" in content:
                    print("✅ advisor のURLインクルードは正しく設定されています")
                elif "path('', include('advisor.urls'))" in content:
                    print("⚠️ advisor のパスが空文字になっています")
                    print("📝 修正案: path('advisor/', include('advisor.urls')) に変更")
                else:
                    print("⚠️ advisor のパス設定を確認してください")
            else:
                print("❌ advisor.urls のインクルードが見つかりません")
                print("📝 以下を追加してください:")
                print("   path('advisor/', include('advisor.urls')),")
        else:
            print(f"❌ メインURLファイルが見つかりません: {main_urls_path}")
            
    except Exception as e:
        print(f"❌ ファイル確認エラー: {e}")

def main():
    main_urls_ok = check_main_urls()
    url_resolution_ok = check_url_resolution()
    http_test_ok = check_actual_request()
    
    print("\n" + "=" * 60)
    print("📊 診断結果サマリー")
    print("=" * 60)
    print(f"メインURL設定: {'✅' if main_urls_ok else '❌'}")
    print(f"URL解決テスト: {'✅' if url_resolution_ok else '❌'}")
    print(f"HTTPテスト: {'✅' if http_test_ok else '❌'}")
    
    if not all([main_urls_ok, url_resolution_ok, http_test_ok]):
        suggest_fixes()
    else:
        print("\n🎉 すべてのテストが成功しました！")
        print("問題は別の箇所にある可能性があります。")
        print("ブラウザのキャッシュクリアを試してください。")

if __name__ == "__main__":
    main()