# advisor/services/nlp_ai_advisor.py - 認識精度向上版

import requests
import json
import re
from django.conf import settings
from ..models import SubsidyType, Answer, ConversationHistory

class NLPAIAdvisorService:
    """自然言語処理対応の高度なAIアドバイザー（認識精度向上版）"""
    
    def __init__(self):
        self.dify_api_url = getattr(settings, 'DIFY_API_URL', '')
        self.dify_api_key = getattr(settings, 'DIFY_API_KEY', '')
        self.headers = {
            'Authorization': f'Bearer {self.dify_api_key}',
            'Content-Type': 'application/json'
        }
        
        # 補助金データを事前読み込み
        self.subsidies = list(SubsidyType.objects.all())
        self._initialize_nlp_patterns()
    
    def _initialize_nlp_patterns(self):
        """自然言語パターンを初期化"""
        
        # 完全版補助金エイリアス辞書（現在の全補助金に対応）
        self.subsidy_aliases = {
            'IT導入補助金': [
                'it導入', 'ＩＴ導入', 'アイティー導入', 'ITツール', 'デジタル化補助',
                'it導入補助金', 'IT導入補助金', 'ITシステム', 'ソフトウェア補助',
                'デジタル補助', 'システム導入', 'デジタル化支援', 'デジタル化',
                'システム化', 'IT化', 'デジタル変革', 'dx'
            ],
            'IT導入補助金2025': [
                'it導入', 'ＩＴ導入', 'アイティー導入', 'ITツール', 'デジタル化補助',
                'it導入補助金', 'IT導入補助金', 'ITシステム', 'ソフトウェア補助',
                'デジタル補助', 'システム導入', 'デジタル化支援', 'デジタル化',
                'システム化', 'IT化', 'デジタル変革', 'dx', 'it導入2025'
            ],
            'ものづくり補助金': [
                'ものづくり', '製造補助', '設備投資', '生産性向上', 'ものづくり補助金',
                '革新的サービス', '試作品開発', '生産プロセス改善', '設備更新',
                '製造業補助', '機械設備', '製造', '工場', '生産'
            ],
            '小規模事業者持続化補助金【一般型】': [
                '持続化', '小規模持続', '販路開拓', '小規模事業者', '持続化補助金',
                '持続化一般', '一般型持続化', '販路拡大', '認知度向上',
                '小規模補助', '販促支援', '小規模事業者持続化補助金',
                '販路', '販売促進', '営業支援'
            ],
            '小規模事業者持続化補助金【創業型】': [
                '持続化創業', '創業型持続化', '創業補助', '新規開業', '起業支援',
                '創業5年', 'スタートアップ支援', '創業期補助', '創業支援',
                '起業補助', '小規模事業者持続化補助金創業型', '創業',
                '起業', 'スタートアップ', '新規事業'
            ],
            '省力化投資補助金': [
                '省力化', '省力化投資', '人手不足解消', '自動化', '効率化投資',
                'IoT補助', 'AI導入', 'ロボット導入', '省人化', '労働力不足',
                '人材不足対策', '自動化設備', '省力化投資補助金',
                '人手不足', '自動化システム', 'iot', 'ai', 'ロボット'
            ],
            '事業承継・M&A補助金': [
                '事業承継', '承継補助', '引継ぎ', '後継者', '事業承継補助金',
                'M&A補助', '買収補助', '経営承継', '世代交代', '事業引継ぎ',
                'ma補助', 'エムアンドエー', '事業承継・M&A補助金',
                '承継', '後継', 'ma', 'm&a'
            ],
            '新事業進出補助金': [
                '新事業', '新分野進出', '事業拡大', '多角化', '新商品開発',
                '新サービス', '市場開拓', '事業転換', '新規事業',
                '分野拡大', '新事業進出補助金', '新分野', '多角化'
            ],
            '成長加速化補助金': [
                '成長加速', '成長促進', '事業拡大', 'スケールアップ', '競争力強化',
                'グローバル展開', '海外進出', '人材育成補助', '成長支援',
                '拡大支援', '成長加速化補助金', '成長', '拡大', 'グローバル'
            ],
            '省エネ診断・省エネ・非化石転換補助金': [
                '省エネ', '省エネルギー', '非化石', 'カーボンニュートラル', '脱炭素',
                '再生可能エネルギー', 'CO2削減', '環境対応', 'グリーン化',
                '省エネ設備', '環境補助', '省エネ診断', '環境',
                'カーボン', '脱炭素化', 'co2'
            ],
            '雇用調整助成金': [
                '雇用調整', '雇調金', '休業補償', '雇用維持', '労働者支援',
                '一時休業', '事業縮小', '雇用安定', '雇用助成',
                '休業手当', '雇用調整助成金', '休業', '雇用'
            ],
            '業務改善助成金': [
                '業務改善', '賃金引上げ', '最低賃金', '生産性向上', '働き方改革',
                '労働環境改善', '設備改善', '職場改善', '賃上げ',
                '労働条件改善', '業務改善助成金', '賃金', '最低賃金'
            ],
            '創業助成金': [
                '創業', '起業', 'スタートアップ', '新規開業', '開業支援',
                '創業支援', '起業助成', '新規事業', '開業助成', '創業助成金'
            ],
            '事業再構築補助金': [
                '再構築', '事業転換', '新分野展開', '業態転換', '事業再構築補助金',
                'V字回復', '事業変革', '構造改革', 'ピボット', '転換'
            ],
            '事業承継・引継ぎ補助金': [
                '事業承継', '承継補助', '引継ぎ補助金', '後継者支援'
            ],
            '小規模事業者持続化補助金': [
                '持続化', '小規模事業者補助'
            ]
        }
        
        # 質問の意図分類パターン
        self.intent_patterns = {
            'overview': {
                'patterns': [
                    r'補助金.*とは', r'補助金.*について.*教え', r'補助金.*仕組み',
                    r'どんな.*補助金', r'補助金.*種類', r'補助金.*概要',
                    r'補助金.*全般', r'補助金.*基本', r'補助金.*説明'
                ],
                'keywords': ['とは', '教えて', '説明', '仕組み', '種類', '概要', '全般', '基本']
            },
            'specific_subsidy': {
                'patterns': [],  # 動的に生成
                'keywords': []   # 動的に生成
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
                    r'コツ.*教え', r'秘訣.*教え', r'戦略.*教え'
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
            }
        }
        
        # specific_subsidy の動的パターン生成
        self._generate_dynamic_patterns()
        
        # 感情・丁寧度の分析
        self.tone_patterns = {
            'polite': [r'いただけ', r'お聞かせ', r'お教え', r'恐れ入り', r'申し訳', r'よろしく'],
            'casual': [r'教えて', r'どう', r'なに', r'どこ', r'いくら'],
            'urgent': [r'急い', r'至急', r'すぐ', r'早く', r'間に合わ'],
            'confused': [r'分から', r'よく.*理解', r'難し', r'複雑', r'混乱']
        }

    def _generate_dynamic_patterns(self):
        """エイリアス辞書から動的にパターンを生成"""
        patterns = []
        keywords = []
        
        for subsidy_name, aliases in self.subsidy_aliases.items():
            # 正式名称をパターンに追加
            escaped_name = re.escape(subsidy_name)
            patterns.append(escaped_name)
            
            # キーワードとして主要部分を抽出
            main_keywords = subsidy_name.replace('補助金', '').replace('助成金', '').split('・')
            keywords.extend([kw.strip() for kw in main_keywords if kw.strip()])
            
            # エイリアスもキーワードに追加
            keywords.extend(aliases)
        
        self.intent_patterns['specific_subsidy']['patterns'] = patterns
        self.intent_patterns['specific_subsidy']['keywords'] = list(set(keywords))

    def analyze_question(self, question_text, user_context=None):
        """自然言語解析による質問分析（完全版エイリアス対応）"""
        
        # Step 1: 質問の意図を分析
        intent = self._analyze_intent(question_text)
        
        # Step 2: 対象補助金を特定（拡張エイリアス使用）
        target_subsidy = self._identify_target_subsidy_enhanced(question_text)
        
        # Step 3: 感情・丁寧度を分析
        tone = self._analyze_tone(question_text)
        
        # Step 4: ビジネス情報を抽出
        business_info = self._extract_business_info(question_text, user_context)
        
        # Step 5: 回答を生成
        response = self._generate_contextual_response(
            question_text, intent, target_subsidy, tone, business_info, user_context
        )
        
        return response

    def _identify_target_subsidy_enhanced(self, question_text):
        """拡張エイリアスを使用した補助金特定（改良版）"""
        question_lower = question_text.lower()
        
        # 正規化処理（全角→半角、記号除去など）
        normalized_question = self._normalize_text(question_lower)
        
        # Step 1: 正式名称での完全一致
        for subsidy in self.subsidies:
            subsidy_normalized = self._normalize_text(subsidy.name.lower())
            if subsidy_normalized in normalized_question:
                return subsidy
        
        # Step 2: エイリアス辞書を使用した特定（スコアベース）
        subsidy_scores = {}
        
        for subsidy_name, aliases in self.subsidy_aliases.items():
            score = 0
            
            # 正式名称での部分マッチ
            main_parts = subsidy_name.replace('補助金', '').replace('助成金', '').split('・')
            for part in main_parts:
                if part and self._normalize_text(part.lower()) in normalized_question:
                    score += 5
            
            # エイリアスでのマッチ
            for alias in aliases:
                alias_normalized = self._normalize_text(alias.lower())
                if alias_normalized in normalized_question:
                    # エイリアスの長さに応じてスコア調整（長いほど高スコア）
                    score += max(1, len(alias_normalized) // 2)
            
            if score > 0:
                subsidy_scores[subsidy_name] = score
        
        # 最高スコアの補助金を返す
        if subsidy_scores:
            best_match = max(subsidy_scores.keys(), key=lambda x: subsidy_scores[x])
            try:
                return SubsidyType.objects.get(name=best_match)
            except SubsidyType.DoesNotExist:
                pass
        
        # Step 3: パターンマッチングによる推定（フォールバック）
        return self._pattern_based_identification(question_text)

    def _normalize_text(self, text):
        """テキスト正規化（全角→半角、記号除去など）"""
        # 全角英数字を半角に変換
        text = text.translate(str.maketrans(
            'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ'
            'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ'
            '０１２３４５６７８９',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            'abcdefghijklmnopqrstuvwxyz'
            '0123456789'
        ))
        
        # 記号・空白を除去
        text = re.sub(r'[^\w]', '', text)
        
        return text

    def _pattern_based_identification(self, question_text):
        """パターンベースの補助金特定（フォールバック）"""
        question_lower = question_text.lower()
        normalized_question = self._normalize_text(question_lower)
        
        # パターンマッチングルール（優先度順）
        patterns = [
            # IT・デジタル関連
            (r'it|ＩＴ|デジタル|システム|ソフト|dx', ['IT導入補助金', 'IT導入補助金2025']),
            
            # 省力化・自動化関連
            (r'省力化|人手不足|自動化|ai|iot|ロボット|省人化|労働力不足', ['省力化投資補助金']),
            
            # ものづくり・製造関連
            (r'ものづくり|製造|設備投資|機械|工場|生産', ['ものづくり補助金']),
            
            # 小規模事業者関連
            (r'小規模.*持続化|販路開拓|小規模事業者', ['小規模事業者持続化補助金【一般型】']),
            
            # 創業関連
            (r'創業|起業|スタートアップ|新規開業', ['小規模事業者持続化補助金【創業型】', '創業助成金']),
            
            # 事業承継関連
            (r'事業承継|承継|後継者|m&a|ma|買収', ['事業承継・M&A補助金', '事業承継・引継ぎ補助金']),
            
            # 新事業関連
            (r'新事業|新分野|多角化|事業拡大', ['新事業進出補助金']),
            
            # 成長・拡大関連
            (r'成長|拡大|グローバル|海外進出', ['成長加速化補助金']),
            
            # 環境・省エネ関連
            (r'省エネ|環境|脱炭素|カーボン|co2', ['省エネ診断・省エネ・非化石転換補助金']),
            
            # 雇用関連
            (r'雇用調整|雇調金|休業|雇用維持', ['雇用調整助成金']),
            
            # 業務改善関連
            (r'業務改善|賃金|最低賃金|働き方改革', ['業務改善助成金']),
            
            # 事業再構築関連
            (r'再構築|転換|ピボット|業態転換', ['事業再構築補助金'])
        ]
        
        for pattern, candidate_names in patterns:
            if re.search(pattern, normalized_question):
                # 候補の中からデータベースに存在するものを返す
                for name in candidate_names:
                    try:
                        return SubsidyType.objects.get(name=name)
                    except SubsidyType.DoesNotExist:
                        continue
        
        return None

    def _analyze_intent(self, question_text):
        """質問の意図を分析"""
        question_lower = question_text.lower()
        intent_scores = {}
        
        # 補助金が特定されているかチェック
        has_specific_subsidy = self._identify_target_subsidy_enhanced(question_text) is not None
        
        for intent_type, config in self.intent_patterns.items():
            score = 0
            
            # パターンマッチング
            for pattern in config['patterns']:
                if re.search(pattern, question_text):
                    score += 3
            
            # キーワードマッチング
            for keyword in config['keywords']:
                if keyword.lower() in question_lower:
                    score += 1
            
            intent_scores[intent_type] = score
        
        # 特定の補助金が識別された場合の重み調整
        if has_specific_subsidy:
            intent_scores['specific_subsidy'] += 5
            
            if re.search(r'について.*教え|を.*教え|の.*詳細|詳しく', question_text):
                intent_scores['specific_subsidy'] += 10
        
        # 最高スコアの意図を返す
        if intent_scores:
            primary_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x])
            
            if intent_scores[primary_intent] == 0:
                primary_intent = 'specific_subsidy' if has_specific_subsidy else 'overview'
            
            confidence = intent_scores[primary_intent] / max(sum(intent_scores.values()), 1)
            secondary_intents = [k for k, v in intent_scores.items() 
                               if v > 0 and k != primary_intent]
            
            return {
                'primary': primary_intent,
                'secondary': secondary_intents,
                'confidence': confidence,
                'scores': intent_scores
            }
        
        return {'primary': 'overview', 'secondary': [], 'confidence': 0.5, 'scores': {}}

    def _analyze_tone(self, question_text):
        """感情・丁寧度を分析"""
        tone_scores = {}
        
        for tone_type, patterns in self.tone_patterns.items():
            score = sum(1 for pattern in patterns if re.search(pattern, question_text))
            if score > 0:
                tone_scores[tone_type] = score
        
        primary_tone = max(tone_scores.keys(), key=lambda x: tone_scores[x]) if tone_scores else 'neutral'
        
        return {
            'primary': primary_tone,
            'is_polite': 'polite' in tone_scores,
            'is_urgent': 'urgent' in tone_scores,
            'is_confused': 'confused' in tone_scores,
            'scores': tone_scores
        }

    def _extract_business_info(self, question_text, user_context):
        """ビジネス情報を抽出"""
        business_info = {}
        question_lower = question_text.lower()
        
        # 業種の特定
        industry_keywords = {
            '製造業': ['製造', '工場', '生産', 'メーカー', '機械'],
            'IT・情報通信業': ['it', 'システム', 'ソフト', 'web', 'アプリ'],
            'サービス業': ['サービス', 'コンサル', '士業'],
            '小売業': ['小売', '販売', '店舗', 'ec'],
            '建設業': ['建設', '工事', '施工'],
            '飲食業': ['飲食', 'レストラン', 'カフェ']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                business_info['business_type'] = industry
                break
        
        return business_info

    def _generate_contextual_response(self, question_text, intent, target_subsidy, tone, business_info, user_context):
        """文脈に応じた回答生成"""
        
        is_polite = tone['is_polite']
        is_urgent = tone['is_urgent']
        primary_intent = intent['primary']
        
        if primary_intent == 'specific_subsidy' and target_subsidy:
            return self._generate_specific_subsidy_response(target_subsidy, is_polite, is_urgent, business_info)
        elif primary_intent == 'overview':
            return self._generate_overview_response(is_polite, business_info)
        elif primary_intent == 'strategy':
            return self._generate_strategy_response(target_subsidy, is_polite, business_info)
        else:
            return self._generate_general_response(question_text, intent, is_polite, business_info)

    def _generate_specific_subsidy_response(self, subsidy, is_polite, is_urgent, business_info):
        """特定補助金の詳細回答"""
        greeting = "恐れ入ります。" if is_polite else ""
        urgency_note = "\n\n⚡ **お急ぎの場合**: まずは申請期限をご確認ください。" if is_urgent else ""
        
        response = f"""{greeting}

## 📋 {subsidy.name} について詳しくご説明します

### 🎯 概要
{subsidy.description}

### 💰 補助金額
- **最大補助額**: {subsidy.max_amount}万円

### 👥 対象事業者
{subsidy.target_business_type}

### ✅ 主な申請要件
{subsidy.requirements}

### 📅 準備期間の目安
- **平均準備期間**: {subsidy.average_preparation_weeks}週
- **申請難易度**: {'⭐' * subsidy.application_difficulty}
- **過去の採択率**: {int(subsidy.historical_success_rate * 100)}%

## 📝 申請の流れ

### **STEP 1: 事前準備（2-3ヶ月前）**
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

{urgency_note}

ご不明な点がございましたら、いつでもお気軽にご相談ください！"""

        return {
            'answer': response,
            'recommended_subsidies': [subsidy],
            'confidence_score': 0.95,
            'model_used': 'nlp-enhanced'
        }

    def _generate_overview_response(self, is_polite, business_info):
        """概要回答の生成"""
        greeting = "ご質問ありがとうございます。" if is_polite else ""
        
        response = f"""{greeting}

## 🎯 補助金制度について総合的にご説明します

### 💡 主要な補助金の種類

#### **🖥️ デジタル化支援**
- **IT導入補助金**: ITツール導入による効率化
- **省力化投資補助金**: AI・IoT・ロボット導入支援

#### **🏭 事業強化支援**
- **ものづくり補助金**: 設備投資・革新的サービス開発
- **事業再構築補助金**: 新分野展開・業態転換

#### **🏢 小規模事業者支援**
- **持続化補助金（一般型）**: 販路開拓・認知度向上
- **持続化補助金（創業型）**: 創業期の事業拡大支援

#### **⚡ その他の重要制度**
- **雇用調整助成金**: 雇用維持支援
- **業務改善助成金**: 賃金向上・働き方改革
- **事業承継・M&A補助金**: 事業承継支援

### 🎯 選択のポイント

1. **事業規模**: 小規模事業者 vs 中小企業
2. **目的**: デジタル化 vs 事業拡大 vs 承継・転換
3. **投資規模**: 50万円～1,000万円以上
4. **準備期間**: 4週～14週

### 📋 基本的な申請の流れ

1. **補助金の選択**
2. **要件確認**
3. **事業計画作成**
4. **申請書提出**
5. **審査・採択**
6. **事業実施**

どの補助金が最適か、具体的にご相談いただけましたら詳しくアドバイスいたします！"""

        return {
            'answer': response,
            'recommended_subsidies': list(self.subsidies[:3]),
            'confidence_score': 0.8,
            'model_used': 'nlp-overview'
        }

    def _generate_strategy_response(self, target_subsidy, is_polite, business_info):
        """戦略的回答の生成"""
        subsidy_name = target_subsidy.name if target_subsidy else "補助金"
        
        response = f"""## 🎯 {subsidy_name} 採択戦略

### 📊 成功のための3つの戦略

#### **戦略① 早期申請による優位性確保**
- 公募開始から2週間以内の申請を目指す
- 審査員の集中力が高い時期を活用
- **効果**: 採択率+15%向上

#### **戦略② 差別化による独自性アピール**
- 競合他社にない独自の強みを明確化
- 具体的な成果指標と根拠を提示
- **効果**: 印象度大幅アップ

#### **戦略③ 数値化による説得力強化**
- 「売上30%向上」など具体的目標設定
- ROI（投資対効果）の明確化
- **効果**: 審査員の納得度向上

### 🚀 今すぐ始める5つのアクション

1. ✅ **競合分析**: 同業他社の申請動向調査
2. ✅ **専門家選定**: 採択実績豊富な支援機関との連携
3. ✅ **強みの明確化**: 自社の独自性・優位性の整理
4. ✅ **数値目標設定**: 具体的で実現可能な改善指標
5. ✅ **リスク対策**: 申請失敗時のプランB策定

戦略的に進めることで、採択確率を大幅に向上させることができます！"""

        return {
            'answer': response,
            'recommended_subsidies': [target_subsidy] if target_subsidy else [],
            'confidence_score': 0.9,
            'model_used': 'nlp-strategy'
        }

    def _generate_general_response(self, question_text, intent, is_polite, business_info):
        """一般的な回答の生成"""
        greeting = "お問い合わせありがとうございます。" if is_polite else ""
        
        response = f"""{greeting}

ご質問の内容を拝見し、最適な補助金制度をご提案いたします。

### 🔍 状況に応じた推奨補助金

現在のご状況やニーズに合わせて、以下のような補助金制度がございます：

- **デジタル化をお考えの場合**: IT導入補助金、省力化投資補助金
- **設備投資をご検討の場合**: ものづくり補助金、省力化投資補助金
- **販路拡大をお考えの場合**: 小規模事業者持続化補助金
- **新事業展開をお考えの場合**: 新事業進出補助金、成長加速化補助金

### 💡 次のステップ

より具体的なアドバイスをご提供するため、以下の点を教えていただけませんでしょうか：

1. **業種・事業内容**
2. **解決したい課題**
3. **投資予定額の規模**
4. **実現したい目標**

これらの情報をお聞かせいただければ、最適な補助金と申請戦略をご提案いたします！"""

        return {
            'answer': response,
            'recommended_subsidies': [],
            'confidence_score': 0.7,
            'model_used': 'nlp-general'
        }


# メインサービスとして設定
AIAdvisorService = NLPAIAdvisorService