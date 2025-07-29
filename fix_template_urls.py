#!/usr/bin/env python3
# fix_template_urls.py - テンプレート内のURL参照を一括修正

import os
import re
import glob

def fix_all_template_urls():
    """全テンプレートファイルのURL参照を修正"""
    
    # 修正対象のパターン
    url_replacements = [
        # 既存の間違ったURL参照を修正
        (r"{% url 'advisor:chat' %}", "{% url 'advisor:chat_interface' %}"),
        (r"{% url 'advisor:trend_analysis' %}", "{% url 'advisor:statistics_dashboard' %}"),
        (r"{% url 'chat' %}", "{% url 'advisor:chat_interface' %}"),
        (r"{% url 'enhanced_chat' %}", "{% url 'advisor:enhanced_chat_interface' %}"),
        (r"{% url 'subsidies' %}", "{% url 'advisor:subsidy_list' %}"),
        (r"{% url 'statistics' %}", "{% url 'advisor:statistics_dashboard' %}"),
        (r"{% url 'predictions' %}", "{% url 'advisor:prediction_dashboard' %}"),
        
        # 名前空間なしの参照を修正
        (r"{% url 'index' %}", "{% url 'advisor:index' %}"),
        (r"{% url 'admin_dashboard' %}", "{% url 'advisor:admin_dashboard' %}"),
    ]
    
    # テンプレートファイルを検索
    template_patterns = [
        'templates/**/*.html',
        'advisor/templates/**/*.html',
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

def add_missing_url_name():
    """不足しているURL名をurls.pyに追加"""
    
    urls_file = 'advisor/urls.py'
    if not os.path.exists(urls_file):
        print(f"❌ URLファイルが見つかりません: {urls_file}")
        return False
    
    try:
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # chatエイリアスが不足している場合は追加
        if "name='chat'" not in content:
            # chat_interfaceパターンの後にエイリアスを追加
            chat_alias = "    path('chat-alias/', views.chat_interface, name='chat'),  # エイリアス\n"
            
            # chat_interfaceパターンを見つけて、その後に追加
            pattern = r"(path\('chat/', views\.chat_interface, name='chat_interface'\),)"
            replacement = r"\1\n" + chat_alias
            
            new_content = re.sub(pattern, replacement, content)
            
            if new_content != content:
                with open(urls_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ chatエイリアスを追加: {urls_file}")
                return True
        else:
            print("✅ 必要なURLパターンは既に存在します")
            return True
    
    except Exception as e:
        print(f"❌ URLファイル更新エラー: {e}")
        return False

def main():
    """メイン実行関数"""
    print("🔧 テンプレートURL一括修正スクリプト開始")
    print("=" * 60)
    
    # 1. テンプレートファイルの修正
    print("\n1. テンプレートファイルのURL参照を修正...")
    modified_files = fix_all_template_urls()
    
    if modified_files:
        print(f"\n✅ {len(modified_files)}個のファイルを修正しました:")
        for file in modified_files:
            print(f"   - {file}")
    else:
        print("\n✅ 修正が必要なファイルはありませんでした")
    
    # 2. URLパターンの追加
    print("\n2. 不足しているURLパターンを確認...")
    url_success = add_missing_url_name()
    
    # 結果まとめ
    print("\n" + "=" * 60)
    print("🎯 修正結果まとめ")
    print(f"✅ テンプレート修正: {len(modified_files)}ファイル")
    print(f"✅ URL追加: {'成功' if url_success else '失敗'}")
    
    print("\n🎉 修正が完了しました！")
    print("次のコマンドでサーバーを再起動してください:")
    print("python manage.py runserver 0.0.0.0:8000")

if __name__ == "__main__":
    main()