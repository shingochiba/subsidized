import os
import sys
import django

# Django設定の初期化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
django.setup()

def check_current_status():
    """現在の状況をチェック"""
    print("🔍 Enhanced Chat 診断開始")
    print("=" * 50)
    
    # 1. URLパターンの確認
    print("\n1. URL設定の確認")
    try:
        from django.urls import reverse
        from advisor.urls import urlpatterns
        
        print(f"✅ advisor.urls のインポート成功")
        print(f"📋 URL パターン数: {len(urlpatterns)}")
        
        # enhanced-chat関連のURLを探す
        enhanced_urls = [url for url in urlpatterns if 'enhanced' in str(url.pattern)]
        print(f"🔗 enhanced関連URL: {len(enhanced_urls)}件")
        
        for url in enhanced_urls:
            print(f"   - {url.pattern}")
            
    except Exception as e:
        print(f"❌ URL設定エラー: {e}")
    
    # 2. Views関数の確認
    print("\n2. View関数の確認")
    try:
        from advisor import views
        
        # enhanced_chat_api関数があるかチェック
        if hasattr(views, 'enhanced_chat_api'):
            print("✅ enhanced_chat_api 関数が存在")
        else:
            print("❌ enhanced_chat_api 関数が見つかりません")
            
        # analyze_question関数の確認
        if hasattr(views, 'analyze_question'):
            print("✅ analyze_question 関数が存在")
        else:
            print("❌ analyze_question 関数が見つかりません")
            
    except Exception as e:
        print(f"❌ Views確認エラー: {e}")
    
    # 3. データベース接続の確認
    print("\n3. データベース接続の確認")
    try:
        from advisor.models import SubsidyType
        subsidy_count = SubsidyType.objects.count()
        print(f"✅ データベース接続成功")
        print(f"📊 補助金データ: {subsidy_count}件")
        
    except Exception as e:
        print(f"❌ データベースエラー: {e}")
    
    # 4. AIサービスの確認
    print("\n4. AIサービスの確認")
    try:
        from advisor.services import AIAdvisorService
        advisor = AIAdvisorService()
        print("✅ AIAdvisorService 初期化成功")
        
        # テスト実行
        test_result = advisor.analyze_question("IT導入補助金について教えて")
        print(f"✅ AIサービステスト成功")
        print(f"📝 回答長: {len(test_result.get('answer', ''))}文字")
        
    except Exception as e:
        print(f"❌ AIサービスエラー: {e}")
    
    # 5. CSRFトークンの確認
    print("\n5. CSRF設定の確認")
    try:
        from django.conf import settings
        csrf_middleware = 'django.middleware.csrf.CsrfViewMiddleware'
        
        if csrf_middleware in settings.MIDDLEWARE:
            print("✅ CSRF middleware が設定済み")
        else:
            print("⚠️ CSRF middleware が見つかりません")
            
    except Exception as e:
        print(f"❌ CSRF確認エラー: {e}")

def create_minimal_working_api():
    """最小限動作するAPIを作成"""
    
    print("\n" + "=" * 50)
    print("🔧 最小限動作するAPIを作成中...")
    
    # 最小限のAPI関数
    api_code = ''