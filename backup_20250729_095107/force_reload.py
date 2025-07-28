# force_reload.py - サービス強制リロード用

import os
import sys
import importlib

# Django設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')

import django
django.setup()

print("🔄 サービスを強制リロード中...")

# モジュールキャッシュをクリア
modules_to_reload = [
    'advisor.services.context_aware_ai_advisor',
    'advisor.services',
]

for module_name in modules_to_reload:
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
        print(f"♻️ {module_name} をリロードしました")

# 新しいサービスをテスト
try:
    from advisor.services import AIAdvisorService
    print(f"✅ 新しいサービス読み込み成功: {AIAdvisorService.__name__}")
    
    # 採択率質問でテスト
    service = AIAdvisorService()
    result = service.analyze_question("IT導入補助金の採択率を教えて", {})
    print(f"🎯 使用モデル: {result['model_used']}")
    
    if 'adoption-rate' in result['model_used']:
        print("✅ 採択率専用回答機能が正常に動作しています！")
    else:
        print("⚠️ まだ汎用回答が使われています")
        
except Exception as e:
    print(f"❌ エラー: {e}")

print("\n🔧 問題が続く場合:")
print("1. Djangoサーバーを完全に停止・再起動")
print("2. ブラウザのキャッシュクリア")
print("3. context_aware_ai_advisor.py ファイルの再保存")