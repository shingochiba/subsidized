# advisor/services/nlp_ai_advisor.py

import requests
import json
import re
from django.conf import settings
from ..models import SubsidyType, Answer, ConversationHistory

class NLPAIAdvisorService:
    """自然言語処理対応の高度なAIアドバイザー"""
    
    def __init__(self):
        self.dify_api_url = settings.DIFY_API_URL
        self.dify_api_key = settings.DIFY_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.dify_api_key}',
            'Content-Type': 'application/json'
        }
        
        # 補助金データを事前読み込み
        self.subsidies = list(SubsidyType.objects.all())
        self._initialize_nlp_patterns()
    
    def _initialize_nlp_patterns(self):
        """自然言語パターンを初期化"""
        
        # 質問の意図分類
        self.intent_patterns = {
            'overview': {
                'patterns': [
                    r'補助金.*とは', r'補助金.*について.*教え', r'補助金.*仕組み',
                    r'どんな.*補助金', r'補助金.*種類', r'補助金.*概要',
                    r'補助金.*全般', r'補助金.*基本', r'補助金.*説明',
                    r'help.*subsidy', r'what.*subsidy', r'explain.*subsidy'
                ],
                'keywords': ['とは', '教えて', '説明', '仕組み', '種類', '概要', '全般', '基本']
            },
            'specific_subsidy': {
                'patterns': [
                    r'IT導入補助金', r'ＩＴ導入補助金', r'アイティー導入補助金',
                    r'事業再構築補助金', r'再構築補助金',
                    r'ものづくり補助金', r'製造業.*補助金',
                    r'持続化補助金', r'小規模.*持続化',
                    r'事業承継.*補助金', r'承継.*補助金'
                ],
                'keywords': ['IT導入', 'ＩＴ導入', '事業再構築', 'ものづくり', '持続化', '事業承継']
            },
            'application_process': {
                'patterns': [
                    r'申請.*方法', r'申請.*手順', r'申請.*やり方', r'申請.*流れ',
                    r'どう.*申請', r'申請.*について', r'申請.*したい',
                    r'必要.*書類', r'書類.*何', r'提出.*書類',
                    r'期限.*いつ', r'締切.*いつ', r'いつまで.*申請'
                ],
                'keywords': ['申請', '手順', 'やり方', '流れ', '書類', '期限', '締切', '提出']
            },
            'requirements': {
                'patterns': [
                    r'要件.*何', r'条件.*何', r'資格.*何', r'対象.*何',
                    r'使える.*か', r'対象.*なる', r'該当.*する',
                    r'うちの.*会社.*対象', r'弊社.*対象', r'当社.*使える'
                ],
                'keywords': ['要件', '条件', '資格', '対象', '該当', '使える', '適用']
            },
            'strategy': {
                'patterns': [
                    r'採択.*され.*方法', r'通り.*やすい', r'成功.*方法',
                    r'採択率.*上げ', r'確率.*高め', r'勝つ.*方法',
                    r'コツ.*教え', r'秘訣.*教え', r'戦略.*教え',
                    r'差別化.*方法', r'競合.*勝つ', r'有利.*進め'
                ],
                'keywords': ['採択', '成功', '確率', 'コツ', '秘訣', '戦略', '差別化', '競合', '有利']
            },
            'amount_rate': {
                'patterns': [
                    r'いくら.*もらえ', r'金額.*いくら', r'補助額.*いくら',
                    r'最大.*いくら', r'上限.*いくら', r'限度額.*いくら',
                    r'補助率.*いくら', r'何割.*補助', r'何パーセント.*補助'
                ],
                'keywords': ['いくら', '金額', '補助額', '最大', '上限', '限度額', '補助率', '何割', 'パーセント']
            },
            'timeline': {
                'patterns': [
                    r'いつ.*申請', r'期限.*いつ', r'締切.*いつ',
                    r'いつから.*いつまで', r'申請期間.*いつ',
                    r'結果.*いつ', r'発表.*いつ', r'通知.*いつ'
                ],
                'keywords': ['いつ', '期限', '締切', '申請期間', '結果', '発表', '通知']
            },
            'business_specific': {
                'patterns': [
                    r'製造業.*補助金', r'IT業.*補助金', r'サービス業.*補助金',
                    r'小売業.*補助金', r'建設業.*補助金', r'農業.*補助金',
                    r'弊社.*業種', r'うちの.*業界', r'当社.*分野'
                ],
                'keywords': ['製造業', 'IT業', 'サービス業', '小売業', '建設業', '農業', '業種', '業界', '分野']
            }
        }
        
        # 感情・丁寧度の分析
        self.tone_patterns = {
            'polite': [r'いただけ', r'お聞かせ', r'お教え', r'恐れ入り', r'申し訳', r'よろしく'],
            'casual': [r'教えて', r'どう', r'なに', r'どこ', r'いくら'],
            'urgent': [r'急い', r'至急', r'すぐ', r'早く', r'間に合わ'],
            'confused': [r'分から', r'よく.*理解', r'難し', r'複雑', r'混乱']
        }
        
        # 補助金の同義語・略語（マッチング精度向上）
        self.subsidy_aliases = {
            'IT導入補助金2025': ['it導入', 'ＩＴ導入', 'アイティー導入', 'ITツール', 'デジタル化補助', 'it導入補助金', 'IT導入補助金'],
            '事業再構築補助金': ['再構築', '事業転換', '新分野展開', '業態転換', '事業再構築補助金'],
            'ものづくり補助金': ['ものづくり', '製造補助', '設備投資', '生産性向上', 'ものづくり補助金'],
            '小規模事業者持続化補助金': ['持続化', '小規模持続', '販路開拓', '小規模事業者', '持続化補助金'],
            '事業承継・引継ぎ補助金': ['事業承継', '承継補助', '引継ぎ', '後継者', '事業承継補助金']
        }
    
    def analyze_question(self, question_text, user_context=None):
        """自然言語解析による質問分析"""
        
        # Step 1: 質問の意図を分析
        intent = self._analyze_intent(question_text)
        
        # Step 2: 対象補助金を特定
        target_subsidy = self._identify_target_subsidy(question_text)
        
        # Step 3: 感情・丁寧度を分析
        tone = self._analyze_tone(question_text)
        
        # Step 4: ビジネス情報を抽出
        business_info = self._extract_business_info(question_text, user_context)
        
        # Step 5: 回答を生成
        response = self._generate_contextual_response(
            question_text, intent, target_subsidy, tone, business_info, user_context
        )
        
        return response
    
    def _analyze_intent(self, question_text):
        """質問の意図を分析"""
        question_lower = question_text.lower()
        intent_scores = {}
        
        # まず補助金名が含まれているかチェック
        has_specific_subsidy = self._identify_target_subsidy(question_text) is not None
        
        for intent_type, config in self.intent_patterns.items():
            score = 0
            
            # パターンマッチング
            for pattern in config['patterns']:
                if re.search(pattern, question_text):
                    score += 3
            
            # キーワードマッチング
            for keyword in config['keywords']:
                if keyword in question_lower:
                    score += 1
            
            intent_scores[intent_type] = score
        
        # 特定の補助金名がある場合は、specific_subsidyの優先度を上げる
        if has_specific_subsidy:
            intent_scores['specific_subsidy'] += 5
            
            # 「〜について教えて」のパターンなら確実にspecific_subsidy
            if re.search(r'について.*教え', question_text) or re.search(r'を.*教え', question_text):
                intent_scores['specific_subsidy'] += 10
        
        # 最高スコアの意図を返す
        if intent_scores:
            primary_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x])
            
            # スコアが0の場合はデフォルト処理
            if intent_scores[primary_intent] == 0:
                if has_specific_subsidy:
                    primary_intent = 'specific_subsidy'
                else:
                    primary_intent = 'overview'
            
            confidence = intent_scores[primary_intent] / max(sum(intent_scores.values()), 1)
            
            # 複数の意図が混在している場合
            secondary_intents = [k for k, v in intent_scores.items() 
                               if v > 0 and k != primary_intent]
            
            return {
                'primary': primary_intent,
                'secondary': secondary_intents,
                'confidence': confidence,
                'scores': intent_scores
            }
        
        return {'primary': 'overview', 'secondary': [], 'confidence': 0.5, 'scores': {}}
    
    def _identify_target_subsidy(self, question_text):
        """対象補助金を特定"""
        question_lower = question_text.lower()
        
        # デバッグ用出力
        print(f"Debug: 質問テキスト = '{question_text}'")
        print(f"Debug: 小文字変換 = '{question_lower}'")
        
        for subsidy in self.subsidies:
            # 正式名称でのマッチ（より柔軟に）
            subsidy_name_lower = subsidy.name.lower()
            if subsidy_name_lower in question_lower:
                print(f"Debug: 正式名称マッチ = {subsidy.name}")
                return subsidy
            
            # 部分マッチも試行
            if 'it導入' in subsidy_name_lower and ('it導入' in question_lower or 'ＩＴ導入' in question_lower):
                print(f"Debug: IT導入マッチ = {subsidy.name}")
                return subsidy
            
            # 同義語・略語でのマッチ
            if subsidy.name in self.subsidy_aliases:
                for alias in self.subsidy_aliases[subsidy.name]:
                    if alias.lower() in question_lower:
                        print(f"Debug: 同義語マッチ '{alias}' = {subsidy.name}")
                        return subsidy
        
        # パターンマッチングによる推定
        if re.search(r'it|ＩＴ|デジタル|システム|ソフト', question_text):
            it_subsidy = next((s for s in self.subsidies if 'IT導入' in s.name), None)
            if it_subsidy:
                print(f"Debug: パターンマッチ IT = {it_subsidy.name}")
                return it_subsidy
        elif re.search(r'再構築|転換|新分野|コロナ', question_text):
            recon_subsidy = next((s for s in self.subsidies if '事業再構築' in s.name), None)
            if recon_subsidy:
                print(f"Debug: パターンマッチ 再構築 = {recon_subsidy.name}")
                return recon_subsidy
        elif re.search(r'ものづくり|製造|設備|機械', question_text):
            mono_subsidy = next((s for s in self.subsidies if 'ものづくり' in s.name), None)
            if mono_subsidy:
                print(f"Debug: パターンマッチ ものづくり = {mono_subsidy.name}")
                return mono_subsidy
        elif re.search(r'小規模|持続化|販路', question_text):
            small_subsidy = next((s for s in self.subsidies if '持続化' in s.name), None)
            if small_subsidy:
                print(f"Debug: パターンマッチ 持続化 = {small_subsidy.name}")
                return small_subsidy
        
        print(f"Debug: マッチなし")
        return None
    
    def _analyze_tone(self, question_text):
        """感情・丁寧度を分析"""
        tones = []
        
        for tone_type, patterns in self.tone_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_text):
                    tones.append(tone_type)
                    break
        
        # デフォルトの丁寧度判定
        if not tones:
            if any(char in question_text for char in ['です', 'ます', 'ください', 'いただけ']):
                tones.append('polite')
            else:
                tones.append('casual')
        
        return tones
    
    def _extract_business_info(self, question_text, user_context):
        """ビジネス情報を抽出"""
        extracted_info = {}
        
        # 既存のユーザーコンテキスト
        if user_context:
            extracted_info.update(user_context)
        
        # 質問文からの情報抽出
        business_patterns = {
            '製造業': [r'製造業', r'工場', r'生産', r'製品.*作'],
            'IT・情報通信業': [r'IT企業', r'システム.*開発', r'ソフトウェア.*会社', r'プログラマ'],
            'サービス業': [r'サービス業', r'コンサル', r'接客', r'サービス.*提供'],
            '小売業': [r'小売', r'店舗', r'販売店', r'ショップ'],
            '建設業': [r'建設', r'工事', r'建築', r'土木'],
            '農業': [r'農業', r'農家', r'農園', r'栽培']
        }
        
        for business_type, patterns in business_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_text):
                    extracted_info['business_type'] = business_type
                    break
        
        # 企業規模の推定
        size_patterns = {
            '小規模事業者': [r'小規模', r'個人事業', r'従業員.*少', r'人数.*少'],
            '中小企業': [r'中小企業', r'従業員.*\d+.*人', r'社員.*\d+'],
            '大企業': [r'大企業', r'上場', r'大手']
        }
        
        for size, patterns in size_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_text):
                    extracted_info['company_size'] = size
                    break
        
        return extracted_info
    
    def _generate_contextual_response(self, question_text, intent, target_subsidy, 
                                    tone, business_info, user_context):
        """文脈に応じた回答を生成"""
        
        # 丁寧度に応じた言葉遣いの調整
        is_polite = 'polite' in tone
        is_urgent = 'urgent' in tone
        is_confused = 'confused' in tone
        
        # 意図別の回答生成
        primary_intent = intent['primary']
        
        if primary_intent == 'overview':
            return self._generate_overview_response(is_polite, business_info)
        elif primary_intent == 'specific_subsidy' and target_subsidy:
            return self._generate_specific_subsidy_response(
                target_subsidy, is_polite, is_urgent, business_info
            )
        elif primary_intent == 'application_process':
            return self._generate_application_process_response(
                target_subsidy, is_polite, is_urgent
            )
        elif primary_intent == 'requirements':
            return self._generate_requirements_response(
                target_subsidy, is_polite, business_info
            )
        elif primary_intent == 'strategy':
            return self._generate_strategy_response(
                target_subsidy, is_polite, business_info
            )
        elif primary_intent == 'amount_rate':
            return self._generate_amount_response(target_subsidy, is_polite)
        elif primary_intent == 'timeline':
            return self._generate_timeline_response(target_subsidy, is_polite, is_urgent)
        elif primary_intent == 'business_specific':
            return self._generate_business_specific_response(
                business_info, is_polite
            )
        else:
            # 複合的な質問の場合はDify APIを使用
            return self._generate_dify_response(question_text, user_context, intent, target_subsidy)
    
    def _generate_overview_response(self, is_polite, business_info):
        """概要回答の生成"""
        greeting = "補助金制度についてご説明いたします。" if is_polite else "補助金について説明するね！"
        
        business_hint = ""
        if business_info.get('business_type'):
            business_hint = f"\n\n{business_info['business_type']}でしたら、特に以下の補助金がおすすめです："
        
        response = f"""## 💰 {greeting}

補助金は、国や地方自治体が企業の成長を支援するために提供する**返済不要**の資金です。

## 🏢 主な補助金の種類

### **IT導入補助金**
- ITツール導入で生産性向上
- 最大450万円（補助率1/2）

### **事業再構築補助金**  
- 新分野展開・事業転換
- 最大1,500万円（補助率2/3）

### **ものづくり補助金**
- 革新的な設備投資
- 最大1,250万円（補助率1/2）

### **小規模事業者持続化補助金**
- 販路開拓・生産性向上
- 最大200万円（補助率2/3）

{business_hint}

## 📋 基本的な流れ
1. 補助金の選択
2. 要件確認
3. 事業計画作成
4. 申請書提出
5. 審査・採択
6. 事業実施

{self._get_next_action_suggestion(is_polite)}"""

        return {
            'answer': response,
            'recommended_subsidies': list(self.subsidies[:3]),
            'confidence_score': 0.8,
            'model_used': 'nlp-overview'
        }
    
    def _generate_specific_subsidy_response(self, subsidy, is_polite, is_urgent, business_info):
        """特定補助金の詳細回答"""
        urgency_note = "\n\n⚡ **お急ぎの場合**: まずは申請期限をご確認ください。" if is_urgent else ""
        
        business_advice = ""
        if business_info.get('business_type'):
            business_advice = self._get_business_specific_advice(subsidy, business_info['business_type'])
        
        response = f"""## 📋 {subsidy.name} について詳しくご説明します

### 🎯 概要
{subsidy.description}

### 👥 対象事業者
{subsidy.target_business}

### 💰 補助金額・補助率
- **最大補助額**: {subsidy.max_amount:,}円
- **補助率**: {subsidy.subsidy_rate}

### 📅 申請期間
{subsidy.application_period}

### ✅ 主な要件
{subsidy.requirements}

{business_advice}

## 📝 申請の流れ

### **準備段階（2-3ヶ月前）**
1. 申請要件の詳細確認
2. 事業計画の検討
3. 必要書類の準備開始

### **申請段階（1ヶ月前）**
1. 事業計画書作成
2. 見積書取得
3. 申請書類完成

### **提出段階**
1. 最終チェック
2. 電子申請
3. 受付確認

{urgency_note}

{self._get_next_action_suggestion(is_polite)}"""

        return {
            'answer': response,
            'recommended_subsidies': [subsidy],
            'confidence_score': 0.9,
            'model_used': 'nlp-specific'
        }
    
    def _generate_strategy_response(self, target_subsidy, is_polite, business_info):
        """戦略的回答の生成"""
        
        subsidy_name = target_subsidy.name if target_subsidy else "補助金"
        business_type = business_info.get('business_type', '')
        
        response = f"""## 🎯 {subsidy_name} の採択率を最大化する戦略

## 📊 現在の競争状況
- 申請件数は年々増加傾向
- **戦略的アプローチ**により採択確率を大幅向上可能
- 適切な準備により成功確率60-80%を目指せます

## 🛡️ 勝利のための3大戦略

### **戦略① 早期申請による優位性確保**
- 公募開始から2週間以内の申請
- 審査員の集中力が高い時期を狙う
- **効果**: 採択率+15%向上

### **戦略② 差別化による独自性アピール**
{self._get_differentiation_strategy(business_type)}
- **効果**: 印象度大幅アップ

### **戦略③ 数値化による説得力強化**
- 「売上30%向上」など具体的目標設定
- ROI（投資対効果）の明確化
- **効果**: 審査員の納得度向上

## ⏰ 最適申請タイミング
- **推奨期間**: 次回公募開始直後
- **準備開始**: 今すぐ（3ヶ月集中プログラム）
- **成功確率**: 戦略実装により70-85%

## 🚀 今すぐ始める5つのアクション

1. ✅ **競合分析**: 同業他社の申請動向調査
2. ✅ **専門家選定**: 採択実績豊富な支援機関との連携
3. ✅ **強みの明確化**: 自社の独自性・優位性の整理
4. ✅ **数値目標設定**: 具体的で実現可能な改善指標
5. ✅ **スケジュール策定**: 逆算による準備計画

## 💡 成功事例から学ぶポイント
- **準備期間**: 平均3ヶ月の入念な準備
- **支援機関活用率**: 採択者の80%が専門家と連携
- **申請タイミング**: 早期申請者の採択率が15%高い

{self._get_next_action_suggestion(is_polite)}"""

        return {
            'answer': response,
            'recommended_subsidies': [target_subsidy] if target_subsidy else [],
            'confidence_score': 0.95,
            'model_used': 'nlp-strategy'
        }
    
    def _get_differentiation_strategy(self, business_type):
        """業種別差別化戦略"""
        strategies = {
            'IT・情報通信業': "- 既存システムとの連携効果を強調\n- セキュリティ対策の充実をアピール\n- 顧客価値向上の具体的効果を数値化",
            '製造業': "- 生産効率向上の具体的数値を提示\n- 品質向上・安全性向上効果を強調\n- 受注拡大への具体的道筋を説明",
            '小売業': "- 顧客体験向上の具体策を提示\n- オムニチャネル戦略への貢献\n- 地域密着性と革新性の両立",
            'サービス業': "- サービス品質向上の測定指標\n- 業務効率化による顧客満足度向上\n- 新サービス創出の可能性"
        }
        return strategies.get(business_type, "- 業界特有の課題解決を明確化\n- 独自の強み・ノウハウを活用\n- 競合他社との明確な差別化")
    
    def _get_next_action_suggestion(self, is_polite):
        """次のアクション提案"""
        if is_polite:
            return """
## 📞 次のステップ

より詳細なご相談や具体的な申請支援が必要でしたら、お気軽にお声がけください。
お客様の事業発展のお手伝いをさせていただきます。

---
*最新の申請要領は必ず公式サイトでご確認ください。*"""
        else:
            return """
## 🚀 次にやること

もっと詳しいことが聞きたかったら、いつでも質問してね！
一緒に最適な補助金活用を考えよう。"""
    
    def _get_business_specific_advice(self, subsidy, business_type):
        """業種特有のアドバイス（既存のロジック）"""
        if not business_type:
            return ""
        
        advice_map = {
            'IT・情報通信業': f"""
## 💻 {business_type}での活用ポイント

- **既存システムとの連携**を明確に説明
- **セキュリティ対策**の実施状況をアピール  
- **顧客への価値提供**の向上効果を数値化
- **業界特有の課題解決**を具体的に記載""",
            
            '製造業': f"""
## 🏭 {business_type}での活用ポイント

- **生産性向上効果**を具体的な数値で示す
- **品質向上**や**コスト削減**効果を明記
- **安全性向上**への貢献をアピール
- **受注拡大**の可能性を具体的に説明"""
        }
        
        return advice_map.get(business_type, f"""
## 🏢 {business_type}での活用ポイント

- **業界特有の課題**を明確に特定
- **既存事業との相乗効果**を具体的に説明
- **競合他社との差別化**を明確にアピール""")
    
    def _generate_dify_response(self, question_text, user_context, intent, target_subsidy):
        """Dify APIによる複合的質問への回答"""
        if not self.dify_api_key:
            return self._generate_specific_subsidy_response(
                target_subsidy or self.subsidies[0], True, False, 
                user_context or {}
            )
        
        try:
            query = self._build_contextual_dify_query(
                question_text, user_context, intent, target_subsidy
            )
            dify_response = self._call_dify_api(query)
            
            if dify_response and 'answer' in dify_response:
                return {
                    'answer': dify_response['answer'],
                    'recommended_subsidies': [target_subsidy] if target_subsidy else [],
                    'confidence_score': 0.85,
                    'model_used': 'nlp-dify'
                }
        except Exception as e:
            print(f"Dify API error: {e}")
        
        # フォールバック
        return self._generate_specific_subsidy_response(
            target_subsidy or self.subsidies[0], True, False, user_context or {}
        )
    
    def _build_contextual_dify_query(self, question, user_context, intent, target_subsidy):
        """文脈を考慮したDifyクエリ構築"""
        
        context_info = ""
        if user_context:
            context_info = f"""
【相談者情報】
- 事業種別: {user_context.get('business_type', '未設定')}
- 企業規模: {user_context.get('company_size', '未設定')}"""
        
        intent_info = f"""
【質問の意図分析】
- 主要意図: {intent['primary']}
- 信頼度: {intent['confidence']:.2f}"""
        
        subsidy_info = ""
        if target_subsidy:
            subsidy_info = f"""
【対象補助金】
{target_subsidy.name}: {target_subsidy.description}"""
        
        return f"""あなたは補助金の専門コンサルタントです。以下の情報を基に、相談者に寄り添った実用的な回答をしてください。

{context_info}

{intent_info}

{subsidy_info}

【質問】
{question}

【回答指針】
1. 質問の意図を正確に理解し、直接的に回答する
2. 専門用語は分かりやすく説明する
3. 具体的で実行可能なアドバイスを提供する
4. 相談者の立場に立った温かい文体で
5. 必要に応じて次のステップを明示する

日本語で、親身になって回答してください。"""
    
    def _call_dify_api(self, query_text):
        """Dify API呼び出し"""
        try:
            request_data = {
                "inputs": {},
                "query": query_text,
                "response_mode": "blocking",
                "user": f"nlp_user_{hash(query_text) % 10000}"
            }
            
            url = f"{self.dify_api_url}/chat-messages"
            
            response = requests.post(
                url,
                headers=self.headers,
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Dify API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Dify API error: {e}")
            return None
    
    # 他の必要なメソッド（amount_response, timeline_response等）は既存のロジックを使用
    def _generate_application_process_response(self, target_subsidy, is_polite, is_urgent):
        """申請プロセス回答"""
        subsidy = target_subsidy or self.subsidies[0]
        urgency = "⚡ 急ぎの場合は、まず申請期限をご確認ください。\n\n" if is_urgent else ""
        
        response = f"""{urgency}## 📝 {subsidy.name} の申請手順

### **STEP 1: 事前準備（申請2-3ヶ月前）**
1. **要件確認**: 詳細な申請要件をチェック
2. **書類準備**: 必要書類のリストアップと収集開始
3. **計画検討**: 事業計画の骨子作成

### **STEP 2: 申請書作成（申請1ヶ月前）**
1. **事業計画書**: 具体的で実現可能な計画を作成
2. **見積書取得**: 複数社から詳細見積もりを取得
3. **証憑書類**: 決算書、税務申告書等を整理

### **STEP 3: 申請提出**
1. **最終確認**: 申請書類の完全性をチェック
2. **電子申請**: 指定システムから提出
3. **受付確認**: 提出完了の確認

## 📄 必要書類チェックリスト
- ✅ 申請書（事業計画書含む）
- ✅ 直近2期分の決算書
- ✅ 税務申告書の写し
- ✅ 見積書（詳細仕様書付き）
- ✅ 会社概要・パンフレット

{self._get_next_action_suggestion(is_polite)}"""
        
        return {
            'answer': response,
            'recommended_subsidies': [subsidy],
            'confidence_score': 0.9,
            'model_used': 'nlp-process'
        }


# 新しいNLP対応AIサービス
AIAdvisorService = NLPAIAdvisorService