# advisor/services/detailed_response_service.py

import requests
import json
import re
from datetime import datetime, date
from django.conf import settings
from ..models import SubsidyType, AdoptionStatistics, AdoptionTips

class DetailedResponseService:
    """詳細で自然な回答を生成するAIサービス"""
    
    def __init__(self):
        self.dify_api_url = settings.DIFY_API_URL
        self.dify_api_key = settings.DIFY_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.dify_api_key}',
            'Content-Type': 'application/json'
        }
    
    def analyze_question(self, question_text, user_context=None):
        """質問を分析して詳細な回答を生成"""
        
        # 1. 質問の意図を分析
        intent = self._analyze_intent(question_text)
        
        # 2. 関連する補助金を特定
        relevant_subsidies = self._find_relevant_subsidies(question_text, user_context)
        
        # 3. 詳細データを収集
        detailed_data = self._collect_detailed_data(relevant_subsidies, intent)
        
        # 4. 回答を生成
        if self.dify_api_key:
            answer = self._generate_dify_response(question_text, user_context, detailed_data, intent)
        else:
            answer = self._generate_enhanced_mock_response(question_text, user_context, detailed_data, intent)
        
        # 5. 推奨補助金を決定
        recommended_subsidies = relevant_subsidies[:3] if relevant_subsidies else []
        
        return {
            'answer': answer,
            'recommended_subsidies': recommended_subsidies,
            'confidence_score': self._calculate_confidence(intent, relevant_subsidies, detailed_data),
            'model_used': 'detailed-response-service',
            'intent': intent,
            'data_sources': len(detailed_data)
        }
    
    def _analyze_intent(self, question_text):
        """質問の意図を分析"""
        question_lower = question_text.lower()
        
        # 採択率に関する質問
        if any(keyword in question_lower for keyword in ['採択率', '通る確率', '成功率', '受かる', '採択']):
            return 'adoption_rate'
        
        # 申請方法に関する質問
        if any(keyword in question_lower for keyword in ['申請方法', '申請手順', '申請の仕方', 'やり方', '手続き']):
            return 'application_process'
        
        # 要件・条件に関する質問
        if any(keyword in question_lower for keyword in ['要件', '条件', '資格', '対象', '使える']):
            return 'requirements'
        
        # 金額に関する質問
        if any(keyword in question_lower for keyword in ['金額', '補助額', 'いくら', '最大', '上限']):
            return 'amount'
        
        # 期間・スケジュールに関する質問
        if any(keyword in keyword in question_lower for keyword in ['期間', 'いつ', '締切', '期限', 'スケジュール']):
            return 'schedule'
        
        # 比較に関する質問
        if any(keyword in question_lower for keyword in ['比較', '違い', 'どちら', 'どれ', '選び方']):
            return 'comparison'
        
        # 成功のコツに関する質問
        if any(keyword in question_lower for keyword in ['コツ', '秘訣', '成功', '通るため', 'ポイント']):
            return 'success_tips'
        
        # 一般的な概要
        return 'overview'
    
    def _find_relevant_subsidies(self, question_text, user_context):
        """関連する補助金を特定"""
        subsidies = SubsidyType.objects.all()
        relevant = []
        
        question_lower = question_text.lower()
        business_type = user_context.get('business_type', '') if user_context else ''
        company_size = user_context.get('company_size', '') if user_context else ''
        
        for subsidy in subsidies:
            score = 0
            
            # 名前での直接マッチ
            if subsidy.name.lower().replace('補助金', '').replace('助成金', '') in question_lower:
                score += 100
            
            # キーワードマッチ
            keywords = {
                'it': ['IT', 'デジタル', 'システム', 'ソフト', 'アプリ'],
                'manufacturing': ['ものづくり', '製造', '設備', '機械'],
                'marketing': ['持続化', '販路', 'マーケティング', '宣伝', '広告'],
                'restructuring': ['再構築', '転換', '新分野'],
                'succession': ['承継', '引継ぎ', 'M&A'],
                'startup': ['創業', 'スタートアップ', '起業'],
                'energy': ['省エネ', 'エネルギー', '環境'],
                'workstyle': ['働き方', 'テレワーク', '労働'],
                'support': ['両立', '育児', '介護']
            }
            
            for category, words in keywords.items():
                if any(word in question_lower for word in words):
                    if any(word in subsidy.name or word in subsidy.description for word in words):
                        score += 50
            
            # 業種・企業規模での適合性
            if business_type:
                if business_type in subsidy.target_business:
                    score += 20
            
            if company_size:
                if company_size in subsidy.target_business:
                    score += 15
            
            if score > 0:
                relevant.append((subsidy, score))
        
        # スコア順でソート
        relevant.sort(key=lambda x: x[1], reverse=True)
        return [subsidy for subsidy, score in relevant]
    
    def _collect_detailed_data(self, subsidies, intent):
        """詳細データを収集"""
        data = {}
        
        for subsidy in subsidies[:5]:  # 上位5つまで
            subsidy_data = {
                'basic_info': {
                    'name': subsidy.name,
                    'description': subsidy.description,
                    'target_business': subsidy.target_business,
                    'max_amount': subsidy.max_amount,
                    'subsidy_rate': subsidy.subsidy_rate,
                    'requirements': subsidy.requirements,
                    'application_period': subsidy.application_period
                }
            }
            
            # 採択統計データ
            if intent in ['adoption_rate', 'comparison', 'overview']:
                stats = AdoptionStatistics.objects.filter(
                    subsidy_type=subsidy
                ).order_by('-year', '-round_number')[:3]
                
                if stats:
                    subsidy_data['statistics'] = []
                    for stat in stats:
                        subsidy_data['statistics'].append({
                            'year': stat.year,
                            'round': stat.round_number,
                            'adoption_rate': stat.adoption_rate,
                            'total_applications': stat.total_applications,
                            'total_adoptions': stat.total_adoptions,
                            'small_business_rate': stat.small_business_adoption_rate,
                            'medium_business_rate': stat.medium_business_adoption_rate,
                            'industry_stats': stat.industry_statistics
                        })
            
            # 成功のコツ・ティップス
            if intent in ['success_tips', 'application_process', 'overview']:
                tips = AdoptionTips.objects.filter(
                    subsidy_type=subsidy
                ).order_by('-importance')[:5]
                
                if tips:
                    subsidy_data['tips'] = []
                    for tip in tips:
                        subsidy_data['tips'].append({
                            'category': tip.category,
                            'title': tip.title,
                            'content': tip.content,
                            'importance': tip.importance,
                            'timing': tip.effective_timing
                        })
            
            data[subsidy.name] = subsidy_data
        
        return data
    
    def _generate_dify_response(self, question_text, user_context, detailed_data, intent):
        """Dify APIを使用して回答を生成"""
        try:
            # コンテキストを構築
            context = self._build_rich_context(detailed_data, intent, user_context)
            
            payload = {
                'inputs': {
                    'query': question_text,
                    'context': context,
                    'user_profile': user_context or {},
                    'intent': intent
                },
                'response_mode': 'blocking',
                'user': user_context.get('user_id', 'anonymous') if user_context else 'anonymous'
            }
            
            response = requests.post(
                f"{self.dify_api_url}/chat-messages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('answer', self._generate_enhanced_mock_response(question_text, user_context, detailed_data, intent))
            else:
                print(f"Dify API error: {response.status_code} - {response.text}")
                return self._generate_enhanced_mock_response(question_text, user_context, detailed_data, intent)
                
        except Exception as e:
            print(f"Dify API exception: {e}")
            return self._generate_enhanced_mock_response(question_text, user_context, detailed_data, intent)
    
    def _build_rich_context(self, detailed_data, intent, user_context):
        """Dify用の豊富なコンテキストを構築"""
        context_parts = []
        
        # システム情報
        context_parts.append("あなたは経験豊富な補助金コンサルタントです。具体的なデータに基づいて、わかりやすく親身なアドバイスを提供してください。")
        
        # ユーザー情報
        if user_context:
            business_type = user_context.get('business_type', '未設定')
            company_size = user_context.get('company_size', '未設定')
            context_parts.append(f"相談者情報: 事業種別={business_type}, 企業規模={company_size}")
        
        # 意図別のガイダンス
        intent_guidance = {
            'adoption_rate': '採択率について具体的な数値とトレンドを示し、業種別・企業規模別の傾向も説明してください。',
            'application_process': '申請手順を段階的に説明し、重要なポイントと期限を明確に示してください。',
            'requirements': '要件を整理して分かりやすく説明し、満たしやすい条件から優先順位をつけてください。',
            'amount': '補助額と補助率を明確に示し、実際にいくら受給できるかの例を挙げてください。',
            'success_tips': '採択率向上のための具体的で実践的なアドバイスを重要度順に提示してください。',
            'comparison': '各補助金の特徴を比較表形式で整理し、相談者に最適な選択肢を推奨してください。'
        }
        
        if intent in intent_guidance:
            context_parts.append(intent_guidance[intent])
        
        # 詳細データ
        if detailed_data:
            context_parts.append("\n=== 利用可能な補助金データ ===")
            for subsidy_name, data in detailed_data.items():
                context_parts.append(f"\n【{subsidy_name}】")
                
                # 基本情報
                basic = data['basic_info']
                context_parts.append(f"対象: {basic['target_business']}")
                context_parts.append(f"最大補助額: {basic['max_amount']:,}円")
                context_parts.append(f"補助率: {basic['subsidy_rate']}")
                context_parts.append(f"申請期間: {basic['application_period']}")
                
                # 統計データ
                if 'statistics' in data:
                    context_parts.append("採択実績:")
                    for stat in data['statistics']:
                        context_parts.append(f"  {stat['year']}年第{stat['round']}回: 採択率{stat['adoption_rate']}% ({stat['total_adoptions']}/{stat['total_applications']}件)")
                
                # ティップス
                if 'tips' in data:
                    context_parts.append("成功のポイント:")
                    for tip in data['tips'][:3]:
                        context_parts.append(f"  ・{tip['title']}: {tip['content']}")
        
        return '\n'.join(context_parts)
    
    def _generate_enhanced_mock_response(self, question_text, user_context, detailed_data, intent):
        """強化されたモック回答を生成"""
        
        # ユーザー情報を取得
        business_type = user_context.get('business_type', '') if user_context else ''
        company_size = user_context.get('company_size', '') if user_context else ''
        
        # 挨拶部分
        greeting = "こんにちは！補助金に関するご質問をいただき、ありがとうございます。"
        if business_type or company_size:
            greeting += f"{'、'.join(filter(None, [business_type, company_size]))}でのご相談ですね。"
        
        response_parts = [greeting]
        
        # 意図別の回答生成
        if intent == 'adoption_rate' and detailed_data:
            response_parts.extend(self._generate_adoption_rate_response(detailed_data))
        elif intent == 'application_process' and detailed_data:
            response_parts.extend(self._generate_process_response(detailed_data))
        elif intent == 'requirements' and detailed_data:
            response_parts.extend(self._generate_requirements_response(detailed_data))
        elif intent == 'amount' and detailed_data:
            response_parts.extend(self._generate_amount_response(detailed_data))
        elif intent == 'success_tips' and detailed_data:
            response_parts.extend(self._generate_tips_response(detailed_data))
        elif detailed_data:
            response_parts.extend(self._generate_overview_response(detailed_data))
        else:
            response_parts.append(self._generate_general_response(question_text))
        
        # まとめと次のアクション
        response_parts.append("\n📝 **次のステップ**")
        response_parts.append("1. 詳細な公募要領の確認")
        response_parts.append("2. 必要書類の準備")
        response_parts.append("3. 申請スケジュールの計画")
        response_parts.append("\nご不明な点がございましたら、お気軽にお聞かせください！")
        
        return '\n'.join(response_parts)
    
    def _generate_adoption_rate_response(self, detailed_data):
        """採択率に関する回答を生成"""
        parts = ["\n🎯 **採択率の実績データ**"]
        
        for subsidy_name, data in detailed_data.items():
            if 'statistics' in data:
                parts.append(f"\n**{subsidy_name}**")
                stats = data['statistics']
                if stats:
                    latest = stats[0]
                    parts.append(f"・最新の採択率: **{latest['adoption_rate']}%** ({latest['year']}年第{latest['round']}回)")
                    parts.append(f"・申請総数: {latest['total_applications']:,}件")
                    parts.append(f"・採択数: {latest['total_adoptions']:,}件")
                    
                    if latest['small_business_rate'] != latest['adoption_rate']:
                        parts.append(f"・小規模事業者: {latest['small_business_rate']:.1f}%")
                        parts.append(f"・中小企業: {latest['medium_business_rate']:.1f}%")
                    
                    # トレンド分析
                    if len(stats) > 1:
                        trend = stats[0]['adoption_rate'] - stats[1]['adoption_rate']
                        if trend > 2:
                            parts.append("📈 採択率は上昇傾向にあります")
                        elif trend < -2:
                            parts.append("📉 採択率は下降傾向にあります")
                        else:
                            parts.append("📊 採択率は安定しています")
        
        return parts
    
    def _generate_process_response(self, detailed_data):
        """申請プロセスに関する回答を生成"""
        parts = ["\n📋 **申請の流れ**"]
        
        # 共通の申請手順
        parts.extend([
            "\n**1. 事前準備**",
            "・gBizIDプライムの取得（2週間程度）",
            "・事業計画の策定",
            "・必要書類の収集",
            "",
            "**2. 申請書作成**",
            "・オンライン申請システムでの入力",
            "・添付書類のアップロード",
            "・申請内容の最終確認",
            "",
            "**3. 申請提出**",
            "・期限内での提出（推奨：締切2-3日前）",
            "・受付完了の確認",
            "",
            "**4. 審査・結果**",
            "・書面審査（約2-3ヶ月）",
            "・結果通知",
            "・採択後の手続き"
        ])
        
        # 個別の補助金情報
        if detailed_data:
            first_subsidy = list(detailed_data.values())[0]
            parts.append(f"\n**申請期間**: {first_subsidy['basic_info']['application_period']}")
            
            if 'tips' in first_subsidy:
                parts.append("\n💡 **申請のポイント**")
                for tip in first_subsidy['tips'][:3]:
                    if '申請' in tip['category'] or 'preparation' in tip['category']:
                        parts.append(f"・{tip['title']}")
        
        return parts
    
    def _generate_requirements_response(self, detailed_data):
        """要件に関する回答を生成"""
        parts = ["\n✅ **申請要件について**"]
        
        for subsidy_name, data in detailed_data.items():
            basic = data['basic_info']
            parts.append(f"\n**{subsidy_name}**")
            parts.append(f"・対象事業者: {basic['target_business']}")
            parts.append(f"・主な要件: {basic['requirements']}")
            
            if 'tips' in data:
                requirement_tips = [tip for tip in data['tips'] if '要件' in tip['content'] or '条件' in tip['content']]
                if requirement_tips:
                    parts.append("・注意点:")
                    for tip in requirement_tips[:2]:
                        parts.append(f"  - {tip['content']}")
        
        return parts
    
    def _generate_amount_response(self, detailed_data):
        """補助額に関する回答を生成"""
        parts = ["\n💰 **補助金額について**"]
        
        for subsidy_name, data in detailed_data.items():
            basic = data['basic_info']
            parts.append(f"\n**{subsidy_name}**")
            parts.append(f"・最大補助額: **{basic['max_amount']:,}円**")
            parts.append(f"・補助率: **{basic['subsidy_rate']}**")
            
            # 具体例
            if basic['max_amount'] >= 1000000:
                example_cost = basic['max_amount'] * 2  # 補助率を考慮した事業費例
                parts.append(f"・例: 事業費{example_cost:,}円の場合 → 補助額{basic['max_amount']:,}円")
        
        return parts
    
    def _generate_tips_response(self, detailed_data):
        """成功のコツに関する回答を生成"""
        parts = ["\n🎯 **採択率を高めるポイント**"]
        
        all_tips = []
        for data in detailed_data.values():
            if 'tips' in data:
                all_tips.extend(data['tips'])
        
        # 重要度順にソート
        all_tips.sort(key=lambda x: x['importance'], reverse=True)
        
        categories = {}
        for tip in all_tips[:8]:
            category = tip['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(tip)
        
        for category, tips in categories.items():
            parts.append(f"\n**{category}**")
            for tip in tips[:3]:
                parts.append(f"・{tip['title']}: {tip['content']}")
        
        return parts
    
    def _generate_overview_response(self, detailed_data):
        """概要回答を生成"""
        parts = ["\n📊 **補助金の概要**"]
        
        for subsidy_name, data in detailed_data.items():
            basic = data['basic_info']
            parts.append(f"\n**{subsidy_name}**")
            parts.append(f"・{basic['description']}")
            parts.append(f"・最大補助額: {basic['max_amount']:,}円（{basic['subsidy_rate']}）")
            
            if 'statistics' in data and data['statistics']:
                latest = data['statistics'][0]
                parts.append(f"・最新採択率: {latest['adoption_rate']}%")
        
        return parts
    
    def _generate_general_response(self, question_text):
        """一般的な回答を生成"""
        return """
申し訳ございませんが、具体的な補助金データが見つかりませんでした。

一般的に、補助金申請を成功させるためには以下が重要です：

1. **早期の情報収集**: 公募開始前から情報をチェック
2. **要件の確実な確認**: 申請要件を漏れなく満たすこと
3. **計画書の質**: 具体的で実現可能な事業計画
4. **期限の遵守**: 余裕を持った申請スケジュール

より具体的なアドバイスのために、対象とする補助金名や事業内容を教えていただけますでしょうか。
"""
    
    def _calculate_confidence(self, intent, subsidies, detailed_data):
        """回答の信頼度を計算"""
        base_confidence = 0.6
        
        # 関連補助金の数
        if subsidies:
            base_confidence += min(0.2, len(subsidies) * 0.05)
        
        # データの豊富さ
        if detailed_data:
            data_richness = sum(1 for data in detailed_data.values() 
                              if 'statistics' in data or 'tips' in data)
            base_confidence += min(0.15, data_richness * 0.03)
        
        # 意図の明確さ
        if intent in ['adoption_rate', 'amount', 'requirements']:
            base_confidence += 0.1
        
        return min(0.95, base_confidence)