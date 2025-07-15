# advisor/management/commands/load_subsidies.py
# 現在のモデル構造に対応した修正版

from django.core.management.base import BaseCommand
from advisor.models import SubsidyType

class Command(BaseCommand):
    help = '補助金マスタデータを投入します（現在のモデル構造対応版）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='既存データを削除してから投入'
        )

    def handle(self, *args, **options):
        if options['reset']:
            SubsidyType.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('既存の補助金データを削除しました')
            )

        # 現在のモデル構造に対応した補助金データ
        subsidies_data = [
            {
                'name': 'IT導入補助金2025',
                'description': 'ITツール導入による業務効率化・売上向上を支援する補助金です。ECサイト構築、勤怠管理システム、会計ソフトなどの導入費用を補助します。gBizIDプライムの取得、SECURITY ACTIONの実施が必要です。',
                'max_amount': 450,  # 万円単位
                'target_business_type': '中小企業・小規模事業者',
                'requirements': 'gBizIDプライムの取得、SECURITY ACTIONの実施、労働生産性の向上',
                'typical_application_months': [1, 4, 7, 10],
                'average_preparation_weeks': 6,
                'historical_success_rate': 0.68,
                'application_difficulty': 2
            },
            {
                'name': 'ものづくり補助金',
                'description': '中小企業・小規模事業者等の革新的サービス開発・試作品開発・生産プロセスの改善を支援。設備投資を通じた生産性向上を図ります。',
                'max_amount': 1000,  # 万円単位
                'target_business_type': '中小企業・小規模事業者',
                'requirements': '革新的な設備投資、付加価値額年率平均3%以上の向上、給与支給総額年率平均1.5%以上の向上',
                'typical_application_months': [2, 6, 10],
                'average_preparation_weeks': 12,
                'historical_success_rate': 0.55,
                'application_difficulty': 4
            },
            {
                'name': '小規模事業者持続化補助金',
                'description': '小規模事業者の販路開拓等の取組や、地域の雇用や産業を支える事業の持続的発展を後押しする補助金です。',
                'max_amount': 200,  # 万円単位
                'target_business_type': '小規模事業者',
                'requirements': '商工会・商工会議所の支援を受けて経営計画書を策定、販路開拓等の取組を実施',
                'typical_application_months': [2, 5, 8, 11],
                'average_preparation_weeks': 8,
                'historical_success_rate': 0.72,
                'application_difficulty': 2
            },
            {
                'name': '事業再構築補助金',
                'description': 'ポストコロナ・ウィズコロナ時代の経済社会の変化に対応するため、中小企業等の思い切った事業再構築を支援する補助金です。',
                'max_amount': 8000,  # 万円単位
                'target_business_type': '中小企業・中堅企業',
                'requirements': '2020年4月以降いずれかの月の売上高が前年同月比で10%以上減少、事業再構築指針に沿った3〜5年の事業計画書の策定',
                'typical_application_months': [3, 7, 11],
                'average_preparation_weeks': 16,
                'historical_success_rate': 0.45,
                'application_difficulty': 5
            },
            {
                'name': '事業承継・引継ぎ補助金',
                'description': '事業承継・M&A時の専門家活用やその後の新しい取組等を支援する補助金です。',
                'max_amount': 800,  # 万円単位
                'target_business_type': '中小企業・小規模事業者',
                'requirements': '事業承継またはM&A等の実施、認定経営革新等支援機関の確認、事業計画の策定と実行',
                'typical_application_months': [4, 8, 12],
                'average_preparation_weeks': 10,
                'historical_success_rate': 0.60,
                'application_difficulty': 3
            },
            {
                'name': '創業助成金',
                'description': '東京都内で創業予定の個人または創業から5年未満の中小企業者等に対して、創業初期に必要な経費の一部を助成します。',
                'max_amount': 300,  # 万円単位
                'target_business_type': '創業予定者・創業5年未満の中小企業',
                'requirements': '東京都内での創業、事業計画書の策定、指定の支援機関による確認',
                'typical_application_months': [4, 10],
                'average_preparation_weeks': 8,
                'historical_success_rate': 0.35,
                'application_difficulty': 3
            }
        ]

        created_count = 0
        updated_count = 0

        for data in subsidies_data:
            try:
                subsidy, created = SubsidyType.objects.get_or_create(
                    name=data['name'],
                    defaults=data
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ 作成: {subsidy.name}')
                    )
                else:
                    # 既存データを更新
                    for key, value in data.items():
                        setattr(subsidy, key, value)
                    subsidy.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'🔄 更新: {subsidy.name}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ エラー: {data["name"]} - {str(e)}')
                )

        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'補助金データの投入が完了しました！\n'
                f'  ✅ 新規作成: {created_count}件\n'
                f'  🔄 更新: {updated_count}件\n'
                f'  📊 総件数: {SubsidyType.objects.count()}件'
            )
        )
        self.stdout.write('='*60)