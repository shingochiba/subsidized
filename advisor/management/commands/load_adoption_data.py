# advisor/management/commands/load_adoption_data.py

from django.core.management.base import BaseCommand
from advisor.models import SubsidyType, AdoptionStatistics, AdoptionTips
import random
from datetime import datetime

class Command(BaseCommand):
    help = '採択統計データとティップスを投入します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='既存データを削除してから投入'
        )
        parser.add_argument(
            '--years',
            type=int,
            default=3,
            help='生成する年数（デフォルト: 3年）'
        )

    def handle(self, *args, **options):
        if options['reset']:
            AdoptionStatistics.objects.all().delete()
            AdoptionTips.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('既存の採択統計・ティップスデータを削除しました')
            )

        # 統計データの生成
        self._create_adoption_statistics(options['years'])
        
        # ティップスデータの生成
        self._create_adoption_tips()

        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'採択データの投入が完了しました！\n'
                f'  📊 統計データ: {AdoptionStatistics.objects.count()}件\n'
                f'  💡 ティップス: {AdoptionTips.objects.count()}件'
            )
        )
        self.stdout.write('='*60)

    def _create_adoption_statistics(self, years):
        """採択統計データを生成"""
        subsidies = SubsidyType.objects.all()
        current_year = datetime.now().year
        created_count = 0

        for subsidy in subsidies:
            # 補助金の特性に応じたベース採択率を設定
            if 'IT導入' in subsidy.name:
                base_rate = 65.0
                variance = 10.0
            elif 'ものづくり' in subsidy.name:
                base_rate = 55.0
                variance = 8.0
            elif '持続化' in subsidy.name:
                base_rate = 70.0
                variance = 12.0
            elif '事業再構築' in subsidy.name:
                base_rate = 45.0
                variance = 15.0
            elif '創業' in subsidy.name:
                base_rate = 60.0
                variance = 20.0
            else:
                base_rate = 50.0
                variance = 15.0

            for year in range(current_year - years, current_year + 1):
                rounds = 2 if '持続化' in subsidy.name or 'IT導入' in subsidy.name else 1
                
                for round_num in range(1, rounds + 1):
                    # 既存データをスキップ
                    if AdoptionStatistics.objects.filter(
                        subsidy_type=subsidy, 
                        year=year, 
                        round_number=round_num
                    ).exists():
                        continue

                    # 年ごとのトレンドを追加
                    trend_adjustment = (year - (current_year - years)) * random.uniform(-2, 3)
                    adoption_rate = max(15.0, min(85.0, base_rate + trend_adjustment + random.uniform(-variance, variance)))

                    # 申請数の生成
                    if 'ものづくり' in subsidy.name:
                        total_apps = random.randint(8000, 15000)
                    elif 'IT導入' in subsidy.name:
                        total_apps = random.randint(15000, 30000)
                    elif '事業再構築' in subsidy.name:
                        total_apps = random.randint(10000, 20000)
                    elif '持続化' in subsidy.name:
                        total_apps = random.randint(6000, 12000)
                    else:
                        total_apps = random.randint(500, 3000)

                    total_adoptions = int(total_apps * adoption_rate / 100)

                    # 企業規模別データ
                    small_ratio = 0.7
                    small_apps = int(total_apps * small_ratio)
                    small_adoption_rate = adoption_rate + random.uniform(-3, 8)
                    small_adoptions = int(small_apps * small_adoption_rate / 100)

                    medium_apps = total_apps - small_apps
                    medium_adoptions = total_adoptions - small_adoptions
                    medium_adoption_rate = (medium_adoptions / medium_apps * 100) if medium_apps > 0 else 0

                    # 業種別統計
                    industry_stats = self._generate_industry_statistics(subsidy, adoption_rate, total_apps, total_adoptions)

                    # 統計データ作成
                    stat = AdoptionStatistics.objects.create(
                        subsidy_type=subsidy,
                        year=year,
                        round_number=round_num,
                        total_applications=total_apps,
                        total_adoptions=total_adoptions,
                        adoption_rate=round(adoption_rate, 1),
                        small_business_applications=small_apps,
                        small_business_adoptions=small_adoptions,
                        medium_business_applications=medium_apps,
                        medium_business_adoptions=medium_adoptions,
                        industry_statistics=industry_stats
                    )
                    created_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(f'✅ 統計作成: {subsidy.name} {year}年 第{round_num}回 (採択率: {adoption_rate:.1f}%, 小規模: {stat.small_business_adoption_rate:.1f}%)')
                    )

    def _generate_industry_statistics(self, subsidy, base_rate, total_apps, total_adoptions):
        """業種別統計を生成"""
        industries = {
            '製造業': 0.25,
            'IT・情報通信業': 0.20,
            'サービス業': 0.20,
            '小売業': 0.15,
            '建設業': 0.10,
            'その他': 0.10
        }

        # 補助金の特性に応じて業種別の補正
        if 'IT導入' in subsidy.name:
            industries['IT・情報通信業'] = 0.35
            industries['製造業'] = 0.20
            industries['サービス業'] = 0.25
        elif 'ものづくり' in subsidy.name:
            industries['製造業'] = 0.50
            industries['IT・情報通信業'] = 0.15

        industry_stats = {}
        remaining_apps = total_apps
        remaining_adoptions = total_adoptions

        for industry, ratio in industries.items():
            if industry == 'その他':  # 最後の業種は残り全部
                apps = remaining_apps
                adoptions = remaining_adoptions
            else:
                apps = int(total_apps * ratio)
                
                # 業種別の採択率補正
                if industry == 'IT・情報通信業' and 'IT導入' in subsidy.name:
                    industry_rate = base_rate + random.uniform(5, 15)
                elif industry == '製造業' and 'ものづくり' in subsidy.name:
                    industry_rate = base_rate + random.uniform(8, 20)
                elif industry == 'サービス業':
                    industry_rate = base_rate + random.uniform(-5, 5)
                else:
                    industry_rate = base_rate + random.uniform(-8, 8)
                
                industry_rate = max(15.0, min(85.0, industry_rate))
                adoptions = int(apps * industry_rate / 100)
                
                remaining_apps -= apps
                remaining_adoptions -= adoptions

            adoption_rate = (adoptions / apps * 100) if apps > 0 else 0

            industry_stats[industry] = {
                'applications': apps,
                'adoptions': adoptions,
                'adoption_rate': round(adoption_rate, 1)
            }

        return industry_stats

    def _create_adoption_tips(self):
        """採択ティップスを生成"""
        subsidies = SubsidyType.objects.all()

        # 共通ティップス
        common_tips = [
            {
                'category': '事前準備',
                'title': '申請要件の徹底確認',
                'content': '申請前に必ず最新の公募要領を熟読し、すべての要件を満たしているか確認しましょう。特に対象経費や期間については見落としがちです。',
                'importance': 5,
                'effective_timing': '申請検討時',
                'is_success_case': True
            },
            {
                'category': '事前準備',
                'title': 'gBizIDプライムの早期取得',
                'content': 'gBizIDプライムの取得には時間がかかります。申請予定が決まったら、まずgBizIDプライムを取得しましょう。',
                'importance': 4,
                'effective_timing': '申請検討時',
                'is_success_case': True
            },
            {
                'category': '申請書作成',
                'title': '具体的な数値目標の設定',
                'content': '売上向上や生産性向上について、具体的で根拠のある数値目標を設定してください。「少し」「多少」などの曖昧な表現は避けましょう。',
                'importance': 5,
                'effective_timing': '申請書作成時',
                'is_success_case': True
            },
            {
                'category': '申請書作成',
                'title': '現状の課題を明確化',
                'content': '現在の事業における具体的な課題を明確に記載し、補助事業によってどのように解決するかを論理的に説明しましょう。',
                'importance': 4,
                'effective_timing': '申請書作成時',
                'is_success_case': True
            },
            {
                'category': '申請書作成',
                'title': '審査項目に沿った記載',
                'content': '公募要領の審査項目を確認し、それぞれの項目について漏れなく記載してください。審査員が評価しやすいよう構成を工夫しましょう。',
                'importance': 5,
                'effective_timing': '申請書作成時',
                'is_success_case': True
            },
            {
                'category': '提出準備',
                'title': '必要書類の完全性確認',
                'content': '提出前に必要書類がすべて揃っているか、記載漏れがないかチェックリストを作成して確認しましょう。',
                'importance': 4,
                'effective_timing': '提出前',
                'is_success_case': True
            },
            {
                'category': '提出準備',
                'title': '期限に余裕を持った提出',
                'content': 'システム障害や書類不備に備え、締切の2-3日前には提出を完了しましょう。最終日の駆け込み提出は避けてください。',
                'importance': 3,
                'effective_timing': '提出前',
                'is_success_case': True
            }
        ]

        # 補助金別の特別ティップス
        special_tips = {
            'IT導入補助金': [
                {
                    'category': 'IT導入補助金特有',
                    'title': 'SECURITY ACTIONの実施',
                    'content': 'SECURITY ACTIONの★一つ星または★★二つ星の実施が必要です。申請前に必ず完了させてください。',
                    'importance': 5,
                    'effective_timing': '申請前',
                    'is_success_case': True
                },
                {
                    'category': 'IT導入補助金特有',
                    'title': 'ITツール選定の適切性',
                    'content': '導入予定のITツールが事前登録されているか確認し、自社の課題解決に最適なツールを選定しましょう。',
                    'importance': 4,
                    'effective_timing': '申請書作成時',
                    'is_success_case': True
                }
            ],
            'ものづくり補助金': [
                {
                    'category': 'ものづくり補助金特有',
                    'title': '革新性の明確な説明',
                    'content': '従来の手法との違いを明確に示し、なぜその設備・技術が革新的なのかを具体的に説明してください。',
                    'importance': 5,
                    'effective_timing': '申請書作成時',
                    'is_success_case': True
                },
                {
                    'category': 'ものづくり補助金特有',
                    'title': '付加価値額向上の根拠',
                    'content': '3年間で付加価値額年平均成長率3%以上の向上について、具体的な根拠と計算過程を示しましょう。',
                    'importance': 4,
                    'effective_timing': '申請書作成時',
                    'is_success_case': True
                }
            ],
            '小規模事業者持続化補助金': [
                {
                    'category': '持続化補助金特有',
                    'title': '経営計画書の質向上',
                    'content': '商工会・商工会議所と密に連携し、経営計画書の内容を充実させてください。第三者の視点での確認が重要です。',
                    'importance': 4,
                    'effective_timing': '申請書作成時',
                    'is_success_case': True
                },
                {
                    'category': '持続化補助金特有',
                    'title': '販路開拓の具体性',
                    'content': '「新規顧客獲得」ではなく、「どのような顧客に、どのような方法で、いつまでに」という具体的な販路開拓計画を記載しましょう。',
                    'importance': 5,
                    'effective_timing': '申請書作成時',
                    'is_success_case': True
                }
            ]
        }

        created_count = 0

        for subsidy in subsidies:
            # 共通ティップスを追加
            for tip_data in common_tips:
                tip, created = AdoptionTips.objects.get_or_create(
                    subsidy_type=subsidy,
                    category=tip_data['category'],
                    title=tip_data['title'],
                    defaults={
                        'content': tip_data['content'],
                        'importance': tip_data['importance'],
                        'effective_timing': tip_data['effective_timing'],
                        'is_success_case': tip_data['is_success_case']
                    }
                )
                if created:
                    created_count += 1

            # 補助金固有のティップスを追加
            for keyword, tips in special_tips.items():
                if keyword in subsidy.name:
                    for tip_data in tips:
                        tip, created = AdoptionTips.objects.get_or_create(
                            subsidy_type=subsidy,
                            category=tip_data['category'],
                            title=tip_data['title'],
                            defaults={
                                'content': tip_data['content'],
                                'importance': tip_data['importance'],
                                'effective_timing': tip_data['effective_timing'],
                                'is_success_case': tip_data['is_success_case']
                            }
                        )
                        if created:
                            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'✅ ティップス作成: {created_count}件')
        )