# advisor/management/commands/test_aliases_quick.py
from django.core.management.base import BaseCommand
from advisor.services.nlp_ai_advisor import NLPAIAdvisorService
from advisor.models import SubsidyType

class Command(BaseCommand):
    help = 'エイリアス機能の動作をクイックテストします'

    def handle(self, *args, **options):
        self.stdout.write('🧪 エイリアス機能のクイックテストを開始します...\n')
        
        try:
            # サービス初期化テスト
            service = NLPAIAdvisorService()
            self.stdout.write(f'✅ サービス初期化: 成功')
            self.stdout.write(f'📊 補助金データ読み込み: {len(service.subsidies)}件')
            self.stdout.write(f'📝 エイリアス辞書: {len(service.subsidy_aliases)}件\n')
            
            # データベース整合性チェック
            db_subsidies = set(SubsidyType.objects.values_list('name', flat=True))
            alias_subsidies = set(service.subsidy_aliases.keys())
            missing = db_subsidies - alias_subsidies
            
            if missing:
                self.stdout.write(self.style.WARNING(f'⚠️  エイリアス未登録: {len(missing)}件'))
                for subsidy in sorted(missing):
                    self.stdout.write(f'  • {subsidy}')
                self.stdout.write('')
            else:
                self.stdout.write(self.style.SUCCESS('✅ 全補助金にエイリアス登録済み\n'))
            
            # 認識テスト
            test_cases = [
                ("IT導入補助金について教えて", "IT導入"),
                ("省力化について知りたい", "省力化投資"),
                ("ものづくり補助金の詳細", "ものづくり"),
                ("持続化補助金を申請したい", "持続化"),
                ("雇調金の要件は？", "雇用調整"),
                ("創業支援はありますか？", "創業"),
                ("人手不足を解消したい", "省力化"),
                ("デジタル化を進めたい", "IT導入"),
            ]
            
            self.stdout.write('🎯 認識テスト結果:')
            success_count = 0
            
            for question, expected_keyword in test_cases:
                result = service._identify_target_subsidy_enhanced(question)
                
                if result and expected_keyword in result.name:
                    self.stdout.write(f'  ✅ "{question}" → {result.name}')
                    success_count += 1
                elif result:
                    self.stdout.write(f'  ⚠️  "{question}" → {result.name} (期待: {expected_keyword})')
                else:
                    self.stdout.write(f'  ❌ "{question}" → 認識失敗')
            
            # 結果サマリー
            success_rate = (success_count / len(test_cases)) * 100
            self.stdout.write(f'\n📈 認識成功率: {success_rate:.1f}% ({success_count}/{len(test_cases)})')
            
            if success_rate >= 80:
                self.stdout.write(self.style.SUCCESS('🎉 エイリアス機能は正常に動作しています！'))
            elif success_rate >= 60:
                self.stdout.write(self.style.WARNING('⚠️  エイリアス機能に改善の余地があります'))
            else:
                self.stdout.write(self.style.ERROR('❌ エイリアス機能に問題があります'))
            
            # パフォーマンステスト
            import time
            start_time = time.time()
            
            for _ in range(100):
                service._identify_target_subsidy_enhanced("IT導入補助金について")
            
            elapsed = time.time() - start_time
            avg_time = elapsed / 100
            
            self.stdout.write(f'⚡ パフォーマンス: 平均{avg_time*1000:.1f}ms/クエリ')
            
            if avg_time < 0.01:
                self.stdout.write(self.style.SUCCESS('⚡ 高速動作確認'))
            elif avg_time < 0.05:
                self.stdout.write(self.style.WARNING('⚠️  動作やや重い'))
            else:
                self.stdout.write(self.style.ERROR('❌ 動作が重すぎます'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ テスト中にエラーが発生しました: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())