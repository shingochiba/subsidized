# advisor/management/commands/load_strategic_tips.py

from django.core.management.base import BaseCommand
from advisor.models import SubsidyType, AdoptionTips

class Command(BaseCommand):
    help = '戦略的な採択ティップスを投入します'

    def handle(self, *args, **options):
        self.stdout.write('🎯 戦略的採択ティップスの投入を開始します...')
        
        self.load_strategic_tips()
        
        self.stdout.write(
            self.style.SUCCESS('✅ 戦略的採択ティップスの投入が完了しました！')
        )

    def load_strategic_tips(self):
        """戦略・作戦に関する具体的なティップスを投入"""
        
        strategic_tips = [
            # IT導入補助金の戦略
            {
                'subsidy_name': 'IT導入補助金2025',
                'tips': [
                    {
                        'category': 'strategy',
                        'title': '早期申請による「やる気アピール」戦略',
                        'content': '公募開始から2週間以内の申請は、審査員に「計画性」と「やる気」をアピールできます。2024年度実績では早期申請者の採択率が平均より15%高い結果となっています。締切直前の申請は審査員の疲労もあり、厳しく評価される傾向があります。',
                        'importance': 4,
                        'effective_timing': '公募開始直後～2週間以内',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '競合他社との差別化「ニッチ特化」戦略',
                        'content': '同業他社が注目しない特定の業務領域や顧客セグメントにフォーカスした提案で差別化を図りましょう。例：「高齢者向けサービスのデジタル化」「地域限定の配送効率化」など。ニッチ分野での独自性は審査員の記憶に残りやすく、採択率向上につながります。',
                        'importance': 4,
                        'effective_timing': '事業計画策定時',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '段階的導入による「リスク軽減」戦略',
                        'content': '一度に大規模システムを導入するより、段階的な導入計画を示すことで実現可能性をアピールできます。第1段階で基本機能、第2段階で応用機能という具体的なステップを示し、各段階での効果測定方法も明記してください。',
                        'importance': 3,
                        'effective_timing': '事業計画書作成時',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '既存顧客の声を活用した「需要実証」戦略',
                        'content': '既存顧客からの「こんなシステムがあれば便利」という具体的な声を収集し、申請書に盛り込みましょう。顧客ニーズの実在性を証明できれば、審査員は事業の成功可能性を高く評価します。可能であれば顧客の推薦状も添付してください。',
                        'importance': 3,
                        'effective_timing': '申請書作成前の準備期間',
                        'is_success_case': True
                    }
                ]
            },
            # 事業再構築補助金の戦略
            {
                'subsidy_name': '事業再構築補助金',
                'tips': [
                    {
                        'category': 'strategy',
                        'title': '「既存事業×新技術」のシナジー創出戦略',
                        'content': '全く新しい事業より、既存事業の強みを活かした新分野展開の方が採択されやすい傾向があります。例：「製造業の技術力×医療機器」「飲食店の接客ノウハウ×介護サービス」など。既存リソースの有効活用により実現可能性と競争優位性を同時にアピールできます。',
                        'importance': 4,
                        'effective_timing': '事業再構築計画の初期段階',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '地域課題解決による「社会性アピール」戦略',
                        'content': '事業再構築が地域の課題解決につながることを明確に示しましょう。高齢化、人口減少、地域経済の活性化など、地域が抱える問題とビジネスを結びつけることで、審査員は高い社会的意義を評価します。地域雇用の創出効果も具体的な数値で示してください。',
                        'importance': 4,
                        'effective_timing': '事業計画策定時',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '保守的財務計画による「信頼性確保」戦略',
                        'content': '売上予測は業界平均より10-20%保守的に設定し、その根拠を詳細に説明してください。過度に楽観的な計画は審査員の不信を招きます。「最低これだけは確実に達成できる」という堅実な計画と、「努力目標としてこれを目指す」という上振れシナリオの両方を提示するのが効果的です。',
                        'importance': 4,
                        'effective_timing': '財務計画作成時',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '競合分析の徹底による「優位性証明」戦略',
                        'content': '同様の事業再構築を行う可能性のある競合他社を徹底的に分析し、自社の優位性を明確に示してください。技術力、顧客基盤、立地条件、人材など、多角的な観点から競合優位性を説明することが重要です。「なぜ自社が成功できるのか」の根拠を具体的に提示しましょう。',
                        'importance': 3,
                        'effective_timing': '市場分析段階',
                        'is_success_case': True
                    }
                ]
            },
            # ものづくり補助金の戦略
            {
                'subsidy_name': 'ものづくり補助金',
                'tips': [
                    {
                        'category': 'strategy',
                        'title': '技術革新性の「見える化」戦略',
                        'content': '導入設備の技術的優位性を、図表や写真を使って分かりやすく説明してください。「従来比○○%の精度向上」「業界初の○○技術」など、技術者でない審査員にも理解できるような表現で革新性をアピールしましょう。可能であれば設備メーカーからの技術証明書も添付してください。',
                        'importance': 4,
                        'effective_timing': '設備選定・申請書作成時',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '生産性向上の「数値実証」戦略',
                        'content': '設備導入による生産性向上効果を、時間短縮、コスト削減、品質向上の3つの観点から数値で示してください。例：「加工時間50%短縮」「不良率0.5%→0.1%」「人件費年間300万円削減」など。根拠となる現状データと改善後の予測データを比較表で示すと説得力が増します。',
                        'importance': 4,
                        'effective_timing': '効果算定時',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '受注拡大の「具体的根拠」戦略',
                        'content': '設備導入により新たに受注可能となる案件を具体的に示してください。「A社から○○の引き合いがあり、新設備があれば受注可能」「B社との取引拡大が見込める」など、実在する商談や引き合いを根拠として提示することで、審査員は事業の実現可能性を高く評価します。',
                        'importance': 3,
                        'effective_timing': '市場開拓計画策定時',
                        'is_success_case': True
                    }
                ]
            },
            # 小規模事業者持続化補助金の戦略
            {
                'subsidy_name': '小規模事業者持続化補助金',
                'tips': [
                    {
                        'category': 'strategy',
                        'title': '地域密着型の「ストーリー戦略」',
                        'content': '地域の課題や特色と事業を結びつけたストーリーを作りましょう。「地域の高齢化に対応した宅配サービス」「地域特産品の販路拡大」など、地域貢献の要素を盛り込むことで、商工会議所や審査員の共感を得られます。地域での知名度や信頼関係もアピールポイントになります。',
                        'importance': 4,
                        'effective_timing': '事業計画の構想段階',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '商工会議所との「連携最大化」戦略',
                        'content': '商工会議所の経営指導員と密に連携し、申請書作成から事業実施まで継続的なサポートを受けましょう。指導員の豊富な経験と地域ネットワークを活用することで、申請書の質向上と事業成功の両方が期待できます。定期的な相談を通じて、計画の実現可能性を高めてください。',
                        'importance': 4,
                        'effective_timing': '申請準備開始時から継続',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '既存顧客との「関係性活用」戦略',
                        'content': '長年培った顧客との信頼関係を最大限活用し、新しい取り組みへの協力を得ましょう。「常連客からの要望に応える新サービス」「得意先企業との新たな取引機会創出」など、既存の関係性を基盤とした計画は実現可能性が高く評価されます。顧客の声や推薦状があるとさらに効果的です。',
                        'importance': 3,
                        'effective_timing': '事業計画策定時',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '小さく始めて大きく育てる「段階成長」戦略',
                        'content': '小規模事業者らしく、無理のない範囲から始めて段階的に事業を拡大する計画を示しましょう。第1段階で基盤作り、第2段階で本格展開、第3段階で地域展開など、リスクを抑えながら着実に成長する道筋を描くことで、審査員は計画の実現可能性を高く評価します。',
                        'importance': 3,
                        'effective_timing': '中長期計画策定時',
                        'is_success_case': True
                    }
                ]
            },
            # 全補助金共通の戦略
            {
                'subsidy_name': 'IT導入補助金2025',  # 代表として設定
                'tips': [
                    {
                        'category': 'strategy',
                        'title': '審査員の心理を読む「印象操作」戦略',
                        'content': '審査員は1日に数十件の申請書を読むため、印象に残る申請書作りが重要です。冒頭で事業の革新性を端的に表現し、図表を効果的に使い、重要な数値は太字や色付きで強調してください。読みやすく、記憶に残る申請書が採択率向上の鍵となります。',
                        'importance': 3,
                        'effective_timing': '申請書レイアウト設計時',
                        'is_success_case': True
                    },
                    {
                        'category': 'strategy',
                        'title': '不採択時の「学習サイクル」戦略',
                        'content': '万が一不採択となった場合も、フィードバックを真摯に受け止め、次回申請に活かす学習サイクルを回してください。不採択理由の分析、専門家への相談、計画の見直しを行い、より強固な申請書を作成しましょう。継続的な改善により、最終的には必ず採択を勝ち取れます。',
                        'importance': 2,
                        'effective_timing': '不採択通知受領後',
                        'is_success_case': True
                    }
                ]
            }
        ]

        created_count = 0
        
        for tips_group in strategic_tips:
            try:
                subsidy = SubsidyType.objects.get(name=tips_group['subsidy_name'])
                
                for tip_data in tips_group['tips']:
                    tip, created = AdoptionTips.objects.get_or_create(
                        subsidy_type=subsidy,
                        title=tip_data['title'],
                        defaults={
                            'category': tip_data['category'],
                            'content': tip_data['content'],
                            'importance': tip_data['importance'],
                            'effective_timing': tip_data.get('effective_timing', ''),
                            'is_success_case': tip_data.get('is_success_case', False)
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'  ✓ {tip_data["title"][:40]}...')
            
            except SubsidyType.DoesNotExist:
                self.stdout.write(f'  ⚠️ 補助金が見つかりません: {tips_group["subsidy_name"]}')
        
        self.stdout.write(f'  ✅ 戦略的ティップス {created_count}件を作成')