# static_check.py - 静的ファイル確認用スクリプト

import os

def check_static_files():
    """静的ファイルの存在確認"""
    print("🔍 静的ファイル確認")
    print("=" * 50)
    
    # 重要な静的ファイル
    critical_files = [
        'static/js/enhanced_chat.js',
        'static/js/main.js',
        'static/css/enhanced_features.css',
        'advisor/static/js/enhanced_chat.js',
        'advisor/templates/advisor/chat.html',
    ]
    
    missing_files = []
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - 見つかりません")
            missing_files.append(file_path)
    
    return missing_files

def check_django_settings():
    """Django設定の確認"""
    print("\n🔍 Django設定確認")
    print("=" * 50)
    
    try:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
        
        import django
        django.setup()
        
        from django.conf import settings
        
        print(f"DEBUG: {settings.DEBUG}")
        print(f"STATIC_URL: {settings.STATIC_URL}")
        print(f"STATIC_ROOT: {getattr(settings, 'STATIC_ROOT', 'Not set')}")
        
        # STATICFILES_DIRS の確認
        if hasattr(settings, 'STATICFILES_DIRS'):
            print(f"STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
        else:
            print("STATICFILES_DIRS: Not set")
            
        return True
        
    except Exception as e:
        print(f"❌ Django設定エラー: {e}")
        return False

def main():
    missing_files = check_static_files()
    settings_ok = check_django_settings()
    
    print("\n" + "=" * 50)
    print("📊 結果サマリー")
    print("=" * 50)
    
    if missing_files:
        print(f"⚠️ 不足ファイル数: {len(missing_files)}")
        print("\n🔧 対処法:")
        print("1. python manage.py collectstatic を実行")
        print("2. 不足ファイルを手動で作成")
    else:
        print("✅ すべての静的ファイルが存在します")
    
    if not settings_ok:
        print("❌ Django設定に問題があります")
    
    print("\n🚀 次のステップ:")
    print("1. ブラウザでF12を押して開発者ツールを開く")
    print("2. Consoleタブでエラーメッセージを確認")
    print("3. Networkタブで失敗したリクエストを確認")

if __name__ == "__main__":
    main()