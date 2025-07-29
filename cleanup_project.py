#!/usr/bin/env python3
"""
補助金アドバイザープロジェクト整理スクリプト
不要なファイル・ディレクトリを削除してプロジェクトを整理します。
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

def create_backup():
    """バックアップフォルダを作成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    
    print(f"📦 バックアップを作成中: {backup_dir}")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def safe_remove(path, backup_dir=None):
    """安全にファイル・ディレクトリを削除（バックアップ付き）"""
    if not os.path.exists(path):
        return False
    
    try:
        if backup_dir:
            # バックアップ先のパスを作成
            rel_path = os.path.relpath(path)
            backup_path = os.path.join(backup_dir, rel_path)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # バックアップを作成
            if os.path.isdir(path):
                shutil.copytree(path, backup_path)
            else:
                shutil.copy2(path, backup_path)
        
        # 元ファイル・ディレクトリを削除
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        
        print(f"  ✅ 削除: {path}")
        return True
    except Exception as e:
        print(f"  ❌ 削除失敗: {path} - {e}")
        return False

def cleanup_project(dry_run=False):
    """プロジェクトの不要ファイルを削除"""
    
    print("🧹 補助金アドバイザープロジェクト整理開始")
    print("=" * 50)
    
    if dry_run:
        print("🔍 DRY RUN モード: 実際の削除は行いません")
        print()
    
    # バックアップディレクトリを作成（dry_runでない場合のみ）
    backup_dir = None
    if not dry_run:
        backup_dir = create_backup()
    
    # 削除対象のファイル・ディレクトリ
    to_remove = [
        # デバッグ・テスト用ファイル
        "ch.py",
        "check.py", 
        "check_main_urls.py",
        "check_model_fields.py", 
        "check_views.py",
        "debug_chat.py",
        "debug_enhanced_chat.py", 
        "debug_intent.py",
        "debug_service.py",
        "diagnosis_chat.py",
        "static_check.py",
        "static_files_diagnosis.py",
        
        # 修正・フィックス用スクリプト
        "cleanup_chat_unification.py",
        "context_aware_fix.py", 
        "direct_fix.py",
        "enhanced_features.py",
        "final_implementation.py",
        "fix_all_templates.py",
        "fix_field_references.py", 
        "fix_other_subsidies.py",
        "fix_syntax_error.py",
        "fix_templates.py",
        "fix_template_urls.py", 
        "fix_urls.py",
        "force_reload.py",
        "setup_directories.py",
        "ultimate_fix.py",
        
        # バックアップファイル
        "advisor/urls_backup.py",
        "advisor/viewspybackup_broken.txt",
        "static/js/chat.js.backup",
        "templates/base_backup.html",
        "templates/base_backup.html.backup",
        "templates/advisor/admin_dashboard.html.backup",
        "templates/advisor/index.html.backup", 
        "templates/advisor/statistics.html.backup",
        "templates/advisor/trend_analysis.html.backup",
        "templates/advisor/user_alerts.html.backup",
        "templates/advisor/chat_backup.html",
        
        # 一時・作業用ディレクトリ
        "backup_chat_files",
        "logs",
        
        # 重複・未使用サービス
        "advisor/services/ai_advisor.py",
        "advisor/services/context_aware_ai_advisor.py", 
        "advisor/services/detailed_response_service.py",
        "advisor/services/enhanced_ai_advisor.py",
        "advisor/services/enhanced_ai_advisor_service.py",
        "advisor/services/improved_ai_advisor.py",
        "advisor/services/load_realistic_data.py",
        "advisor/services/nlp_ai_advisor.py",
        "advisor/services/smart_ai_advisor.py",
        "advisor/services/strategic_ai_advisor.py",
        "advisor/services/subsidy_prediction.py",
        
        # 未使用CSS
        "static/css/chat_enhancements.css",
        "static/css/toast_notifications.css",
        
        # 未使用管理コマンド
        "advisor/management/commands/data_import_management_script.py",
        "advisor/management/commands/test_aliases_quick.py",
    ]
    
    # 必須ファイル・ディレクトリ（削除しない）
    keep_files = [
        # 基本Django設定
        "manage.py",
        ".env", 
        "requirements.txt",
        ".gitignore",
        "README.md",
        "db.sqlite3",
        
        # Django設定ディレクトリ
        "subsidy_advisor_project/",
        
        # アプリケーションディレクトリ
        "advisor/__init__.py",
        "advisor/admin.py",
        "advisor/apps.py", 
        "advisor/models.py",
        "advisor/tests.py",
        "advisor/urls.py",
        "advisor/views.py",
        
        # 必要なサービス
        "advisor/services/__init__.py",
        "advisor/services/enhanced_adoption_analysis.py",
        "advisor/services/enhanced_chat_service.py", 
        "advisor/services/llm_enhanced_advisor.py",
        "advisor/services/subsidy_prediction_service.py",
        "advisor/services/adoption_analysis.py",
        
        # 必要な管理コマンド
        "advisor/management/commands/__init__.py",
        "advisor/management/commands/add_missing_subsidies.py",
        "advisor/management/commands/load_adoption_data.py",
        "advisor/management/commands/load_comprehensive_adoption_data.py",
        "advisor/management/commands/load_prediction_data.py", 
        "advisor/management/commands/load_strategic_tips.py",
        "advisor/management/commands/load_subsidies.py",
        "advisor/management/commands/update_subsidy_aliases.py",
        
        # マイグレーション
        "advisor/migrations/",
        
        # テンプレート
        "templates/base.html",
        "templates/advisor/enhanced_chat.html",
        "templates/advisor/index.html",
        "templates/advisor/statistics.html",
        "templates/advisor/trend_analysis.html", 
        "templates/advisor/adoption_analysis.html",
        "templates/advisor/prediction_calendar.html",
        "templates/advisor/prediction_dashboard.html",
        "templates/advisor/statistics_dashboard.html",
        "templates/advisor/subsidy_list.html",
        "templates/advisor/subsidy_prediction.html",
        "templates/advisor/admin_dashboard.html",
        "templates/advisor/session_list.html",
        "templates/advisor/user_alerts.html",
        "templates/advisor/error.html",
        "templates/advisor/debug_history.html",
        "templates/registration/",
        
        # 必要な静的ファイル
        "static/css/main.css",
        "static/css/enhanced_chat.css", 
        "static/css/enhanced_features.css",
        "static/css/custom.css",
        "static/js/main.js",
        "static/js/enhanced_chat.js",
        "static/js/adoption_analysis.js",
        "static/js/chat.js",
        "static/images/",
        
        # 生成された静的ファイル（Django collectstatic）
        "staticfiles/",
        
        # メディアファイル
        "media/",
        "docs/",
    ]
    
    removed_count = 0
    total_count = len(to_remove)
    
    print(f"📋 削除対象: {total_count} 個のファイル・ディレクトリ")
    print()
    
    for item in to_remove:
        if os.path.exists(item):
            print(f"🗑️  {item}")
            if not dry_run:
                if safe_remove(item, backup_dir):
                    removed_count += 1
            else:
                removed_count += 1
        else:
            print(f"⏭️  スキップ (存在しない): {item}")
    
    print()
    print("=" * 50)
    print(f"✨ 整理完了!")
    print(f"📊 削除済み: {removed_count}/{total_count}")
    
    if backup_dir:
        print(f"💾 バックアップ場所: {backup_dir}")
    
    if dry_run:
        print()
        print("ℹ️  実際に削除するには、dry_run=False で実行してください")
    
    # 残存ファイル構造を表示
    print()
    print("📁 整理後の主要ディレクトリ構造:")
    show_structure(".", max_depth=3)

def show_structure(path=".", max_depth=3, current_depth=0, prefix=""):
    """ディレクトリ構造を表示"""
    if current_depth > max_depth:
        return
    
    items = []
    try:
        for item in sorted(os.listdir(path)):
            if item.startswith('.') and item not in ['.env', '.gitignore']:
                continue
            if item in ['__pycache__', '*.pyc']:
                continue
            item_path = os.path.join(path, item)
            items.append((item, os.path.isdir(item_path)))
    except PermissionError:
        return
    
    for i, (item, is_dir) in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        icon = "📁" if is_dir else "📄"
        print(f"{prefix}{current_prefix}{icon} {item}")
        
        if is_dir and current_depth < max_depth:
            extension = "    " if is_last else "│   "
            show_structure(
                os.path.join(path, item), 
                max_depth, 
                current_depth + 1, 
                prefix + extension
            )

def main():
    """メイン関数"""
    print("補助金アドバイザープロジェクト整理ツール")
    print()
    
    # 引数でdry runモードを制御
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    
    if dry_run:
        cleanup_project(dry_run=True)
    else:
        response = input("⚠️  実際にファイルを削除しますか？ (y/N): ")
        if response.lower() in ['y', 'yes']:
            cleanup_project(dry_run=False)
        else:
            print("キャンセルされました")
            cleanup_project(dry_run=True)

if __name__ == "__main__":
    main()