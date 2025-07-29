# cleanup_chat_unification.py - チャット統一化用クリーンアップ

import os
import shutil
from pathlib import Path

def unify_chat_system():
    """チャット機能を強化版に統一"""
    
    print("🔄 チャット機能統一化開始")
    print("=" * 50)
    
    # 1. 旧版テンプレートのバックアップ
    print("\n1. 旧版ファイルのバックアップ")
    
    backup_dir = Path('backup_chat_files')
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        'templates/advisor/chat.html',
        'advisor/static/js/chat.js',
        'static/js/chat.js'
    ]
    
    for file_path in files_to_backup:
        file_path = Path(file_path)
        if file_path.exists():
            backup_path = backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            print(f"✅ バックアップ: {file_path} → {backup_path}")
        else:
            print(f"⚠️ ファイルが見つかりません: {file_path}")
    
    # 2. 旧版テンプレートの削除
    print("\n2. 旧版ファイルの削除")
    
    files_to_remove = [
        'templates/advisor/chat.html',  # 通常版テンプレート
        'advisor/templates/advisor/chat.html',  # アプリ内テンプレート（もしあれば）
    ]
    
    for file_path in files_to_remove:
        file_path = Path(file_path)
        if file_path.exists():
            file_path.unlink()
            print(f"🗑️ 削除: {file_path}")
        else:
            print(f"➖ ファイルが存在しません: {file_path}")
    
    # 3. JavaScript統一
    print("\n3. JavaScript統一")
    
    enhanced_js_path = Path('static/js/enhanced_chat.js')
    unified_js_path = Path('static/js/chat.js')
    
    if enhanced_js_path.exists():
        # enhanced_chat.js を chat.js としてもコピー（後方互換性）
        shutil.copy2(enhanced_js_path, unified_js_path)
        print(f"✅ 統一: {enhanced_js_path} → {unified_js_path}")
    
    # 4. 設定確認
    print("\n4. 設定確認")
    
    print("📋 確認事項:")
    print("   1. advisor/urls.py の更新")
    print("   2. advisor/views.py の関数統一")
    print("   3. templates/advisor/index.html のボタン更新")
    print("   4. サーバー再起動")
    
    print("\n✅ 統一化準備完了！")
    
    # 5. 次のステップ
    print("\n🚀 次のステップ:")
    print("1. 上記のファイル更新を手動で実行")
    print("2. python manage.py runserver で再起動")
    print("3. ブラウザでテスト")
    
    return True

def create_unified_template_redirect():
    """統一用のリダイレクトテンプレート作成"""
    
    # chat.html を enhanced_chat.html へのリダイレクトとして作成
    redirect_template = '''{% extends 'base.html' %}

{% block content %}
<div class="container text-center mt-5">
    <div class="alert alert-info">
        <h4><i class="fas fa-arrow-right"></i> チャット機能が統一されました</h4>
        <p>強化版チャット機能をご利用ください。自動的にリダイレクトします...</p>
    </div>
</div>

<script>
// 3秒後に強化版チャットにリダイレクト
setTimeout(function() {
    window.location.href = "{% url 'advisor:enhanced_chat_interface' %}";
}, 3000);
</script>
{% endblock %}'''
    
    chat_template_path = Path('templates/advisor/chat.html')
    chat_template_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(chat_template_path, 'w', encoding='utf-8') as f:
        f.write(redirect_template)
    
    print(f"✅ リダイレクトテンプレート作成: {chat_template_path}")

if __name__ == "__main__":
    unify_chat_system()
    create_unified_template_redirect()