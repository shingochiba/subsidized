# advisor/management/commands/add_missing_subsidies.py
from django.core.management.base import BaseCommand
from advisor.models import SubsidyType

class Command(BaseCommand):
    help = '不足している補助金制度を追加実装します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際には追加せず、追加予定の補助金のみ表示'
        )

    def handle(self, *args, **options):
        # 既存の補助金名を取得
        existing_subsidies = set(SubsidyType.objects.values_list('name', flat=True))
        
        # 実装すべき補助金の完全なリスト
        target_subsidies = [
            {
                'name': '省力化投資補助金',
                'description': '中小企業等の省力化投資による生産性向上を支援する補助金です。人手不足の解消と生産性向上を目的とした設備投資・システム導入を対象とします。IoT、AI、ロボット技術を活用した省力化設備の導入費用を補助します。',
                'max_amount': 1000,  # 万円単位
                'target_business_type': '中小企業・小規模事業者',
                'requirements': '従業員数300人以下、省力化効果の定量的説明、3年間の事業継続、付加価値額年率平均3%以上向上',
                'typical_application_months': [3, 6, 9, 12],
                'average_preparation_weeks': 10,
                'historical_success_rate': 0.45,
                'application_difficulty': 4
            },
            {
                'name': 'ものづくり補助金',
                'description': '中小企業・小規模事業者等の革新的サービス開発・試作品開発・生産プロセスの改善を支援します。設備投資を通じた生産性向上と、革新的な製品・サービスの開発を促進します。デジタル技術を活用した取り組みに対して特別枠も設置されています。',
                'max_amount': 1250,  # 万円単位（デジタル枠の場合）
                'target_business_type': '中小企業・小規模事業者',
                'requirements': '革新的な設備投資、3年間で付加価値額年率平均3%以上向上、給与支給総額年率平均1.5%以上向上',
                'typical_application_months': [2, 6, 10],
                'average_preparation_weeks': 12,
                'historical_success_rate': 0.55,
                'application_difficulty': 4
            },
            {
                'name': 'IT導入補助金',
                'description': '中小企業・小規模事業者等のITツール導入による業務効率化・売上向上を支援する補助金です。会計ソフト、受発注システム、決済ソフト、ECサイト構築ツールなどの導入費用を補助します。デジタル化による生産性向上が目的です。',
                'max_amount': 450,  # 万円単位
                'target_business_type': '中小企業・小規模事業者',
                'requirements': 'gBizIDプライムの取得、SECURITY ACTIONの実施、労働生産性の向上計画',
                'typical_application_months': [1, 4, 7, 10],
                'average_preparation_weeks': 6,
                'historical_success_rate': 0.68,
                'application_difficulty': 2
            },
            {
                'name': '小規模事業者持続化補助金【一般型】',
                'description': '小規模事業者の販路開拓等の取組や業務効率化の取組を支援する補助金です。経営計画に基づく販路開拓、生産性向上のための設備投資等を支援します。商工会議所等の支援を受けて申請する制度です。',
                'max_amount': 50,  # 万円単位
                'target_business_type': '小規模事業者',
                'requirements': '商工会議所等の確認、販路開拓等の事業計画、小規模事業者の要件を満たす',
                'typical_application_months': [2, 6, 10],
                'average_preparation_weeks': 8,
                'historical_success_rate': 0.72,
                'application_difficulty': 2
            },
            {
                'name': '小規模事業者持続化補助金【創業型】',
                'description': '創業期の小規模事業者による販路開拓等の取組を支援する補助金です。創業に伴う販路開拓、認知度向上、ブランディング等の取組を対象とします。創業から5年以内の事業者が対象です。',
                'max_amount': 200,  # 万円単位
                'target_business_type': '創業5年以内の小規模事業者',
                'requirements': '創業5年以内、商工会議所等の確認、販路開拓等の事業計画',
                'typical_application_months': [3, 7, 11],
                'average_preparation_weeks': 10,
                'historical_success_rate': 0.65,
                'application_difficulty': 3
            },
            {
                'name': '事業承継・M&A補助金',
                'description': '事業承継やM&Aを契機とした経営革新等への挑戦を支援する補助金です。事業承継・M&A後の新商品・サービス開発、販路開拓、設備投資等を対象とします。後継者の確保と企業の持続的発展を促進します。',
                'max_amount': 600,  # 万円単位
                'target_business_type': '中小企業・小規模事業者',
                'requirements': '事業承継またはM&A実施、経営革新等の取組、5年以内の事業実施',
                'typical_application_months': [4, 8, 12],
                'average_preparation_weeks': 12,
                'historical_success_rate': 0.58,
                'application_difficulty': 4
            },
            {
                'name': '新事業進出補助金',
                'description': '新分野への事業進出や新商品・サービスの開発等を支援する補助金です。市場調査、商品開発、販路開拓、設備投資等の費用を補助します。地域経済の活性化と企業の成長促進を目的とします。',
                'max_amount': 500,  # 万円単位
                'target_business_type': '中小企業・小規模事業者',
                'requirements': '新分野進出計画、市場分析、事業継続性、雇用創出効果',
                'typical_application_months': [5, 9],
                'average_preparation_weeks': 10,
                'historical_success_rate': 0.48,
                'application_difficulty': 3
            },
            {
                'name': '成長加速化補助金',
                'description': '中小企業の成長を加速させる革新的な取組を支援する補助金です。デジタル化、グローバル展開、人材育成、技術開発等の成長戦略を対象とします。持続的な成長と競争力強化を促進します。',
                'max_amount': 800,  # 万円単位
                'target_business_type': '中小企業・小規模事業者',
                'requirements': '成長戦略の策定、KPI設定、3年間の成長計画、外部専門家の活用',
                'typical_application_months': [1, 7],
                'average_preparation_weeks': 14,
                'historical_success_rate': 0.42,
                'application_difficulty': 4
            },
            {
                'name': '省エネ診断・省エネ・非化石転換補助金',
                'description': '省エネルギー設備の導入や非化石燃料への転換を支援する補助金です。省エネ診断、高効率設備への更新、再生可能エネルギー設備の導入等を対象とします。カーボンニュートラルの実現に貢献します。',
                'max_amount': 1000,  # 万円単位
                'target_business_type': '中小企業・小規模事業者',
                'requirements': '省エネ診断の実施、CO2削減効果の算定、省エネ計画の策定',
                'typical_application_months': [4, 8],
                'average_preparation_weeks': 8,
                'historical_success_rate': 0.62,
                'application_difficulty': 3
            },
            {
                'name': '雇用調整助成金',
                'description': '経済情勢の変動等により事業活動の縮小を余儀なくされた事業主が、雇用の維持を図るため労働者の休業等を行う場合に助成する制度です。労働者の雇用維持と企業の事業継続を支援します。',
                'max_amount': 330,  # 万円単位（上限日額の年間概算）
                'target_business_type': '雇用保険適用事業主',
                'requirements': '雇用保険の適用事業主、売上等の減少、雇用維持の取組',
                'typical_application_months': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                'average_preparation_weeks': 4,
                'historical_success_rate': 0.85,
                'application_difficulty': 2
            },
            {
                'name': '業務改善助成金',
                'description': '中小企業・小規模事業者の生産性向上を支援し、事業場内最低賃金の引上げを図る助成金です。設備投資等により業務改善を行い、従業員の賃金引上げを実施する事業主を支援します。',
                'max_amount': 600,  # 万円単位
                'target_business_type': '中小企業・小規模事業者',
                'requirements': '事業場内最低賃金の引上げ、生産性向上のための設備投資、労働者数30人以下',
                'typical_application_months': [2, 6, 10],
                'average_preparation_weeks': 6,
                'historical_success_rate': 0.75,
                'application_difficulty': 2
            }
        ]

        # 不足している補助金を特定
        missing_subsidies = []
        for subsidy_data in target_subsidies:
            if subsidy_data['name'] not in existing_subsidies:
                missing_subsidies.append(subsidy_data)

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('📋 補助金実装状況レポート'))
        self.stdout.write('='*70)
        
        self.stdout.write(f'📊 既存の補助金数: {len(existing_subsidies)}件')
        self.stdout.write(f'📋 対象補助金数: {len(target_subsidies)}件')
        self.stdout.write(f'⚠️  未実装の補助金数: {len(missing_subsidies)}件\n')

        if not missing_subsidies:
            self.stdout.write(self.style.SUCCESS('✅ すべての対象補助金が実装済みです！'))
            return

        self.stdout.write(self.style.WARNING('🔍 未実装の補助金一覧:'))
        for subsidy in missing_subsidies:
            self.stdout.write(f'  • {subsidy["name"]}')
        
        if options['dry_run']:
            self.stdout.write('\n' + self.style.WARNING('--dry-run モードのため、実際の追加は行いません'))
            return

        # 不足している補助金を追加
        self.stdout.write('\n' + self.style.SUCCESS('🚀 補助金の追加を開始します...'))
        
        created_count = 0
        for subsidy_data in missing_subsidies:
            try:
                subsidy = SubsidyType.objects.create(**subsidy_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ 追加完了: {subsidy.name}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ 追加エラー: {subsidy_data["name"]} - {str(e)}')
                )

        self.stdout.write('\n' + '='*70)
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 補助金データの追加が完了しました！\n'
                f'  ✅ 新規追加: {created_count}件\n'
                f'  📊 総件数: {SubsidyType.objects.count()}件'
            )
        )
        
        # AIアドバイザーへの反映状況を確認
        self._check_ai_advisor_integration()
        
        self.stdout.write('='*70)

    def _check_ai_advisor_integration(self):
        """AIアドバイザーサービスへの統合状況をチェック"""
        self.stdout.write('\n' + self.style.SUCCESS('🤖 AIアドバイザーとの統合状況:'))
        
        try:
            from advisor.services.nlp_ai_advisor import NLPAIAdvisorService
            
            # サービスの初期化をテスト
            service = NLPAIAdvisorService()
            subsidy_count = len(service.subsidies)
            
            self.stdout.write(f'  ✅ AIサービス: 正常に初期化済み')
            self.stdout.write(f'  📊 認識可能な補助金数: {subsidy_count}件')
            
            # 補助金エイリアスの更新が必要かチェック
            unregistered_subsidies = []
            for subsidy in service.subsidies:
                if subsidy.name not in service.subsidy_aliases:
                    unregistered_subsidies.append(subsidy.name)
            
            if unregistered_subsidies:
                self.stdout.write(f'  ⚠️  エイリアス未登録: {len(unregistered_subsidies)}件')
                self.stdout.write('  💡 以下の補助金のエイリアス登録を推奨:')
                for name in unregistered_subsidies[:5]:  # 最大5件まで表示
                    self.stdout.write(f'     • {name}')
            else:
                self.stdout.write('  ✅ エイリアス: すべて登録済み')
                
        except ImportError:
            self.stdout.write('  ⚠️  NLPAIAdvisorService が見つかりません')
        except Exception as e:
            self.stdout.write(f'  ❌ エラー: {str(e)}')