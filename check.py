#!/usr/bin/env python3
"""
Django プロジェクト構成チェックスクリプト（エンコーディング対応版）
補助金アドバイザープロジェクトの必要ファイルを確認します。
"""

import os
import sys
from pathlib import Path
import codecs

def setup_django():
    """Django設定をセットアップ"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
        import django
        django.setup()
        return True
    except Exception as e:
        print(f"  ⚠️  Django設定の読み込みに失敗: {e}")
        return False

def safe_read_file(filepath, max_size=1024):
    """安全にファイルを読み込む（エンコーディングエラー対応）"""
    try:
        # まずUTF-8で試す
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read(max_size)
    except UnicodeDecodeError:
        try:
            # UTF-8で失敗したらShift_JIS（CP932）で試す
            with open(filepath, 'r', encoding='cp932') as f:
                return f.read(max_size)
        except UnicodeDecodeError:
            try:
                # それでも失敗したらLatin-1で試す
                with open(filepath, 'r', encoding='latin-1') as f:
                    return f.read(max_size)
            except Exception:
                return None
    except Exception:
        return None

def check_project_structure():
    """プロジェクト構成をチェック"""
    
    print("🔍 補助金アドバイザープロジェクト構成チェック")
    print("=" * 50)
    
    # 必須ファイル・ディレクトリのリスト
    required_items = [
        # 基本ファイル
        ('ファイル', 'manage.py'),
        ('ファイル', '.env'),
        ('ファイル', 'requirements.txt'),
        
        # Django設定
        ('ディレクトリ', 'subsidy_advisor_project'),
        ('ファイル', 'subsidy_advisor_project/__init__.py'),
        ('ファイル', 'subsidy_advisor_project/settings.py'),
        ('ファイル', 'subsidy_advisor_project/urls.py'),
        ('ファイル', 'subsidy_advisor_project/wsgi.py'),
        
        # アプリケーション
        ('ディレクトリ', 'advisor'),
        ('ファイル', 'advisor/__init__.py'),
        ('ファイル', 'advisor/models.py'),
        ('ファイル', 'advisor/views.py'),
        ('ファイル', 'advisor/urls.py'),
        ('ファイル', 'advisor/admin.py'),
        ('ファイル', 'advisor/apps.py'),
        
        # マイグレーション
        ('ディレクトリ', 'advisor/migrations'),
        ('ファイル', 'advisor/migrations/__init__.py'),
        
        # 管理コマンド
        ('ディレクトリ', 'advisor/management'),
        ('ファイル', 'advisor/management/__init__.py'),
        ('ディレクトリ', 'advisor/management/commands'),
        ('ファイル', 'advisor/management/commands/__init__.py'),
        ('ファイル', 'advisor/management/commands/load_subsidies.py'),
        ('ファイル', 'advisor/management/commands/load_adoption_data.py'),
        
        # サービスレイヤー
        ('ディレクトリ', 'advisor/services'),
        ('ファイル', 'advisor/services/__init__.py'),
        ('ファイル', 'advisor/services/adoption_analysis.py'),
        ('ファイル', 'advisor/services/ai_advisor.py'),
        
        # テンプレート
        ('ディレクトリ', 'templates'),
        ('ファイル', 'templates/base.html'),
        ('ディレクトリ', 'templates/advisor'),
        ('ファイル', 'templates/advisor/chat.html'),
        ('ファイル', 'templates/advisor/adoption_analysis.html'),
        
        # 静的ファイル
        ('ディレクトリ', 'static'),
        ('ディレクトリ', 'static/css'),
        ('ディレクトリ', 'static/js'),
        ('ディレクトリ', 'static/images'),
    ]
    
    # 推奨項目
    recommended_items = [
        ('ファイル', '.gitignore'),
        ('ディレクトリ', 'media'),
        ('ディレクトリ', 'logs'),
        ('ディレクトリ', 'docs'),
        ('ファイル', 'static/css/custom.css'),
        ('ファイル', 'static/js/chat.js'),
        ('ファイル', 'static/js/adoption_analysis.js'),
    ]
    
    missing_required = []
    missing_recommended = []
    
    print("📋 必須項目チェック:")
    for item_type, path in required_items:
        if os.path.exists(path):
            print(f"  ✅ {item_type}: {path}")
        else:
            print(f"  ❌ {item_type}: {path}")
            missing_required.append((item_type, path))
    
    print(f"\n📋 推奨項目チェック:")
    for item_type, path in recommended_items:
        if os.path.exists(path):
            print(f"  ✅ {item_type}: {path}")
        else:
            print(f"  ⚠️  {item_type}: {path}")
            missing_recommended.append((item_type, path))
    
    # 結果サマリー
    print(f"\n📊 チェック結果:")
    print(f"  必須項目: {len(required_items) - len(missing_required)}/{len(required_items)} 完了")
    print(f"  推奨項目: {len(recommended_items) - len(missing_recommended)}/{len(recommended_items)} 完了")
    
    # 不足項目の修正方法を提案
    if missing_required or missing_recommended:
        print(f"\n🛠️ PowerShellで一括作成するコマンド:")
        print("# 不足項目を一括作成")
        
        for item_type, path in missing_required + missing_recommended:
            if item_type == 'ディレクトリ':
                print(f"New-Item -ItemType Directory -Path \"{path}\" -Force")
            else:
                print(f"New-Item -ItemType File -Path \"{path}\" -Force")
    
    # 特別なチェック
    print(f"\n🔍 特別チェック:")
    
    # 二重ディレクトリチェック
    if os.path.exists('advisor/advisor'):
        print(f"  ⚠️  不要なディレクトリが検出されました: advisor/advisor")
        print(f"     削除コマンド: Remove-Item -Path \"advisor\\advisor\" -Force -Recurse")
    else:
        print(f"  ✅ 二重ディレクトリなし")
    
    # Django設定をセットアップしてからimportテスト
    django_setup_success = setup_django()
    
    if django_setup_success:
        # import エラーチェック
        try:
            sys.path.append('.')
            from advisor.services import AdoptionAnalysisService
            print(f"  ✅ AdoptionAnalysisService import 成功")
        except ImportError as e:
            print(f"  ❌ AdoptionAnalysisService import 失敗: {e}")
        
        try:
            from advisor.services import AIAdvisorService
            print(f"  ✅ AIAdvisorService import 成功")
        except ImportError as e:
            print(f"  ❌ AIAdvisorService import 失敗: {e}")
    else:
        print(f"  ⚠️  Django設定が読み込めないため、import テストをスキップします")
    
    # ファイル内容のクイックチェック（エンコーディング対応）
    print(f"\n📝 ファイル内容チェック:")
    
    # requirements.txt の中身チェック
    if os.path.exists('requirements.txt'):
        content = safe_read_file('requirements.txt')
        if content and 'Django' in content:
            print(f"  ✅ requirements.txt に Django が含まれています")
        elif content:
            print(f"  ⚠️  requirements.txt に Django が含まれていません")
            print(f"     内容プレビュー: {content[:100]}...")
        else:
            print(f"  ⚠️  requirements.txt を読み込めませんでした")
    
    # .env ファイルの重要設定チェック
    if os.path.exists('.env'):
        content = safe_read_file('.env')
        if content and 'DIFY_API_KEY' in content:
            print(f"  ✅ .env に DIFY_API_KEY が設定されています")
        elif content:
            print(f"  ⚠️  .env に DIFY_API_KEY が設定されていません")
        else:
            print(f"  ⚠️  .env ファイルを読み込めませんでした")
    
    # models.py の新モデルチェック
    if os.path.exists('advisor/models.py'):
        content = safe_read_file('advisor/models.py', 2048)
        if content:
            new_models = ['AdoptionStatistics', 'AdoptionTips', 'UserApplicationHistory', 'ApplicationScoreCard']
            found_models = [model for model in new_models if model in content]
            if len(found_models) == len(new_models):
                print(f"  ✅ 新しいモデル（採択率分析機能）がすべて定義されています")
            else:
                missing_models = [model for model in new_models if model not in found_models]
                print(f"  ⚠️  一部のモデルが不足しています: {', '.join(missing_models)}")
    
    print(f"\n✨ チェック完了!")
    
    # 次のステップを提案
    if len(missing_required) == 0:
        print(f"\n🚀 次のステップ:")
        print(f"  1. python manage.py check")
        print(f"  2. python manage.py makemigrations")
        print(f"  3. python manage.py migrate")
        print(f"  4. python manage.py load_subsidies")
        print(f"  5. python manage.py load_adoption_data")
        print(f"  6. python manage.py runserver")
    
    return len(missing_required) == 0

def create_setup_batch():
    """Windows用の一括セットアップバッチファイルを作成"""
    batch_content = """@echo off
chcp 65001 >nul
echo 🚀 補助金アドバイザープロジェクト セットアップ

echo 📁 ディレクトリとファイルを作成中...

REM 必須項目
echo Django==5.2> requirements.txt
echo djangorestframework==3.14.0>> requirements.txt
echo python-dotenv==1.0.0>> requirements.txt
echo requests==2.31.0>> requirements.txt
echo python-dateutil==2.8.2>> requirements.txt

mkdir static\\images 2>nul

REM 推奨項目
echo # Python> .gitignore
echo *.pyc>> .gitignore
echo __pycache__/>> .gitignore
echo venv/>> .gitignore
echo .env>> .gitignore
echo db.sqlite3>> .gitignore
echo media/>> .gitignore
echo staticfiles/>> .gitignore

mkdir media 2>nul
mkdir logs 2>nul
mkdir docs 2>nul

type nul > static\\css\\custom.css
type nul > static\\js\\chat.js
type nul > static\\js\\adoption_analysis.js

echo ✅ セットアップ完了!
echo.
echo 🔍 Django設定をチェック中...
python manage.py check

if %errorlevel% equ 0 (
    echo ✅ Django設定チェック成功!
    echo.
    echo 📊 次のステップ:
    echo   python manage.py makemigrations
    echo   python manage.py migrate
    echo   python manage.py runserver
) else (
    echo ❌ Django設定にエラーがあります
)

pause
"""
    
    with open('setup_complete.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"\n🛠️ セットアップバッチファイルを作成しました: setup_complete.bat")
    print(f"   実行方法: setup_complete.bat")

if __name__ == "__main__":
    success = check_project_structure()
    
    if not success:
        create_setup_batch()
    
    sys.exit(0 if success else 1)