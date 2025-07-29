#!/usr/bin/env python3
# check_model_fields.py - モデルフィールドを確認してコードを修正

import os
import django

# Django設定の初期化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
django.setup()

def check_conversation_history_fields():
    """ConversationHistoryモデルのフィールドを確認"""
    print("🔍 ConversationHistoryモデルのフィールド確認")
    print("=" * 60)
    
    try:
        from advisor.models import ConversationHistory
        
        # モデルのフィールド一覧を取得
        fields = ConversationHistory._meta.get_fields()
        
        print("✅ ConversationHistoryモデルのフィールド:")
        for field in fields:
            field_name = field.name
            field_type = field.__class__.__name__
            print(f"   - {field_name}: {field_type}")
        
        # フィールド名を確認
        field_names = [field.name for field in fields]
        
        print(f"\n📋 利用可能なフィールド名: {field_names}")
        
        # 特定フィールドの確認
        message_field = None
        content_field = None
        
        if 'message' in field_names:
            message_field = 'message'
            print("✅ 'message' フィールドが存在します")
        
        if 'content' in field_names:
            content_field = 'content'
            print("✅ 'content' フィールドが存在します")
        
        if not message_field and not content_field:
            print("❌ 'message' も 'content' も見つかりません")
            print("📝 利用可能なテキストフィールドを探しています...")
            
            # テキスト系フィールドを探す
            text_fields = []
            for field in fields:
                if 'text' in field.name.lower() or 'content' in field.name.lower() or 'message' in field.name.lower():
                    text_fields.append(field.name)
            
            if text_fields:
                print(f"📝 テキスト系フィールド候補: {text_fields}")
            else:
                print("❌ テキスト系フィールドが見つかりません")
        
        # サンプルデータの確認
        print(f"\n📊 データ件数: {ConversationHistory.objects.count()}")
        
        if ConversationHistory.objects.exists():
            sample = ConversationHistory.objects.first()
            print("📝 サンプルデータ:")
            for field in fields:
                if not field.many_to_many and not field.one_to_many:
                    try:
                        value = getattr(sample, field.name)
                        print(f"   {field.name}: {str(value)[:100]}...")
                    except Exception as e:
                        print(f"   {field.name}: エラー ({e})")
        
        return field_names
        
    except ImportError as e:
        print(f"❌ モデルのインポートエラー: {e}")
        return []
    except Exception as e:
        print(f"❌ フィールド確認エラー: {e}")
        return []

def check_subsidy_type_fields():
    """SubsidyTypeモデルのフィールドを確認"""
    print("\n🔍 SubsidyTypeモデルのフィールド確認")
    print("=" * 60)
    
    try:
        from advisor.models import SubsidyType
        
        # モデルのフィールド一覧を取得
        fields = SubsidyType._meta.get_fields()
        
        print("✅ SubsidyTypeモデルのフィールド:")
        for field in fields:
            field_name = field.name
            field_type = field.__class__.__name__
            print(f"   - {field_name}: {field_type}")
        
        # フィールド名を確認
        field_names = [field.name for field in fields]
        
        print(f"\n📋 利用可能なフィールド名: {field_names}")
        
        # データ件数確認
        print(f"\n📊 データ件数: {SubsidyType.objects.count()}")
        
        if SubsidyType.objects.exists():
            sample = SubsidyType.objects.first()
            print("📝 サンプルデータ:")
            for field in fields:
                if not field.many_to_many and not field.one_to_many:
                    try:
                        value = getattr(sample, field.name)
                        print(f"   {field.name}: {str(value)[:100]}...")
                    except Exception as e:
                        print(f"   {field.name}: エラー ({e})")
        
        return field_names
        
    except ImportError as e:
        print(f"❌ モデルのインポートエラー: {e}")
        return []
    except Exception as e:
        print(f"❌ フィールド確認エラー: {e}")
        return []

def generate_fixed_code(conversation_fields, subsidy_fields):
    """修正されたコードを生成"""
    print("\n🔧 修正コード生成")
    print("=" * 60)
    
    # メッセージフィールドの特定
    message_field = None
    if 'content' in conversation_fields:
        message_field = 'content'
    elif 'message' in conversation_fields:
        message_field = 'message'
    elif 'text' in conversation_fields:
        message_field = 'text'
    else:
        print("❌ メッセージフィールドが特定できません")
        return
    
    print(f"✅ メッセージフィールド: '{message_field}'")
    
    # 修正コードのテンプレート
    fixes = {
        'values_list_fix': f"values_list('{message_field}', flat=True)",
        'create_fix': f"content={message_field},  # 修正: message → {message_field}",
        'access_fix': f"conv.{message_field}  # 修正: message → {message_field}",
    }
    
    print("\n📝 必要な修正:")
    for fix_name, fix_code in fixes.items():
        print(f"   {fix_name}: {fix_code}")
    
    return message_field

def main():
    """メイン実行関数"""
    print("🚀 モデルフィールド確認・修正スクリプト開始")
    print("=" * 60)
    
    # 1. ConversationHistoryモデルの確認
    conversation_fields = check_conversation_history_fields()
    
    # 2. SubsidyTypeモデルの確認
    subsidy_fields = check_subsidy_type_fields()
    
    # 3. 修正コードの生成
    if conversation_fields:
        message_field = generate_fixed_code(conversation_fields, subsidy_fields)
        
        if message_field:
            print(f"\n🎯 結論: '{message_field}' フィールドを使用してください")
            print("\n📋 修正手順:")
            print("1. advisor/views.py の全ての 'message' を確認")
            print(f"2. ConversationHistory関連は '{message_field}' に変更")
            print("3. サーバーを再起動してテスト")
    
    print("\n" + "=" * 60)
    print("🎉 フィールド確認完了")

if __name__ == "__main__":
    main()