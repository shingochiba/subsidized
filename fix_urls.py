# fix_urls.py
# urls.pyの問題を修正

def fix_urls_py():
    """urls.pyを修正"""
    
    clean_urls = '''# advisor/urls.py - 修正版

from django.urls import path
from . import views

app_name = 'advisor'

urlpatterns = [
    # メインページ
    path('', views.index, name='index'),
    path('chat/', views.chat, name='chat'),
    
    # API エンドポイント
    path('api/analyze/', views.analyze_question, name='analyze_question'),
    path('api/chat/', views.enhanced_chat_api, name='enhanced_chat_api'),
    
    # 補助金情報
    path('subsidies/', views.subsidy_list, name='subsidy_list'),
    path('subsidies/<int:subsidy_id>/', views.subsidy_detail, name='subsidy_detail'),
    
    # 管理機能
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # 分析機能
    path('trends/', views.trend_analysis, name='trend_analysis'),
]'''
    
    try:
        # 現在のurls.pyをバックアップ
        with open('advisor/urls.py', 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        with open('advisor/urls_backup.py', 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        # 修正版を保存
        with open('advisor/urls.py', 'w', encoding='utf-8') as f:
            f.write(clean_urls)
        
        print("✅ advisor/urls.py を修正しました")
        return True
        
    except Exception as e:
        print(f"❌ urls.py修正エラー: {e}")
        return False

def main():
    """メイン実行"""
    print("🔧 urls.py を修正中...")
    
    if fix_urls_py():
        print("✅ 修正完了！")
        print("\n📋 次のステップ:")
        print("1. python manage.py runserver 0.0.0.0:8000 で再起動")
        print("2. エラーが解消されたか確認")
    else:
        print("❌ 修正に失敗しました")

if __name__ == "__main__":
    main()