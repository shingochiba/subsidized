from django.core.management.base import BaseCommand
from advisor.models import SubsidyType

class Command(BaseCommand):
    help = '補助金の初期データを投入します'

    def handle(self, *args, **options):
        subsidies_data = [
            {
                'name': 'IT導入補助金2025',
                'description': 'ITツール（ソフトウェア、サービス等）の導入による中小企業・小規模事業者等の生産性向上を支援する補助金です。',
                'target_business': '中小企業・小規模事業者（製造業、建設業、運輸業、卸売業、サービス業、小売業、その他業種）',
                'application_period': '2025年1月〜12月（年数回の公募予定）',
                'max_amount': 4500000,
                'subsidy_rate': '1/2以内',
                'requirements': 'gBizIDプライムアカウントの取得、SECURITY ACTIONの実施、交付決定後の効果報告の実施など'
            },
            {
                'name': '事業再構築補助金',
                'description': 'ポストコロナ時代の経済社会の変化に対応するため、中小企業等の思い切った事業再構築を支援する補助金です。',
                'target_business': '中小企業・中堅企業・個人事業主・企業組合等',
                'application_period': '2025年1月〜（随時公募）',
                'max_amount': 15000000,
                'subsidy_rate': '2/3以内（中小企業）、1/2以内（中堅企業）',
                'requirements': '2020年4月以降の連続する6か月間のうち任意の3か月の合計売上高がコロナ以前と比較して10%以上減少、事業再構築指針に沿った新分野展開・事業転換・業種転換等、認定経営革新等支援機関との事業計画策定など'
            },
            {
                'name': 'ものづくり補助金',
                'description': '中小企業・小規模事業者等が取り組む革新的サービス開発・試作品開発・生産プロセスの改善を行うための設備投資等を支援する補助金です。',
                'target_business': '中小企業・小規模事業者',
                'application_period': '2025年1月〜（年数回の公募予定）',
                'max_amount': 12500000,
                'subsidy_rate': '1/2以内（小規模事業者は2/3以内）',
                'requirements': '3〜5年の事業計画策定と実行、付加価値額年率平均3%以上の向上、給与支給総額年率平均1.5%以上の向上、事業場内最低賃金地域別最低賃金+30円以上など'
            },
            {
                'name': '小規模事業者持続化補助金',
                'description': '小規模事業者が経営計画を策定して取り組む販路開拓や生産性向上の取組を支援する補助金です。',
                'target_business': '小規模事業者（商業・サービス業：従業員5人以下、製造業等：従業員20人以下）',
                'application_period': '2025年1月〜（年数回の公募予定）',
                'max_amount': 2000000,
                'subsidy_rate': '2/3以内',
                'requirements': '商工会・商工会議所の支援を受けて経営計画書・補助事業計画書を策定、販路開拓等の取組実施、効果報告書の提出など'
            },
            {
                'name': '事業承継・引継ぎ補助金',
                'description': '事業承継、事業引継ぎ後の設備投資や販路開拓、既存事業の廃止等に係る費用を支援する補助金です。',
                'target_business': '中小企業・個人事業主',
                'application_period': '2025年1月〜（年数回の公募予定）',
                'max_amount': 8000000,
                'subsidy_rate': '1/2以内〜2/3以内（類型により異なる）',
                'requirements': '事業承継またはM&A等の実施、認定経営革新等支援機関の確認、事業計画の策定と実行など'
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
                    self.style.SUCCESS(f"✓ 作成: {subsidy.name}")
                )
            else:
                updated_count += 1
                # 既存データを更新
                for key, value in data.items():
                    setattr(subsidy, key, value)
                subsidy.save()
                self.stdout.write(
                    self.style.WARNING(f"▲ 更新: {subsidy.name}")
                )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f"補助金データの投入が完了しました\n"
                f"新規作成: {created_count}件\n"
                f"更新: {updated_count}件"
            )
        )