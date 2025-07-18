# advisor/services/enhanced_ai_advisor_service.py
# AIアドバイザーサービスの拡張版（新規補助金対応）

import re
from django.conf import settings
from ..models import SubsidyType, Answer, ConversationHistory

class EnhancedAIAdvisorService:
    """新規補助金に完全対応したAIアドバイザーサービス"""
    
    def __init__(self):
        self.subsidies = list(SubsidyType.objects.all())
        self._initialize_enhanced_patterns()
    
    def _initialize_enhanced_patterns(self):
        """新規補助金を含む拡張パターンの初期化"""
        
        # 更新された補助金エイリアス辞書（全補助金対応）
        self.subsidy_aliases = {
            'IT導入補助金': [
                'it導入', 'ＩＴ導入', 'アイティー導入', 'ITツール', 'デジタル化補助',
                'it導入補助金', 'IT導入補助金', 'ITシステム', 'ソフトウェア補助',
                'デジタル補助', 'システム導入'
            ],
            'ものづくり補助金': [
                'ものづくり', '製造補助', '設備投資', '生産性向上', 'ものづくり補助金',
                '革新的サービス', '試作品開発', '生産プロセス改善', '設備更新'
            ],
            '小規模事業者持続化補助金【一般型】': [
                '持続化', '小規模持続', '販路開拓', '小規模事業者', '持続化補助金',
                '持続化一般', '一般型持続化', '販路拡大', '認知度向上'
            ],
            '小規模事業者持続化補助金【創業型】': [
                '持続化創業', '創業型持続化', '創業補助', '新規開業', '起業支援',
                '創業5年', 'スタートアップ支援', '創業期補助'
            ],
            '省力化投資補助金': [
                '省力化', '省力化投資', '人手不足解消', '自動化', '効率化投資',
                'IoT補助', 'AI導入', 'ロボット導入', '省人化', '労働力不足'
            ],
            '事業承継・M&A補助金': [
                '事業承継', '承継補助', '引継ぎ', '後継者', '事業承継補助金',
                'M&A補助', '買収補助', '経営承継', '世代交代', '事業引継ぎ'
            ],
            '新事業進出補助金': [
                '新事業', '新分野進出', '事業拡大', '多角化', '新商品開発',
                '新サービス', '市場開拓', '事業転換'
            ],
            '成長加速化補助金': [
                '成長加速', '成長促進', '事業拡大', 'スケールアップ', '競争力強化',
                'グローバル展開', '海外進出', '人材育成補助'
            ],
            '省エネ診断・省エネ・非化石転換補助金': [
                '省エネ', '省エネルギー', '非化石', 'カーボンニュートラル', '脱炭素',
                '再生可能エネルギー', 'CO2削減', '環境対応', 'グリーン化'
            ],
            '雇用調整助成金': [
                '雇用調整', '雇調金', '休業補償', '雇用維持', '労働者支援',
                '一時休業', '事業縮小', '雇用安定'
            ],
            '業務改善助成金': [
                '業務改善', '賃金引上げ', '最低賃金', '生産性向上', '働き方改革',
                '労働環境改善', '設備改善'
            ]
        }
        
        # 業種別推奨補助金マッピング（拡張版）
        self.industry_subsidy_mapping = {
            '製造業': [
                'ものづくり補助金', '省力化投資補助金', '省エネ診断・省エネ・非化石転換補助金',
                'IT導入補助金', '業務改善助成金'
            ],
            'IT・情報通信業': [
                'IT導入補助金', '成長加速化補助金', '新事業進出補助金',
                'ものづくり補助金', '省力化投資補助金'
            ],
            'サービス業': [
                '小規模事業者持続化補助金【一般型】', 'IT導入補助金', '業務改善助成金',
                '省力化投資補助金', '新事業進出補助金'
            ],
            '小売業': [
                '小規模事業者持続化補助金【一般型】', 'IT導入補助金', '省力化投資補助金',
                '新事業進出補助金', '業務改善助成金'
            ],
            '建設業': [
                'ものづくり補助金', '省力化投資補助金', 'IT導入補助金',
                '業務改善助成金', '省エネ診断・省エネ・非化石転換補助金'
            ],
            '農業・林業・漁業': [
                '省力化投資補助金', 'ものづくり補助金', 'IT導入補助金',
                '省エネ診断・省エネ・非化石転換補助金'
            ],
            '運輸業': [
                '省力化投資補助金', 'IT導入補助金', '省エネ診断・省エネ・非化石転換補助金',
                '業務改善助成金'
            ],
            '飲食業': [
                '小規模事業者持続化補助金【一般型】', 'IT導入補助金', '業務改善助成金',
                '省力化投資補助金'
            ],
            '創業・スタートアップ': [
                '小規模事業者持続化補助金【創業型】', 'IT導入補助金', '成長加速化補助金',
                '新事業進出補助金'
            ]
        }
        
        # 課題別推奨補助金マッピング（新規追加）
        self.challenge_subsidy_mapping = {
            '人手不足': ['省力化投資補助金', '業務改善助成金', 'IT導入補助金'],
            'デジタル化': ['IT導入補助金', '省力化投資補助金', 'ものづくり補助金'],
            '売上拡大': ['小規模事業者持続化補助金【一般型】', '新事業進出補助金', '成長加速化補助金'],
            '生産性向上': ['ものづくり補助金', '省力化投資補助金', '業務改善助成金'],
            '環境対応': ['省エネ診断・省エネ・非化石転換補助金', 'ものづくり補助金'],
            '事業承継': ['事業承継・M&A補助金', '成長加速化補助金'],
            '創業支援': ['小規模事業者持続化補助金【創業型】', '新事業進出補助金'],
            '雇用維持': ['雇用調整助成金', '業務改善助成金'],
            '設備投資': ['ものづくり補助金', '省力化投資補助金', '省エネ診断・省エネ・非化石転換補助金']
        }
        
        # 企業規模別推奨補助金
        self.company_size_mapping = {
            '小規模事業者': [
                '小規模事業者持続化補助金【一般型】',
                '小規模事業者持続化補助金【創業型】',
                'IT導入補助金', '業務改善助成金'
            ],
            '中小企業': [
                'ものづくり補助金', '省力化投資補助金', 'IT導入補助金',
                '成長加速化補助金', '新事業進出補助金', '事業承継・M&A補助金'
            ]
        }

    def analyze_question_enhanced(self, question_text, user_context=None):
        """拡張された質問分析（新規補助金対応）"""
        
        analysis_result = {
            'identified_subsidies': [],
            'recommended_subsidies': [],
            'business_analysis': {},
            'priority_recommendations': [],
            'next_actions': []
        }
        
        # Step 1: 明示的に言及された補助金を特定
        identified = self._identify_mentioned_subsidies(question_text)
        analysis_result['identified_subsidies'] = identified
        
        # Step 2: ビジネス情報を抽出
        business_info = self._extract_business_context(question_text, user_context)
        analysis_result['business_analysis'] = business_info
        
        # Step 3: 業種・課題・規模に基づく推奨
        recommendations = self._generate_smart_recommendations(business_info, question_text)
        analysis_result['recommended_subsidies'] = recommendations
        
        # Step 4: 優先度付きアクションプランを生成
        priority_plan = self._create_priority_action_plan(recommendations, business_info)
        analysis_result['priority_recommendations'] = priority_plan
        
        # Step 5: 次のステップを提案
        next_actions = self._suggest_next_actions(recommendations, business_info)
        analysis_result['next_actions'] = next_actions
        
        return analysis_result

    def _identify_mentioned_subsidies(self, question_text):
        """質問文中で明示的に言及された補助金を特定"""
        identified = []
        question_lower = question_text.lower()
        
        for subsidy_name, aliases in self.subsidy_aliases.items():
            # 正確な名前でのマッチング
            if subsidy_name.lower() in question_lower:
                identified.append(subsidy_name)
                continue
            
            # エイリアスでのマッチング
            for alias in aliases:
                if alias.lower() in question_lower:
                    identified.append(subsidy_name)
                    break
        
        return list(set(identified))

    def _extract_business_context(self, question_text, user_context):
        """質問文とユーザーコンテキストからビジネス情報を抽出"""
        context = {
            'industry': None,
            'company_size': None,
            'challenges': [],
            'goals': [],
            'technology_needs': [],
            'urgency_level': 'normal'
        }
        
        question_lower = question_text.lower()
        
        # 業種の特定
        industry_keywords = {
            '製造業': ['製造', '工場', '生産', 'メーカー', '機械'],
            'IT・情報通信業': ['it', 'システム', 'ソフト', 'web', 'アプリ', 'デジタル'],
            'サービス業': ['サービス', 'コンサル', '士業', '専門サービス'],
            '小売業': ['小売', '販売', '店舗', 'ec', '通販'],
            '建設業': ['建設', '工事', '施工', '建築'],
            '飲食業': ['飲食', 'レストラン', 'カフェ', '居酒屋'],
            '農業・林業・漁業': ['農業', '漁業', '林業', '農家', '漁師'],
            '運輸業': ['運送', '配送', '物流', 'トラック']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                context['industry'] = industry
                break
        
        # 企業規模の特定
        if any(word in question_lower for word in ['小規模', '個人事業', '零細']):
            context['company_size'] = '小規模事業者'
        elif any(word in question_lower for word in ['中小企業', '中小']):
            context['company_size'] = '中小企業'
        
        # 課題の特定
        challenge_keywords = {
            '人手不足': ['人手不足', '人材不足', '採用難', '労働力'],
            'デジタル化': ['デジタル化', 'dx', 'システム化', 'it化'],
            '売上拡大': ['売上', '収益', '販路', '新規顧客'],
            '生産性向上': ['生産性', '効率', '自動化', '省力化'],
            '環境対応': ['環境', '省エネ', 'co2', 'カーボン'],
            '事業承継': ['事業承継', '後継者', '世代交代'],
            '創業支援': ['創業', '起業', 'スタートアップ'],
            '設備投資': ['設備', '機械', '装置', '導入']
        }
        
        for challenge, keywords in challenge_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                context['challenges'].append(challenge)
        
        # 緊急度の判定
        if any(word in question_lower for word in ['急い', '至急', 'すぐ', '早く']):
            context['urgency_level'] = 'high'
        
        return context

    def _generate_smart_recommendations(self, business_info, question_text):
        """ビジネス情報に基づくスマートな推奨補助金生成"""
        recommendations = []
        scored_subsidies = {}
        
        # 業種ベースの推奨
        if business_info['industry']:
            industry_subsidies = self.industry_subsidy_mapping.get(business_info['industry'], [])
            for subsidy_name in industry_subsidies:
                scored_subsidies[subsidy_name] = scored_subsidies.get(subsidy_name, 0) + 3
        
        # 課題ベースの推奨
        for challenge in business_info['challenges']:
            challenge_subsidies = self.challenge_subsidy_mapping.get(challenge, [])
            for subsidy_name in challenge_subsidies:
                scored_subsidies[subsidy_name] = scored_subsidies.get(subsidy_name, 0) + 2
        
        # 企業規模ベースの推奨
        if business_info['company_size']:
            size_subsidies = self.company_size_mapping.get(business_info['company_size'], [])
            for subsidy_name in size_subsidies:
                scored_subsidies[subsidy_name] = scored_subsidies.get(subsidy_name, 0) + 2
        
        # スコア順にソート
        sorted_subsidies = sorted(scored_subsidies.items(), key=lambda x: x[1], reverse=True)
        
        # 上位5つを推奨として返す
        recommendations = [name for name, score in sorted_subsidies[:5]]
        
        return recommendations

    def _create_priority_action_plan(self, recommendations, business_info):
        """優先度付きアクションプランの作成"""
        plan = []
        
        for i, subsidy_name in enumerate(recommendations[:3]):
            try:
                subsidy = SubsidyType.objects.get(name=subsidy_name)
                priority = ['高', '中', '低'][i] if i < 3 else '低'
                
                action_item = {
                    'subsidy_name': subsidy_name,
                    'priority': priority,
                    'max_amount': f'{subsidy.max_amount}万円',
                    'difficulty': ['易', '普通', '難', '高', '最高'][subsidy.application_difficulty - 1],
                    'preparation_weeks': subsidy.average_preparation_weeks,
                    'success_rate': f'{int(subsidy.historical_success_rate * 100)}%'
                }
                plan.append(action_item)
            except SubsidyType.DoesNotExist:
                continue
        
        return plan

    def _suggest_next_actions(self, recommendations, business_info):
        """次のアクションステップを提案"""
        actions = []
        
        if business_info['urgency_level'] == 'high':
            actions.append('⚡ 緊急性が高いため、申請期限の確認を最優先で行ってください')
        
        if business_info['company_size'] == '小規模事業者':
            actions.append('🏢 商工会議所または商工会での事前相談をお勧めします')
        
        if 'デジタル化' in business_info['challenges']:
            actions.append('💻 IT導入補助金の対象ツール検索サイトで具体的なソリューションを確認してください')
        
        actions.extend([
            '📋 事業計画書のドラフト作成を開始してください',
            '📊 過去3年間の財務データをまとめてください',
            '🎯 補助事業の具体的な成果目標を設定してください'
        ])
        
        return actions

    def generate_comprehensive_response(self, question_text, user_context=None):
        """包括的な回答生成（新規補助金対応）"""
        analysis = self.analyze_question_enhanced(question_text, user_context)
        
        response = f"""
## 🎯 あなたの状況に最適な補助金をご提案します

### 📊 ビジネス分析結果
"""
        
        if analysis['business_analysis']['industry']:
            response += f"- **業種**: {analysis['business_analysis']['industry']}\n"
        
        if analysis['business_analysis']['company_size']:
            response += f"- **企業規模**: {analysis['business_analysis']['company_size']}\n"
        
        if analysis['business_analysis']['challenges']:
            response += f"- **主な課題**: {', '.join(analysis['business_analysis']['challenges'])}\n"
        
        response += "\n### 🏆 優先度別推奨補助金\n\n"
        
        for item in analysis['priority_recommendations']:
            response += f"""
**{item['priority']}優先度: {item['subsidy_name']}**
- 💰 補助上限: {item['max_amount']}
- 📈 成功率: {item['success_rate']}
- ⏱️ 準備期間: {item['preparation_weeks']}週
- 🎯 難易度: {item['difficulty']}
"""
        
        response += "\n### 📋 次のアクションステップ\n\n"
        for action in analysis['next_actions']:
            response += f"- {action}\n"
        
        response += """
### 💡 成功のポイント
- 早期準備が採択率向上の鍵です
- 具体的な数値目標を設定しましょう
- 専門家との連携を積極的に活用してください

**ご不明な点があれば、いつでもお気軽にご相談ください！**
"""
        
        return response.strip()