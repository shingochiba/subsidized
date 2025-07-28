# setup_directories.py - 必要なディレクトリを作成するスクリプト

import os
from pathlib import Path

def create_directories():
    """必要なディレクトリ構造を作成"""
    
    base_dir = Path('.')
    
    directories = [
        'advisor/management',
        'advisor/management/commands',
        'static/css',
        'static/js', 
        'static/images',
        'media',
        'logs'
    ]
    
    created = []
    
    for directory in directories:
        path = base_dir / directory
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(directory)
            print(f"✅ 作成: {directory}")
        else:
            print(f"⚪ 存在: {directory}")
    
    # __init__.py ファイルの作成
    init_files = [
        'advisor/management/__init__.py',
        'advisor/management/commands/__init__.py'
    ]
    
    for init_file in init_files:
        path = base_dir / init_file
        if not path.exists():
            path.touch()
            created.append(init_file)
            print(f"✅ 作成: {init_file}")
        else:
            print(f"⚪ 存在: {init_file}")
    
    print(f"\n📁 ディレクトリ設定完了！")
    if created:
        print(f"新規作成: {len(created)}個")
    else:
        print("すべてのディレクトリが既に存在しています。")

if __name__ == '__main__':
    create_directories()