# debug_service.py - サービス状況確認用スクリプト

import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')

import django
django.setup()

# 現在使用されているサービスを確認
from advisor.services import AIAdvisorService
print(f"🔍 現在のAIAdvisorService: {AIAdvisorService}")
print(f"📁 モジュール: {AIAdvisorService.__module__}")
print(f"🏷️ クラス名: {AIAdvisorService.__name__}")

# 利用可能なメソッドを確認
methods = [method for method in dir(AIAdvisorService) if not method.startswith('_')]
print(f"📋 利用可能なメソッド: {methods}")

# テスト質問で確認
try:
    service = AIAdvisorService()
    result = service.analyze_question("IT導入補助金の採択率を教えて", {})
    print(f"✅ テスト成功: {result['model_used']}")
    print(f"📝 回答の一部: {result['answer'][:100]}...")
except Exception as e:
    print(f"❌ エラー: {e}")

print("\n" + "="*50)
print("🔧 修正が必要な場合は以下を確認してください：")
print("1. context_aware_ai_advisor.py ファイルが正しく作成されているか")
print("2. __init__.py が正しく更新されているか") 
print("3. Djangoサーバーが再起動されているか")