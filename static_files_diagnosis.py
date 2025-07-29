# static_files_diagnosis.py - 静的ファイル問題の診断と修正

import os
import sys
import django

# Django設定の初期化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
django.setup()

def check_static_settings():
    """静的ファイル設定の確認"""
    print("🔍 静的ファイル設定の確認")
    print("=" * 60)
    
    try:
        from django.conf import settings
        
        # STATIC_URL の確認
        print(f"✅ STATIC_URL: {getattr(settings, 'STATIC_URL', 'NOT SET')}")
        
        # STATIC_ROOT の確認
        static_root = getattr(settings, 'STATIC_ROOT', None)
        print(f"📁 STATIC_ROOT: {static_root}")
        
        # STATICFILES_DIRS の確認
        staticfiles_dirs = getattr(settings, 'STATICFILES_DIRS', [])
        print(f"📂 STATICFILES_DIRS: {staticfiles_dirs}")
        
        # DEBUG設定の確認
        debug = getattr(settings, 'DEBUG', False)
        print(f"🐛 DEBUG: {debug}")
        
        if debug:
            print("ℹ️  DEBUGモードでは django.contrib.staticfiles が静的ファイルを提供")
        else:
            print("⚠️  本番モードでは別途Webサーバー設定が必要")
            
        # INSTALLED_APPS の確認
        installed_apps = getattr(settings, 'INSTALLED_APPS', [])
        if 'django.contrib.staticfiles' in installed_apps:
            print("✅ django.contrib.staticfiles がINSTALLED_APPSに含まれています")
        else:
            print("❌ django.contrib.staticfiles がINSTALLED_APPSにありません")
            
    except Exception as e:
        print(f"❌ 設定確認エラー: {e}")

def check_static_files_structure():
    """静的ファイルディレクトリ構造の確認"""
    print("\n📁 静的ファイル構造の確認")
    print("=" * 60)
    
    # 各種静的ファイルディレクトリを確認
    directories_to_check = [
        'static/',
        'static/js/',
        'static/css/',
        'static/images/',
        'advisor/static/',
        'advisor/static/js/',
        'advisor/static/css/',
    ]
    
    for directory in directories_to_check:
        if os.path.exists(directory):
            files = os.listdir(directory)
            print(f"✅ {directory} - {len(files)}個のファイル")
            
            # jsファイルとcssファイルをリスト
            js_files = [f for f in files if f.endswith('.js')]
            css_files = [f for f in files if f.endswith('.css')]
            
            if js_files:
                print(f"   📝 JS: {', '.join(js_files)}")
            if css_files:
                print(f"   🎨 CSS: {', '.join(css_files)}")
                
        else:
            print(f"❌ {directory} - ディレクトリが存在しません")

def check_missing_files():
    """不足しているファイルの確認"""
    print("\n🔍 不足ファイルの確認")
    print("=" * 60)
    
    # よく参照される静的ファイル
    common_files = [
        'static/js/main.js',
        'static/js/enhanced_chat.js',
        'static/css/enhanced_features.css',
        'static/css/main.css',
        'advisor/static/js/main.js',
        'advisor/static/js/enhanced_chat.js',
        'advisor/static/css/enhanced_features.css',
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in common_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    return missing_files, existing_files

def create_minimal_static_files():
    """最小限の静的ファイルを作成"""
    print("\n🔧 最小限の静的ファイルを作成")
    print("=" * 60)
    
    # 必要なディレクトリを作成
    directories = [
        'static/js/',
        'static/css/',
        'static/images/',
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 作成: {directory}")
    
    # main.js を作成
    main_js_content = '''
// static/js/main.js - 基本的なJavaScript

console.log("メイン JavaScript ファイルが読み込まれました");

// 共通のユーティリティ関数
window.utils = {
    // CSRF トークンの取得
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    },
    
    // 簡単な通知表示
    showNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // 簡単なアラート表示（後で改善可能）
        if (type === 'error') {
            alert(`エラー: ${message}`);
        } else if (type === 'success') {
            console.log(`成功: ${message}`);
        }
    },
    
    // 読み込み状態の管理
    setLoading(element, isLoading) {
        if (element) {
            element.disabled = isLoading;
            if (isLoading) {
                element.textContent = '処理中...';
            }
        }
    }
};

// DOM読み込み完了後の初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM読み込み完了");
    
    // 基本的なフォーム処理
    const forms = document.querySelectorAll('form[data-ajax]');
    forms.forEach(form => {
        form.addEventListener('submit', handleAjaxForm);
    });
});

// Ajax フォーム処理
function handleAjaxForm(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const url = form.action || window.location.href;
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': window.utils.getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.utils.showNotification('送信完了', 'success');
        } else {
            window.utils.showNotification(data.error || '送信エラー', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        window.utils.showNotification('ネットワークエラー', 'error');
    });
}
'''
    
    with open('static/js/main.js', 'w', encoding='utf-8') as f:
        f.write(main_js_content)
    print("✅ static/js/main.js を作成しました")
    
    # main.css を作成
    main_css_content = '''
/* static/css/main.css - 基本スタイル */

/* 基本リセット */
* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    line-height: 1.6;
    color: #333;
    margin: 0;
    padding: 0;
}

/* 共通レイアウト */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* ボタン */
.btn {
    display: inline-block;
    padding: 10px 20px;
    background: #007bff;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    transition: background-color 0.3s;
}

.btn:hover {
    background: #0056b3;
}

.btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
}

/* フォーム */
.form-group {
    margin-bottom: 1rem;
}

.form-control {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.form-control:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

/* ユーティリティ */
.text-center { text-align: center; }
.mt-3 { margin-top: 1rem; }
.mb-3 { margin-bottom: 1rem; }
.p-3 { padding: 1rem; }

/* レスポンシブ */
@media (max-width: 768px) {
    .container {
        padding: 0 10px;
    }
    
    .btn {
        width: 100%;
        margin-bottom: 10px;
    }
}
'''
    
    with open('static/css/main.css', 'w', encoding='utf-8') as f:
        f.write(main_css_content)
    print("✅ static/css/main.css を作成しました")

def check_template_references():
    """テンプレート内の静的ファイル参照を確認"""
    print("\n🔍 テンプレート内の静的ファイル参照確認")
    print("=" * 60)
    
    template_files = [
        'templates/base.html',
        'templates/advisor/index.html',
        'templates/advisor/enhanced_chat.html',
        'templates/advisor/chat.html'
    ]
    
    for template_file in template_files:
        if os.path.exists(template_file):
            print(f"📄 {template_file} を確認中...")
            
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 静的ファイルの参照を検索
                if '{% load static %}' in content:
                    print("  ✅ {% load static %} が含まれています")
                else:
                    print("  ⚠️ {% load static %} がありません")
                
                # main.js の参照を検索
                if 'main.js' in content:
                    print("  📝 main.js の参照が見つかりました")
                
                # CSS の参照を検索
                if '.css' in content:
                    print("  🎨 CSS ファイルの参照が見つかりました")
        else:
            print(f"❌ {template_file} が見つかりません")

def main():
    check_static_settings()
    check_static_files_structure()
    missing_files, existing_files = check_missing_files()
    
    if missing_files:
        print(f"\n⚠️ {len(missing_files)}個の静的ファイルが不足しています")
        create_minimal_static_files()
    
    check_template_references()
    
    print("\n" + "=" * 60)
    print("🎯 次のアクション")
    print("=" * 60)
    
    if missing_files:
        print("1. 作成された静的ファイルを確認")
        print("2. python manage.py collectstatic を実行（本番環境の場合）")
        print("3. サーバーを再起動: python manage.py runserver")
        print("4. ブラウザでアクセステスト")
    else:
        print("1. すべての静的ファイルが存在します")
        print("2. 別の問題の可能性があります")
        print("3. Django settings の STATICFILES_DIRS を確認")

if __name__ == "__main__":
    main()