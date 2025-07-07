# advisor/management/commands/load_adoption_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from advisor.models import SubsidyType, AdoptionStatistics, AdoptionTips, UserApplicationHistory
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = '採択率分析用のサンプルデータを投入します'

    def handle(self, *args, **options):
        self.stdout.write('採択率分析用サンプルデータの投入を開始します...\n')
        
        # 1. 採択統計データの投入
        self.load_adoption_statistics()
        
        # 2. 採択ティップスの投入
        self.load_adoption_tips()
        
        # 3. サンプル申請履歴の投入
        self.load_sample_application_history()
        
        self.stdout.write(
            self.style.SUCCESS('\n採択率分析用サンプルデータの投入が完了しました！')
        )

    def load_adoption_statistics(self):
        """採択統計データを投入"""
        self.stdout.write('📊 採択統計データを投入中...')
        
        subsidies = SubsidyType.objects.all()
        years = [2022, 2023, 2024]
        
        created_count = 0
        
        for subsidy in subsidies:
            for year in years:
                # 年に1-3回の公募があると仮定
                rounds = random.randint(1, 3)
                
                for round_num in range(1, rounds + 1):
                    # リアルなデータを模擬
                    if 'IT導入' in subsidy.name:
                        total_apps = random.randint(8000, 12000)
                        adoption_rate = random.uniform(50, 70)
                    elif '事業再構築' in subsidy.name:
                        total_apps = random.randint(15000, 25000)
                        adoption_rate = random.uniform(25, 45)
                    elif 'ものづくり' in subsidy.name:
                        total_apps = random.randint(6000, 10000)
                        adoption_rate = random.uniform(40, 60)
                    elif '持続化' in subsidy.name:
                        total_apps = random.randint(20000, 35000)
                        adoption_rate = random.uniform(55, 75)
                    else:
                        total_apps = random.randint(3000, 8000)
                        adoption_rate = random.uniform(30, 50)
                    
                    total_adoptions = int(total_apps * adoption_rate / 100)
                    
                    # 企業規模別データ
                    small_apps = int(total_apps * 0.4)
                    small_adoptions = int(small_apps * (adoption_rate + random.uniform(-5, 10)) / 100)
                    medium_apps = int(total_apps * 0.6)
                    medium_adoptions = total_adoptions - small_adoptions
                    
                    # 業種別統計（サンプル）
                    industry_stats = {
                        '製造業': {'applications': int(total_apps * 0.3), 'adoptions': int(total_adoptions * 0.35), 'adoption_rate': random.uniform(35, 65)},
                        'IT・情報通信業': {'applications': int(total_apps * 0.2), 'adoptions': int(total_adoptions * 0.25), 'adoption_rate': random.uniform(45, 75)},
                        'サービス業': {'applications': int(total_apps * 0.25), 'adoptions': int(total_adoptions * 0.2), 'adoption_rate': random.uniform(25, 55)},
                        '建設業': {'applications': int(total_apps * 0.15), 'adoptions': int(total_adoptions * 0.12), 'adoption_rate': random.uniform(20, 50)},
                        '小売業': {'applications': int(total_apps * 0.1), 'adoptions': int(total_adoptions * 0.08), 'adoption_rate': random.uniform(30, 60)}
                    }
                    
                    stat, created = AdoptionStatistics.objects.get_or_create(
                        subsidy_type=subsidy,
                        year=year,
                        round_number=round_num,
                        defaults={
                            'total_applications': total_apps,
                            'total_adoptions': total_adoptions,
                            'adoption_rate': adoption_rate,
                            'small_business_applications': small_apps,
                            'small_business_adoptions': small_adoptions,
                            'medium_business_applications': medium_apps,
                            'medium_business_adoptions': medium_adoptions,
                            'industry_statistics': industry_stats
                        }
                    )
                    
                    if created:
                        created_count += 1
        
        self.stdout.write(f'  ✓ 採択統計データ {created_count}件を作成')

    def load_adoption_tips(self):
        """採択ティップスを投入"""
        self.stdout.write('💡 採択ティップスを投入中...')
        
        tips_data = [
            # IT導入補助金
            {
                'subsidy_name': 'IT導入補助金2025',
                'tips': [
                    {'category': 'preparation', 'title': 'ITツールの事前選定', 'content': 'IT導入支援事業者と連携し、自社に最適なITツールを事前に選定しておくことが重要です。', 'importance': 4},
                    {'category': 'application', 'title': '生産性向上の具体的数値化', 'content': 'IT導入により期待される生産性向上効果を具体的な数値で示し、ROIを明確にすることで採択率が向上します。', 'importance': 4},
                    {'category': 'documents', 'title': 'SECURITY ACTION実施証明', 'content': '情報セキュリティ対策の実施を証明するSECURITY ACTIONの宣言は必須要件です。', 'importance': 4},
                    {'category': 'strategy', 'title': 'IT導入支援事業者との連携', 'content': '認定されたIT導入支援事業者との密な連携により、申請書の質が大幅に向上します。', 'importance': 3},
                    {'category': 'common_mistakes', 'title': 'gBizIDの取得遅れ', 'content': 'gBizIDプライムアカウントの取得には時間がかかるため、早めの準備が必要です。', 'importance': 3},
                    {'category': 'success_factors', 'title': '業務プロセス改善の明確化', 'content': 'IT導入により具体的にどの業務プロセスがどのように改善されるかを明確に示すことが重要です。', 'importance': 3}
                ]
            },
            # 事業再構築補助金
            {
                'subsidy_name': '事業再構築補助金',
                'tips': [
                    {'category': 'preparation', 'title': '認定経営革新等支援機関との連携', 'content': '事業計画策定において認定経営革新等支援機関との連携は必須です。早期に相談先を確保しましょう。', 'importance': 4},
                    {'category': 'application', 'title': '売上減少要件の適切な証明', 'content': 'コロナ禍による売上減少を適切な書類で証明し、要件を満たしていることを明確に示してください。', 'importance': 4},
                    {'category': 'strategy', 'title': '事業再構築指針への適合', 'content': '新分野展開、事業転換、業種転換、業態転換、事業再編のいずれかに該当することを明確に示してください。', 'importance': 4},
                    {'category': 'documents', 'title': '詳細な事業計画書作成', 'content': '5年間の事業計画を詳細に作成し、実現可能性と収益性を具体的に示すことが重要です。', 'importance': 3},
                    {'category': 'common_mistakes', 'title': '既存事業との差別化不足', 'content': '既存事業との違いを明確にし、なぜ新しい事業が必要なのかを説得力を持って説明してください。', 'importance': 3},
                    {'category': 'success_factors', 'title': '地域経済への貢献', 'content': '地域経済や雇用創出への貢献を具体的に示すことで評価が高まります。', 'importance': 2}
                ]
            },
            # ものづくり補助金
            {
                'subsidy_name': 'ものづくり補助金',
                'tips': [
                    {'category': 'preparation', 'title': '革新的な設備投資計画', 'content': '従来の設備とは異なる革新的な設備投資により、生産性向上を図る計画を策定してください。', 'importance': 4},
                    {'category': 'application', 'title': '付加価値額向上の具体的計画', 'content': '3～5年で付加価値額を年率平均3%以上向上させる具体的な計画を示してください。', 'importance': 4},
                    {'category': 'strategy', 'title': '技術的優位性の明確化', 'content': '導入する技術や設備の技術的優位性と競合他社との差別化を明確に示してください。', 'importance': 3},
                    {'category': 'documents', 'title': '詳細な見積書の取得', 'content': '設備投資に関する詳細で適正な見積書を複数社から取得し、比較検討結果を示してください。', 'importance': 3},
                    {'category': 'common_mistakes', 'title': '単純な設備更新', 'content': '単純な設備の更新や維持修繕は対象外です。革新性や生産性向上効果を明確に示してください。', 'importance': 3},
                    {'category': 'success_factors', 'title': '給与支給総額の向上計画', 'content': '従業員の給与支給総額を年率平均1.5%以上向上させる計画を具体的に示してください。', 'importance': 2}
                ]
            },
            # 小規模事業者持続化補助金
            {
                'subsidy_name': '小規模事業者持続化補助金',
                'tips': [
                    {'category': 'preparation', 'title': '商工会・商工会議所との連携', 'content': '商工会・商工会議所の支援を受けて経営計画書を策定することで、申請の質が向上します。', 'importance': 4},
                    {'category': 'application', 'title': '販路開拓の具体的戦略', 'content': '新規顧客獲得や売上拡大につながる具体的な販路開拓戦略を明確に示してください。', 'importance': 4},
                    {'category': 'strategy', 'title': '地域密着型の取り組み', 'content': '地域の特色を活かした取り組みや地域経済への貢献を具体的に示すことが重要です。', 'importance': 3},
                    {'category': 'documents', 'title': '効果的な広告宣伝計画', 'content': 'ホームページ作成、チラシ作成、展示会出展など、効果的な広告宣伝計画を策定してください。', 'importance': 3},
                    {'category': 'common_mistakes', 'title': '単発的な取り組み', 'content': '一時的な販促活動ではなく、継続的な事業発展につながる取り組みを計画してください。', 'importance': 2},
                    {'category': 'success_factors', 'title': '既存事業との相乗効果', 'content': '新しい取り組みが既存事業とどのような相乗効果を生むかを具体的に示してください。', 'importance': 2}
                ]
            },
            # 事業承継・引継ぎ補助金
            {
                'subsidy_name': '事業承継・引継ぎ補助金',
                'tips': [
                    {'category': 'preparation', 'title': '事業承継計画の策定', 'content': '中長期的な事業承継計画を策定し、承継後の事業発展戦略を明確にしてください。', 'importance': 4},
                    {'category': 'application', 'title': '承継者の経営能力証明', 'content': '承継者の経営能力や事業への理解度を具体的な実績や計画で証明してください。', 'importance': 4},
                    {'category': 'strategy', 'title': '既存事業の発展・改善', 'content': '事業承継を機に既存事業をどのように発展・改善させるかを具体的に示してください。', 'importance': 3},
                    {'category': 'documents', 'title': '財務状況の適切な開示', 'content': '承継する事業の財務状況を適切に開示し、健全性や将来性を示してください。', 'importance': 3},
                    {'category': 'common_mistakes', 'title': '承継のみで新規性なし', 'content': '単純な事業承継ではなく、承継を機とした新たな取り組みや改善を明確に示してください。', 'importance': 3},
                    {'category': 'success_factors', 'title': '地域での事業継続価値', 'content': '地域における事業継続の重要性や地域経済への貢献を具体的に示してください。', 'importance': 2}
                ]
            }
        ]
        
        created_count = 0
        
        for subsidy_data in tips_data:
            try:
                subsidy = SubsidyType.objects.get(name=subsidy_data['subsidy_name'])
                
                for tip_data in subsidy_data['tips']:
                    tip, created = AdoptionTips.objects.get_or_create(
                        subsidy_type=subsidy,
                        title=tip_data['title'],
                        defaults={
                            'category': tip_data['category'],
                            'content': tip_data['content'],
                            'importance': tip_data['importance']
                        }
                    )
                    
                    if created:
                        created_count += 1
            
            except SubsidyType.DoesNotExist:
                self.stdout.write(f'  ⚠️ 補助金が見つかりません: {subsidy_data["subsidy_name"]}')
        
        self.stdout.write(f'  ✓ 採択ティップス {created_count}件を作成')

    def load_sample_application_history(self):
        """サンプル申請履歴を投入"""
        self.stdout.write('📋 サンプル申請履歴を投入中...')
        
        # サンプルユーザーを作成（存在しない場合）
        sample_users = [
            {'username': 'sample_user1', 'email': 'user1@example.com', 'first_name': '太郎', 'last_name': '田中'},
            {'username': 'sample_user2', 'email': 'user2@example.com', 'first_name': '花子', 'last_name': '佐藤'},
            {'username': 'sample_user3', 'email': 'user3@example.com', 'first_name': '次郎', 'last_name': '鈴木'},
        ]
        
        users = []
        for user_data in sample_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name']
                }
            )
            users.append(user)
        
        subsidies = SubsidyType.objects.all()
        business_types = ['製造業', 'IT・情報通信業', 'サービス業', '建設業', '小売業']
        company_sizes = ['小規模事業者', '中小企業', '中堅企業']
        statuses = ['preparing', 'submitted', 'under_review', 'adopted', 'rejected']
        
        created_count = 0
        
        for user in users:
            # 各ユーザーに2-5件の申請履歴を作成
            num_applications = random.randint(2, 5)
            
            for _ in range(num_applications):
                subsidy = random.choice(subsidies)
                status = random.choice(statuses)
                
                # 申請日は過去1-3年
                days_ago = random.randint(30, 1095)
                app_date = date.today() - timedelta(days=days_ago)
                
                # 結果発表日（採択・不採択の場合）
                result_date = None
                if status in ['adopted', 'rejected']:
                    result_date = app_date + timedelta(days=random.randint(60, 120))
                
                # 申請金額
                max_amount = subsidy.max_amount
                requested_amount = random.randint(int(max_amount * 0.3), int(max_amount * 0.8))
                
                history, created = UserApplicationHistory.objects.get_or_create(
                    user=user,
                    subsidy_type=subsidy,
                    application_date=app_date,
                    defaults={
                        'application_round': random.randint(1, 3),
                        'status': status,
                        'result_date': result_date,
                        'business_type_at_application': random.choice(business_types),
                        'company_size_at_application': random.choice(company_sizes),
                        'requested_amount': requested_amount,
                        'feedback': self.generate_sample_feedback(status)
                    }
                )
                
                if created:
                    created_count += 1
        
        self.stdout.write(f'  ✓ サンプル申請履歴 {created_count}件を作成')

    def generate_sample_feedback(self, status):
        """ステータスに応じたサンプルフィードバックを生成"""
        feedback_templates = {
            'adopted': [
                '事業計画が具体的で実現可能性が高く評価されました。',
                '革新性と市場性が十分に示されており、採択となりました。',
                '地域経済への貢献が期待でき、優秀な提案として採択されました。'
            ],
            'rejected': [
                '事業計画の具体性が不足しており、実現可能性に疑問が残りました。',
                '市場分析が不十分で、事業の優位性が明確ではありませんでした。',
                '財務計画に問題があり、事業継続性に懸念が見られました。'
            ],
            'under_review': [
                '現在審査中です。結果は後日お知らせいたします。'
            ],
            'submitted': [
                '申請書類を受理いたしました。審査開始までお待ちください。'
            ],
            'preparing': [
                '申請準備中です。'
            ]
        }
        
        templates = feedback_templates.get(status, [''])
        return random.choice(templates) if templates else ''