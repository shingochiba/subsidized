# fix_field_references.py
# target_business を target_business_type に修正するスクリプト

import os
import re

def fix_field_references():
    """AIサービスファイル内のフィールド参照を修正"""
    
    # 修正対象ファイル
    files_to_fix = [
        'advisor/services/ai_advisor.py',
        'advisor/services/smart_ai_advisor.py',
        'advisor/services/nlp_ai_advisor.py',
        'advisor/services/context_aware_ai_advisor.py',
        'advisor/views.py'
    ]
    
    # 修正パターン
    replacements = [
        (r'\.target_business\b', '.target_business_type'),
        (r'target_business=', 'target_business_type='),
        (r'"target_business"', '"target_business_type"'),
        (r"'target_business'", "'target_business_type'"),
        (r'subsidy\.target_business', 'subsidy.target_business_type'),
        (r'target_subsidy\.target_business', 'target_subsidy.target_business_type')
    ]
    
    print("🔧 フィールド名修正を開始します...")
    print("=" * 50)
    
    total_files_fixed = 0
    total_replacements = 0
    
    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            print(f"⚠️ ファイルが見つかりません: {file_path}")
            continue
        
        try:
            # ファイルを読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_replacements = 0
            
            # 各パターンで置換
            for pattern, replacement in replacements:
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    file_replacements += len(matches)
                    print(f"  📝 {file_path}: '{pattern}' を {len(matches)}箇所修正")
            
            # 変更があった場合のみファイルを保存
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                total_files_fixed += 1
                total_replacements += file_replacements
                print(f"✅ {file_path}: {file_replacements}箇所修正済み")
            else:
                print(f"✅ {file_path}: 修正不要")
                
        except Exception as e:
            print(f"❌ {file_path}: エラー - {e}")
    
    print("=" * 50)
    print(f"🎉 修正完了!")
    print(f"📊 修正ファイル数: {total_files_fixed}")
    print(f"📊 総修正箇所: {total_replacements}")
    
    if total_replacements > 0:
        print("\n🚀 次のステップ:")
        print("1. python manage.py runserver でサーバーを再起動")
        print("2. チャット機能をテスト")
        print("3. エラーが解消されたか確認")
    else:
        print("\n💡 他の原因でエラーが発生している可能性があります。")
        print("サーバーログを確認してください。")

if __name__ == "__main__":
    fix_field_references()