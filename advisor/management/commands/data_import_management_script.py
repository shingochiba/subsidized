#!/usr/bin/env python3
"""
過去3年分の採択率データを投入し、分析環境を整備するスクリプト
"""

import os
import sys
import subprocess
import django
from pathlib import Path

def setup_django():
    """Django環境をセットアップ"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
        django.setup()
        return True
    except Exception as e:
        print(f"❌ Django設定エラー: {e}")
        return False

def run_management_command(command, description):
    """管理コマンドを実行"""
    print(f"\n🔄 {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ['python', 'manage.py'] + command,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"⚠️ 警告: {result.stderr}")
        print(f"✅ {description} 完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗")
        print(f"エラー詳細: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        return False

def check_data_status():
    """データの投入状況を確認"""
    print("\n📊 データベース状況確認")
    print("=" * 60)
    
    if not setup_django():
        return False
    
    from advisor.models import SubsidyType, AdoptionStatistics, AdoptionTips
    
    subsidies_count = SubsidyType.objects.count()
    statistics_count = AdoptionStatistics.objects.count()
    tips_count = AdoptionTips.objects.count()
    
    print(f"補助金データ: {subsidies_count}件")
    print(f"採択統計データ: {statistics_count}件")
    print(f"採択ティップス: {tips_count}件")
    
    # 年度別統計データの詳細
    if statistics_count > 0:
        print("\n📈 年度別統計データ:")
        for year in [2022, 2023, 2024]:
            year_stats = AdoptionStatistics.objects.filter(year=year)
            print(f"  {year}年度: {year_stats.count()}件")
            
            if year_stats.exists():
                for subsidy in SubsidyType.objects.all():
                    subsidy_year_stats = year_stats.filter(subsidy_type=subsidy)
                    if subsidy_year_stats.exists():
                        avg_rate = subsidy_year_stats.aggregate(
                            avg_rate=django.db.models.Avg('adoption_rate')
                        )['avg_rate']
                        print(f"    - {subsidy.name}: {subsidy_year_stats.count()}回, 平均採択率{avg_rate:.1f}%")
    
    return True

def create_analysis_summary():
    """分析サマリーを作成"""
    print("\n📋 分析サマリー作成")
    print("=" * 60)
    
    if not setup_django():
        return False
    
    from advisor.models import SubsidyType, AdoptionStatistics
    from django.db.models import Avg, Count
    
    print("過去3年間の採択率分析サマリー:")
    print("-" * 40)
    
    for subsidy in SubsidyType.objects.all():
        print(f"\n🏷️ {subsidy.name}")
        
        stats = AdoptionStatistics.objects.filter(
            subsidy_type=subsidy,
            year__gte=2022
        )
        
        if stats.exists():
            total_apps = sum(stat.total_applications for stat in stats)
            total_adoptions = sum(stat.total_adoptions for stat in stats)
            overall_rate = (total_adoptions / total_apps * 100) if total_apps > 0 else 0
            
            print(f"  📊 総申請数: {total_apps:,}件")
            print(f"  ✅ 総採択数: {total_adoptions:,}件")
            print(f"  📈 全体採択率: {overall_rate:.1f}%")
            
            # 年度別推移
            print("  📅 年度別推移:")
            for year in [2022, 2023, 2024]:
                year_stats = stats.filter(year=year)
                if year_stats.exists():
                    year_total_apps = sum(stat.total_applications for stat in year_stats)
                    year_total_adoptions = sum(stat.total_adoptions for stat in year_stats)
                    year_rate = (year_total_adoptions / year_total_apps * 100) if year_total_apps > 0 else 0
                    print(f"    {year}年度: {year_rate:.1f}% ({year_total_adoptions:,}/{year_total_apps:,})")
            
            # 企業規模別分析
            latest_stat = stats.order_by('-year', '-round_number').first()
            if latest_stat:
                print("  🏢 企業規模別採択率（最新データ）:")
                if latest_stat.small_business_adoption_rate:
                    print(f"    小規模事業者: {latest_stat.small_business_adoption_rate:.1f}%")
                if latest_stat.medium_business_adoption_rate:
                    print(f"    中小企業: {latest_stat.medium_business_adoption_rate:.1f}%")
        else:
            print("  ⚠️ 統計データなし")
    
    return True

def generate_analysis_recommendations():
    """分析に基づく推奨事項を生成"""
    print("\n💡 分析結果に基づく推奨事項")
    print("=" * 60)
    
    if not setup_django():
        return False
    
    from advisor.models import SubsidyType, AdoptionStatistics
    
    print("採択率向上のための重要ポイント:")
    print()
    
    # 採択率の高い補助金を特定
    high_success_subsidies = []
    low_success_subsidies = []
    
    for subsidy in SubsidyType.objects.all():
        recent_stats = AdoptionStatistics.objects.filter(
            subsidy_type=subsidy,
            year__gte=2023
        )
        
        if recent_stats.exists():
            avg_rate = sum(stat.adoption_rate for stat in recent_stats) / recent_stats.count()
            
            if avg_rate >= 60:
                high_success_subsidies.append((subsidy.name, avg_rate))
            elif avg_rate <= 40:
                low_success_subsidies.append((subsidy.name, avg_rate))
    
    if high_success_subsidies:
        print("🌟 採択率が高い補助金（60%以上）:")
        for name, rate in sorted(high_success_subsidies, key=lambda x: x[1], reverse=True):
            print(f"  • {name}: {rate:.1f}%")
        print("  → 申請を積極的に検討することをお勧めします")
    
    print()
    
    if low_success_subsidies:
        print("⚠️ 採択率が低い補助金（40%以下）:")
        for name, rate in sorted(low_success_subsidies, key=lambda x: x[1]):
            print(f"  • {name}: {rate:.1f}%")
        print("  → 十分な準備と戦略的な申請が必要です")
    
    print()
    print("📋 一般的な推奨事項:")
    print("  1. 小規模事業者は採択率が高い傾向にあります")
    print("  2. IT導入補助金は比較的採択されやすいです")
    print("  3. 事業再構築補助金は準備期間を十分確保してください")
    print("  4. 申請書類の品質が採択率に大きく影響します")
    print("  5. 認定支援機関との連携を活用してください")
    
    return True

def main():
    """メイン実行関数"""
    print("🚀 過去3年分の採択率分析データ投入システム")
    print("=" * 60)
    print("このスクリプトは以下の処理を実行します:")
    print("1. 補助金基本データの投入")
    print("2. 過去3年分の詳細な採択統計データの投入") 
    print("3. 実用的な採択ティップスの投入")
    print("4. データ状況の確認と分析")
    print("=" * 60)
    
    # 実行確認
    response = input("\n実行しますか？ (y/N): ")
    if response.lower() != 'y':
        print("処理を中止しました。")
        return
    
    success_count = 0
    total_steps = 6
    
    # 1. 補助金基本データの投入
    if run_management_command(['load_subsidies'], "補助金基本データの投入"):
        success_count += 1
    
    # 2. 詳細な採択統計データの投入
    if run_management_command(['load_comprehensive_adoption_data'], "詳細な採択統計データの投入"):
        success_count += 1
    
    # 3. 既存の採択データコマンドも実行（ティップス等）
    if run_management_command(['load_adoption_data'], "採択ティップス等の投入"):
        success_count += 1
    
    # 4. データ状況確認
    if check_data_status():
        success_count += 1
    
    # 5. 分析サマリー作成
    if create_analysis_summary():
        success_count += 1
    
    # 6. 推奨事項生成
    if generate_analysis_recommendations():
        success_count += 1
    
    # 結果表示
    print("\n" + "=" * 60)
    print(f"🎯 実行結果: {success_count}/{total_steps} 成功")
    
    if success_count == total_steps:
        print("✅ すべての処理が正常に完了しました！")
        print("\n次のステップ:")
        print("1. python manage.py runserver でサーバーを起動")
        print("2. http://localhost:8000/analysis/ で分析画面にアクセス")
        print("3. 補助金を選択して詳細な採択率推移を確認")
    else:
        print("⚠️ 一部の処理で問題が発生しました。")
        print("エラーを確認して再実行してください。")

if __name__ == "__main__":
    main()