# debug_intent.py - 意図検出のデバッグ

import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')

import django
django.setup()

from advisor.services import AIAdvisorService

# テスト質問リスト
test_questions = [
    "IT導入補助金の採択率を教えて",
    "最近の採択率はどうですか？",
    "通る確率は何パーセントですか？",
    "採択率教えて",
    "何%通る？",
    "受かる可能性は？",
    "成功確率は？",
    "直近の採択率",
    "ものづくり補助金は何パーセント通る？"
]

print("🧪 意図検出テストを開始します...\n")

service = AIAdvisorService()

for i, question in enumerate(test_questions, 1):
    print(f"【テスト {i}】: {question}")
    print("-" * 50)
    
    try:
        result = service.analyze_question(question, {})
        print(f"✅ 使用モデル: {result['model_used']}")
        
        if 'adoption-rate' in result['model_used']:
            print("🎯 ✅ 採択率専用回答成功！")
        else:
            print("⚠️ 汎用回答が使用されました")
            
        print(f"📝 回答の開始: {result['answer'][:100]}...")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    print("\n" + "="*60 + "\n")

print("🔧 もし採択率専用回答が動作しない場合:")
print("1. context_aware_ai_advisor.py を再保存")
print("2. Djangoサーバーを再起動")
print("3. 以下のコマンドでモジュールを強制リロード:")
print("   python -c \"import importlib; import sys; importlib.reload(sys.modules['advisor.services'])\"")