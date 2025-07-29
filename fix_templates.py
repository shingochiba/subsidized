#!/usr/bin/env python3
# fix_templates.py - テンプレートのURL参照を一括修正

import os
import re
import glob

def fix_template_files():
    """全HTMLテンプレートファイルのURL参照を修正"""
    
    # 修正対象のパターン
    url_replacements = [
        # 存在しないURL名を正しいものに修正
        (r"{% url 'advisor:chat_interface' %}", "{% url 'advisor:chat_interface' %}"),
        (r"{% url 'advisor:enhanced_chat_interface' %}", "{% url 'advisor:enhanced_chat_interface' %}"),
        (r"{% url 'advisor:subsidies' %}", "{% url 'advisor:subsidy_list' %}"),  # 重要な修正
        (r"{% url 'subsidies' %}", "{% url 'advisor:subsidy_list' %}"),          # 重要な修正
        (r"{% url 'advisor:analyze' %}", "{% url 'advisor:analyze_question' %}"),
        (r"{% url 'chat' %}", "{% url 'advisor:chat_interface' %}"),
        (r"{% url 'enhanced_chat' %}", "{% url 'advisor:enhanced_chat_interface' %}"),
        
        # JavaScript内のURL参照も修正
        (r"url: '/api/question/'", "url: '{% url \"advisor:analyze_question\" %}'"),
        (r"url: '/api/enhanced-chat/'", "url: '{% url \"advisor:enhanced_chat_api\" %}'"),
    ]
    
    # テンプレートファイルを検索
    template_patterns = [
        'templates/**/*.html',
        'advisor/templates/**/*.html',
        'templates/advisor/*.html'
    ]
    
    modified_files = []
    
    for pattern in template_patterns:
        template_files = glob.glob(pattern, recursive=True)
        
        for template_file in template_files:
            if os.path.isfile(template_file):
                try:
                    # ファイルを読み込み
                    with open(template_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # 各置換パターンを適用
                    for old_pattern, new_pattern in url_replacements:
                        content = re.sub(old_pattern, new_pattern, content)
                    
                    # 内容が変更された場合のみファイルを更新
                    if content != original_content:
                        with open(template_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        modified_files.append(template_file)
                        print(f"✅ 修正完了: {template_file}")
                    
                except Exception as e:
                    print(f"❌ ファイル処理エラー ({template_file}): {e}")
    
    return modified_files

def create_missing_url_patterns():
    """不足しているURLパターンを追加"""
    
    urls_file = 'advisor/urls.py'
    
    if not os.path.exists(urls_file):
        print(f"❌ URLファイルが見つかりません: {urls_file}")
        return False
    
    try:
        # 現在のURLファイルを読み込み
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 必要なURLパターンをチェック
        required_patterns = [
            ("path('subsidies/', views.subsidy_list, name='subsidy_list'),", 'subsidy_list'),
            ("path('api/subsidies/', views.subsidy_list, name='subsidy_list_api'),", 'subsidy_list_api'),
        ]
        
        urls_to_add = []
        
        for pattern, name in required_patterns:
            if f"name='{name}'" not in content:
                urls_to_add.append(pattern)
        
        if urls_to_add:
            # urlpatternsの終了部分を見つけて挿入
            if 'urlpatterns = [' in content:
                # 最後の ']' の前に挿入
                insertion_point = content.rfind(']')
                if insertion_point != -1:
                    # 新しいパターンを追加
                    new_patterns = '\n    # 自動追加されたパターン\n'
                    for pattern in urls_to_add:
                        new_patterns += f'    {pattern}\n'
                    
                    content = content[:insertion_point] + new_patterns + content[insertion_point:]
                    
                    # ファイルを更新
                    with open(urls_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"✅ URLパターンを追加: {urls_file}")
                    for pattern in urls_to_add:
                        print(f"   + {pattern}")
                    
                    return True
        else:
            print("✅ 必要なURLパターンは既に存在します")
            return True
    
    except Exception as e:
        print(f"❌ URLファイル更新エラー: {e}")
        return False

def create_missing_view_functions():
    """不足しているビュー関数を追加"""
    
    views_file = 'advisor/views.py'
    
    if not os.path.exists(views_file):
        print(f"❌ ビューファイルが見つかりません: {views_file}")
        return False
    
    try:
        with open(views_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # subsidy_list関数が存在するかチェック
        if 'def subsidy_list(' not in content:
            # subsidy_list関数を追加
            subsidy_list_function = '''
def subsidy_list(request):
    """
    補助金一覧API
    """
    try:
        subsidies = SubsidyType.objects.all()
        
        subsidy_data = []
        for subsidy in subsidies:
            subsidy_data.append({
                'id': subsidy.id,
                'name': subsidy.name,
                'description': subsidy.description,
                'max_amount': str(subsidy.max_amount),
                'target_business_type': subsidy.target_business_type,
                'requirements': subsidy.requirements,
            })
        
        return JsonResponse({
            'success': True,
            'subsidies': subsidy_data,
            'count': len(subsidy_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
'''
            
            # ファイルの末尾に関数を追加
            content += subsidy_list_function
            
            with open(views_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ subsidy_list関数を追加しました")
            return True
        else:
            print("✅ subsidy_list関数は既に存在します")
            return True
    
    except Exception as e:
        print(f"❌ ビューファイル更新エラー: {e}")
        return False

def main():
    """メイン実行関数"""
    print("🔧 テンプレート一括修正スクリプト開始")
    print("=" * 60)
    
    # 1. テンプレートファイルの修正
    print("\n1. テンプレートファイルのURL参照を修正...")
    modified_files = fix_template_files()
    
    if modified_files:
        print(f"\n✅ {len(modified_files)}個のファイルを修正しました:")
        for file in modified_files:
            print(f"   - {file}")
    else:
        print("\n✅ 修正が必要なファイルはありませんでした")
    
    # 2. URLパターンの追加
    print("\n2. 不足しているURLパターンを追加...")
    url_success = create_missing_url_patterns()
    
    # 3. ビュー関数の追加
    print("\n3. 不足しているビュー関数を追加...")
    view_success = create_missing_view_functions()
    
    # 結果まとめ
    print("\n" + "=" * 60)
    print("🎯 修正結果まとめ")
    print(f"✅ テンプレート修正: {len(modified_files)}ファイル")
    print(f"✅ URL追加: {'成功' if url_success else '失敗'}")
    print(f"✅ ビュー追加: {'成功' if view_success else '失敗'}")
    
    if url_success and view_success:
        print("\n🎉 全ての修正が完了しました！")
        print("次のコマンドでサーバーを再起動してください:")
        print("python manage.py runserver 0.0.0.0:8000")
    else:
        print("\n⚠️ 一部の修正に失敗しました。手動で確認してください。")

if __name__ == "__main__":
    main()