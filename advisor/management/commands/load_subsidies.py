# advisor/management/commands/load_subsidies.py

from django.core.management.base import BaseCommand
from advisor.models import SubsidyType
from datetime import date

class Command(BaseCommand):
    help = '補助金マスタデータを投入します'

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

        # 補助金データの定義
        subsidies_data = [
            {
                'name': 'IT導入補助金2024',
                'description': 'ITツール導入による業務効率化・売上向上を支援する補助金です。ECサイト構築、勤怠管理システム、会計ソフトなどの導入費用を補助します。gBizIDプライムの取得、SECURITY ACTIONの実施、みらデジ経営チェックの実施が必要です。管理組織：一般社団法人 サービスデザイン推進協議会',
                'target_business': '中小企業・小規模事業者',
                'application_period': '2024年4月1日〜2024年12月20日（複数回に分けて実施）',
                'max_amount': 4500000,
                'subsidy_rate': '1/2以内',
                'requirements': 'gBizIDプライムの取得、SECURITY ACTIONの実施、みらデジ経営チェックの実施'
            },
            {
                'name': 'ものづくり補助金（16次公募）',
                'description': '中小企業・小規模事業者等の革新的サービス開発・試作品開発・生産プロセスの改善を支援。設備投資を通じた生産性向上を図ります。管理組織：全国中小企業団体中央会',
                'target_business': '中小企業・小規模事業者',
                'application_period': '2024年7月26日〜2024年10月3日',
                'max_amount': 10000000,
                'subsidy_rate': '2/3以内',
                'requirements': 'gBizIDプライムの取得、経営計画書の作成、3〜5年の事業計画'
            },
            {
                'name': '小規模事業者持続化補助金（第15回）',
                'description': '小規模事業者の販路開拓や生産性向上の取組を支援。チラシ作成、ホームページ制作、展示会出展などの費用を補助します。管理組織：日本商工会議所',
                'target_business': '小規模事業者',
                'application_period': '2024年6月6日〜2024年8月26日',
                'max_amount': 2000000,
                'subsidy_rate': '2/3以内',
                'requirements': '商工会議所・商工会の事業支援計画書の発行、補助事業の適切な遂行'
            },
            {
                'name': '事業再構築補助金（第12回公募）',
                'description': 'ポストコロナ・ウィズコロナ時代の経済社会の変化に対応するため、中小企業等の思い切った事業再構築を支援。新分野展開、業態転換、業種転換などを対象。管理組織：中小企業庁',
                'target_business': '中小企業・中堅企業・個人事業主',
                'application_period': '2024年9月2日〜2024年10月15日',
                'max_amount': 15000000,
                'subsidy_rate': '2/3以内',
                'requirements': '売上減少要件（2020年4月以降で任意の3か月間の売上高が前年・前々年同期比で10%以上減少）、事業再構築要件'
            },
            {
                'name': '事業承継・引継ぎ補助金（第8回公募）',
                'description': '事業承継・M&Aを契機とした経営革新や事業転換への挑戦、M&A時の士業専門家活用を支援します。管理組織：中小企業庁',
                'target_business': '中小企業・小規模事業者・個人事業主',
                'application_period': '2024年5月20日〜2024年7月10日',
                'max_amount': 8000000,
                'subsidy_rate': '2/3以内',
                'requirements': '事業承継・M&Aが対象期間内に実行されること、認定経営革新等支援機関による確認'
            },
            {
                'name': '創業助成金（東京都）',
                'description': '東京都内での創業予定者・創業間もない中小企業者に対し、賃借料、広告費、器具備品購入費等、創業初期に必要な経費の一部を助成。管理組織：東京都中小企業振興公社',
                'target_business': '都内での創業予定者・創業5年未満の中小企業者',
                'application_period': '2024年4月26日〜2024年5月10日',
                'max_amount': 3000000,
                'subsidy_rate': '2/3以内',
                'requirements': '東京都内での創業、事業の継続性・発展性があること、地域経済の活性化に貢献すること'
            },
            {
                'name': '省エネルギー投資促進・需給構造転換支援事業費補助金',
                'description': '省エネルギー性能の高い設備・機器等の導入を支援し、エネルギー消費効率の改善を促進します。管理組織：一般社団法人 環境共創イニシアチブ',
                'target_business': '民間企業・地方公共団体等',
                'application_period': '2024年5月7日〜2024年6月21日',
                'max_amount': 100000000,
                'subsidy_rate': '1/3以内',
                'requirements': '省エネルギー率1%以上の改善、投資回収年数が適切であること'
            },
            {
                'name': '働き方改革推進支援助成金',
                'description': '中小企業・小規模事業者の働き方改革の推進を支援。労働時間短縮、年次有給休暇の促進、テレワーク導入などの取組を支援します。管理組織：厚生労働省',
                'target_business': '中小企業・小規模事業者',
                'application_period': '通年（予算に達し次第終了）',
                'max_amount': 1000000,
                'subsidy_rate': '3/4以内',
                'requirements': '36協定の締結・届出、労働時間等設定改善委員会等の設置'
            },
            {
                'name': '両立支援等助成金（育児休業等支援コース）',
                'description': '育児休業の円滑な取得・職場復帰を支援する制度を整備し、実際に利用された場合に助成します。管理組織：厚生労働省',
                'target_business': '全企業',
                'application_period': '通年',
                'max_amount': 720000,
                'subsidy_rate': '定額',
                'requirements': '育児休業取得・職場復帰支援の実施、育児休業等に関する情報提供・研修の実施'
            },
            {
                'name': 'DX投資促進税制対象設備導入促進補助金',
                'description': 'DX（デジタルトランスフォーメーション）投資促進税制の対象となる設備導入を支援し、企業のデジタル化を促進します。管理組織：経済産業省',
                'target_business': '中小企業・中堅企業',
                'application_period': '2024年6月1日〜2024年11月30日',
                'max_amount': 5000000,
                'subsidy_rate': '1/2以内',
                'requirements': 'DX投資促進税制の認定、デジタル技術を活用した業務プロセスの改善'
            }
        ]

        created_count = 0
        updated_count = 0

        for data in subsidies_data:
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