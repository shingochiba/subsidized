# advisor/management/commands/update_subsidy_aliases.py
from django.core.management.base import BaseCommand
import os
import re
from advisor.models import SubsidyType

class Command(BaseCommand):
    help = 'AIアドバイザーのエイリアス辞書を現在の補助金データベースに合わせて更新します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--preview',
            action='store_true',
            help='変更内容をプレビューのみ表示（実際の更新は行わない）'
        )

    def handle(self, *args, **options):
        self.stdout.write('🔧 補助金エイリアス辞書の更新を開始します...\n')
        
        # 現在登録されている補助金を取得
        current_subsidies = SubsidyType.objects.all().values_list('name', flat=True)
        
        # 完全版エイリアス辞書を生成
        complete_aliases = self._generate_complete_aliases(current_subsidies)
        
        # ファイルパスを特定
        nlp_service_path = 'advisor/services/nlp_ai_advisor.py'
        
        if not os.path.exists(nlp_service_path):
            self.stdout.write(self.style.ERROR(f'❌ ファイルが見つかりません: {nlp_service_path}'))
            return
        
        if options['preview']:
            self._preview_changes(complete_aliases, current_subsidies)
        else:
            self._update_nlp_service_file(nlp_service_path, complete_aliases)
            
        self.stdout.write('✅ エイリアス辞書の更新が完了しました！')

    def _generate_complete_aliases(self, subsidies):
        """現在の補助金データベースから完全なエイリアス辞書を生成"""
        aliases = {}
        
        for subsidy_name in subsidies:
            aliases[subsidy_name] = self._generate_aliases_for_subsidy(subsidy_name)
        
        return aliases

    def _generate_aliases_for_subsidy(self, subsidy_name):
        """個別補助金のエイリアス生成"""
        name_lower = subsidy_name.lower()
        aliases = []
        
        # 基本パターン
        aliases.append(subsidy_name.lower())
        
        # 補助金名からのバリエーション生成
        if 'IT導入補助金' in subsidy_name or 'it導入' in name_lower:
            aliases.extend([
                'it導入', 'ＩＴ導入', 'アイティー導入', 'ITツール', 'デジタル化補助',
                'it導入補助金', 'IT導入補助金', 'ITシステム', 'ソフトウェア補助',
                'デジタル補助', 'システム導入', 'デジタル化支援'
            ])
        
        elif 'ものづくり補助金' in subsidy_name:
            aliases.extend([
                'ものづくり', '製造補助', '設備投資', '生産性向上', 'ものづくり補助金',
                '革新的サービス', '試作品開発', '生産プロセス改善', '設備更新',
                '製造業補助', '機械設備'
            ])
            
        elif '小規模事業者持続化補助金【一般型】' in subsidy_name:
            aliases.extend([
                '持続化', '小規模持続', '販路開拓', '小規模事業者', '持続化補助金',
                '持続化一般', '一般型持続化', '販路拡大', '認知度向上',
                '小規模補助', '販促支援'
            ])
            
        elif '小規模事業者持続化補助金【創業型】' in subsidy_name:
            aliases.extend([
                '持続化創業', '創業型持続化', '創業補助', '新規開業', '起業支援',
                '創業5年', 'スタートアップ支援', '創業期補助', '創業支援',
                '起業補助'
            ])
            
        elif '省力化投資補助金' in subsidy_name:
            aliases.extend([
                '省力化', '省力化投資', '人手不足解消', '自動化', '効率化投資',
                'IoT補助', 'AI導入', 'ロボット導入', '省人化', '労働力不足',
                '人材不足対策', '自動化設備'
            ])
            
        elif '事業承継・M&A補助金' in subsidy_name:
            aliases.extend([
                '事業承継', '承継補助', '引継ぎ', '後継者', '事業承継補助金',
                'M&A補助', '買収補助', '経営承継', '世代交代', '事業引継ぎ',
                'ma補助', 'エムアンドエー'
            ])
            
        elif '新事業進出補助金' in subsidy_name:
            aliases.extend([
                '新事業', '新分野進出', '事業拡大', '多角化', '新商品開発',
                '新サービス', '市場開拓', '事業転換', '新規事業',
                '分野拡大'
            ])
            
        elif '成長加速化補助金' in subsidy_name:
            aliases.extend([
                '成長加速', '成長促進', '事業拡大', 'スケールアップ', '競争力強化',
                'グローバル展開', '海外進出', '人材育成補助', '成長支援',
                '拡大支援'
            ])
            
        elif '省エネ診断・省エネ・非化石転換補助金' in subsidy_name:
            aliases.extend([
                '省エネ', '省エネルギー', '非化石', 'カーボンニュートラル', '脱炭素',
                '再生可能エネルギー', 'CO2削減', '環境対応', 'グリーン化',
                '省エネ設備', '環境補助'
            ])
            
        elif '雇用調整助成金' in subsidy_name:
            aliases.extend([
                '雇用調整', '雇調金', '休業補償', '雇用維持', '労働者支援',
                '一時休業', '事業縮小', '雇用安定', '雇用助成',
                '休業手当'
            ])
            
        elif '業務改善助成金' in subsidy_name:
            aliases.extend([
                '業務改善', '賃金引上げ', '最低賃金', '生産性向上', '働き方改革',
                '労働環境改善', '設備改善', '職場改善', '賃上げ',
                '労働条件改善'
            ])
            
        elif '創業助成金' in subsidy_name:
            aliases.extend([
                '創業', '起業', 'スタートアップ', '新規開業', '開業支援',
                '創業支援', '起業助成', '新規事業', '開業助成'
            ])
            
        elif '事業再構築補助金' in subsidy_name:
            aliases.extend([
                '再構築', '事業転換', '新分野展開', '業態転換', '事業再構築補助金',
                'V字回復', '事業変革', '構造改革', 'ピボット'
            ])
            
        # 年度表記の除去バリエーション
        base_name = re.sub(r'20\d{2}', '', subsidy_name)
        if base_name != subsidy_name:
            aliases.append(base_name.lower())
            
        # 「補助金」「助成金」の除去バリエーション
        no_subsidy = subsidy_name.replace('補助金', '').replace('助成金', '')
        if no_subsidy != subsidy_name:
            aliases.append(no_subsidy.lower())
        
        # 重複を除去して返す
        return list(set(aliases))

    def _preview_changes(self, complete_aliases, current_subsidies):
        """変更内容をプレビュー表示"""
        self.stdout.write('📋 更新プレビュー:\n')
        
        self.stdout.write(f'🗂️  対象補助金数: {len(current_subsidies)}件\n')
        
        for subsidy_name in sorted(current_subsidies):
            aliases = complete_aliases[subsidy_name]
            self.stdout.write(f'📌 {subsidy_name}')
            self.stdout.write(f'   エイリアス数: {len(aliases)}個')
            if len(aliases) <= 10:
                self.stdout.write(f'   └ {", ".join(aliases[:5])}{"..." if len(aliases) > 5 else ""}')
            self.stdout.write('')
        
        self.stdout.write('⚠️  --preview モードのため、実際の更新は行いませんでした')
        self.stdout.write('   実際に更新するには --preview オプションを外して実行してください')

    def _update_nlp_service_file(self, file_path, complete_aliases):
        """NLPサービスファイルのエイリア辞書を更新"""
        
        # ファイルを読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 新しいエイリアス辞書のコードを生成
        new_aliases_code = self._generate_aliases_code(complete_aliases)
        
        # subsidy_aliases の部分を置換
        pattern = r'self\.subsidy_aliases\s*=\s*{[^}]*}(?:\s*})*'
        
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(
                pattern,
                f'self.subsidy_aliases = {new_aliases_code}',
                content,
                flags=re.DOTALL
            )
        else:
            # パターンが見つからない場合は、_initialize_nlp_patterns メソッド内に追加
            init_pattern = r'(def _initialize_nlp_patterns\(self\):.*?""")'
            replacement = r'\1\n        \n        # 完全版補助金エイリアス辞書\n        self.subsidy_aliases = ' + new_aliases_code
            new_content = re.sub(init_pattern, replacement, content, flags=re.DOTALL)
        
        # ファイルに書き戻し
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        self.stdout.write(f'✅ {file_path} を更新しました')

    def _generate_aliases_code(self, aliases_dict):
        """エイリアス辞書のPythonコードを生成"""
        lines = ['{']
        
        for subsidy_name, aliases in sorted(aliases_dict.items()):
            # エイリアスリストを整形
            if len(aliases) <= 3:
                aliases_str = str(aliases)
            else:
                # 長いリストは複数行に分割
                aliases_formatted = '[\n                '
                aliases_formatted += ',\n                '.join(f"'{alias}'" for alias in aliases)
                aliases_formatted += '\n            ]'
                aliases_str = aliases_formatted
            
            lines.append(f"            '{subsidy_name}': {aliases_str},")
        
        lines.append('        }')
        
        return '\n'.join(lines)