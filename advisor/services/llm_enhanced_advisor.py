# advisor/services/llm_enhanced_advisor.py

import requests
import json
from django.conf import settings
from datetime import datetime
from ..models import SubsidyType, AdoptionStatistics, AdoptionTips

class LLMEnhancedAdvisorService:
    """LLM(Dify)と戦略ロジックを組み合わせた高度アドバイザー"""
    
    def __init__(self):
        self.dify_api_url = settings.DIFY_API_URL
        self.dify_api_key = settings.DIFY_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.dify_api_key}',
            'Content-Type': 'application/json'
        }
        
    def analyze_question(self, question_text, user_context=None):
        """LLMと戦略ロジックを組み合わせた分析"""
        
        # Step 1: 戦略的データ分析（Python）
        strategic_data = self._analyze_strategic_context(question_text, user_context)
        
        # Step 2: LLM（Dify）による自然な回答生成
        if self.dify_api_key:
            llm_response = self._get_llm_enhanced_response(question_text, user_context, strategic_data)
        else:
            llm_response = None
            
        # Step 3: 戦略ロジック + LLM回答の融合
        final_response = self._merge_strategy_and_llm(strategic_data, llm_response, question_text, user_context)
        
        return final_response
    
    def _analyze_strategic_context(self, question_text, user_context):
        """Pythonによる戦略的データ分析"""
        business_type = user_context.get('business_type', '') if user_context else ''
        company_size = user_context.get('company_size', '') if user_context else ''
        
        # 1. 補助金の戦略的選択
        recommended_subsidy = self._strategic_subsidy_selection(question_text, business_type)
        
        # 2. 競合状況分析
        competition_analysis = self._analyze_competition(recommended_subsidy, business_type)
        
        # 3. 成功確率計算
        success_probability = self._calculate_success_probability(recommended_subsidy, business_type, company_size)
        
        # 4. 最適タイミング分析
        timing_strategy = self._analyze_optimal_timing()
        
        # 5. 戦略的ティップス取得
        strategic_tips = self._get_strategic_tips(recommended_subsidy)
        
        return {
            'recommended_subsidy': recommended_subsidy,
            'competition_analysis': competition_analysis,
            'success_probability': success_probability,
            'timing_strategy': timing_strategy,
            'strategic_tips': strategic_tips,
            'business_type': business_type,
            'company_size': company_size
        }
    
    def _get_llm_enhanced_response(self, question_text, user_context, strategic_data):
        """LLM（Dify）による自然な回答生成"""
        
        # 戦略データをLLMに提供するための構造化プロンプト
        enhanced_prompt = self._build_llm_prompt(question_text, user_context, strategic_data)
        
        try:
            response = self._call_dify_api(enhanced_prompt)
            if response and 'answer' in response:
                return response['answer']
        except Exception as e:
            print(f"LLM API error: {e}")
        
        return None
    
    def _build_llm_prompt(self, question_text, user_context, strategic_data):
        """LLM用の強化プロンプト構築"""
        business_type = user_context.get('business_type', '未設定') if user_context else '未設定'
        company_size = user_context.get('company_size', '未設定') if user_context else '未設定'
        
        subsidy = strategic_data['recommended_subsidy']
        subsidy_name = subsidy.name if subsidy else 'IT導入補助金2025'
        
        prompt = f"""あなたは補助金申請の戦略コンサルタントです。以下の情報を基に、温かみがあり実践的なアドバイスを提供してください。

【相談者情報】
- 事業種別: {business_type}
- 企業規模: {company_size}
- 質問: {question_text}

【戦略分析結果】
- 推奨補助金: {subsidy_name}
- 成功確率: {strategic_data['success_probability']}%
- 競合状況: {strategic_data['competition_analysis']}
- 最適タイミング: {strategic_data['timing_strategy']}

【重要な戦略ポイント】
{self._format_strategic_tips(strategic_data['strategic_tips'])}

【回答スタイル】
1. 相談者に寄り添う温かい文体
2. 具体的な数値と根拠
3. 実行可能な行動指針
4. 戦略的思考を含む

以下の構成で回答してください：

## 🎯 お客様の状況分析と最適戦略

## 💡 なぜこの補助金がベストなのか

## 🛡️ 競合に勝つための3つの差別化戦略

## ⏰ 成功確率を最大化するタイミング戦略

## 🚀 今すぐ始めるべき具体的アクション

必ず日本語で、専門コンサルタントとして丁寧かつ戦略的に回答してください。"""

        return prompt
    
    def _merge_strategy_and_llm(self, strategic_data, llm_response, question_text, user_context):
        """戦略ロジックとLLM回答を融合"""
        
        if llm_response:
            # LLMの回答に戦略的要素を強化
            enhanced_answer = self._enhance_llm_response(llm_response, strategic_data)
        else:
            # LLMが利用できない場合は純粋な戦略回答
            enhanced_answer = self._generate_pure_strategic_response(strategic_data, question_text, user_context)
        
        return {
            'answer': enhanced_answer,
            'recommended_subsidies': [strategic_data['recommended_subsidy']] if strategic_data['recommended_subsidy'] else [],
            'confidence_score': 0.95,
            'model_used': 'llm-enhanced-strategic'
        }
    
    def _enhance_llm_response(self, llm_response, strategic_data):
        """LLM回答に戦略的データを追加"""
        
        # 戦略的データテーブルを追加
        strategic_enhancement = f"""

---

## 📊 戦略的データ分析（AI + データサイエンス）

### 🎯 採択確率シミュレーション
- **基本確率**: {strategic_data['success_probability']}%
- **早期申請ボーナス**: +15%
- **戦略実装後予測**: {min(95, strategic_data['success_probability'] + 15)}%

### 📈 競合状況マップ
```
{strategic_data['competition_analysis']}
```

### ⏰ 最適申請タイミング
**推奨期間**: {strategic_data['timing_strategy']}
**準備開始**: 今すぐ（120日戦略プログラム）

### 🎖️ 成功要因ランキング
1. **支援機関連携** (重要度: ★★★★★)
2. **早期申請** (重要度: ★★★★☆)  
3. **差別化戦略** (重要度: ★★★★☆)
4. **数値化根拠** (重要度: ★★★☆☆)

---

💡 **戦略コンサルタントからの一言**
データと経験に基づく分析では、お客様の成功確率は非常に高いです。
適切な戦略実行により、必ず良い結果を得られるでしょう！"""

        return llm_response + strategic_enhancement
    
    def _generate_pure_strategic_response(self, strategic_data, question_text, user_context):
        """純粋な戦略回答生成（LLMバックアップ）"""
        
        subsidy = strategic_data['recommended_subsidy']
        subsidy_name = subsidy.name if subsidy else 'IT導入補助金2025'
        business_type = strategic_data['business_type']
        
        return f"""## 🎯 戦略分析：{subsidy_name}での勝利シナリオ

### 📊 お客様の現状評価
- **推奨補助金**: {subsidy_name}
- **予測成功確率**: {strategic_data['success_probability']}%
- **競合状況**: {strategic_data['competition_analysis']}
- **業種適合度**: {business_type}での実績良好

## 🛡️ 競合他社に勝つ3つの差別化戦略

### 戦略①「先行優位作戦」⚡
公募開始2週間以内の早期申請により、審査員の新鮮な目で評価されます。
**効果**: 採択率+15%向上

### 戦略②「ニッチ特化作戦」🎯
業界特有の課題解決にフォーカスし、競合の少ない分野で優位性を確保。
**効果**: 差別化による印象度向上

### 戦略③「数値説得作戦」📈
具体的な改善目標（「売上30%向上」など）で審査員を納得させます。
**効果**: 評価基準の明確化

## ⏰ 最適タイミング戦略

**推奨申請時期**: {strategic_data['timing_strategy']}
**準備開始**: 今すぐ（90-120日間プログラム）

## 🚀 今すぐ始めるべき5つのアクション

1. ✅ 支援機関の選定と初回相談予約
2. ✅ 現状業務の課題整理とデータ収集
3. ✅ 競合他社の動向調査
4. ✅ 投資対効果の概算計算
5. ✅ 申請スケジュールの策定

## 📞 次のステップ

まずは信頼できる支援機関との相談から始めましょう。
この戦略プランを実行すれば、必ず良い結果が得られます！

---
*戦略的データ分析 + 実務経験に基づく提案*"""
    
    def _strategic_subsidy_selection(self, question_text, business_type):
        """戦略的補助金選択"""
        subsidies = SubsidyType.objects.all()
        question_lower = question_text.lower()
        
        # キーワード + 業種マッチング
        scores = {}
        for subsidy in subsidies:
            score = 0
            
            # キーワードマッチング
            if 'it' in question_lower and 'IT導入' in subsidy.name:
                score += 30
            elif '再構築' in question_lower and '事業再構築' in subsidy.name:
                score += 30
            elif 'ものづくり' in question_lower and 'ものづくり' in subsidy.name:
                score += 30
            elif '持続化' in question_lower and '持続化' in subsidy.name:
                score += 30
            
            # 業種適合度
            if business_type:
                if 'IT' in business_type and 'IT導入' in subsidy.name:
                    score += 20
                elif '製造業' in business_type and 'ものづくり' in subsidy.name:
                    score += 20
                elif '小規模' in business_type and '持続化' in subsidy.name:
                    score += 20
            
            # 採択率ボーナス
            recent_stats = AdoptionStatistics.objects.filter(
                subsidy_type=subsidy
            ).order_by('-year', '-round_number').first()
            
            if recent_stats and recent_stats.adoption_rate > 60:
                score += 10
                
            scores[subsidy] = score
        
        if scores:
            return max(scores.keys(), key=lambda x: scores[x])
        return subsidies.first() if subsidies.exists() else None
    
    def _analyze_competition(self, subsidy, business_type):
        """競合状況分析"""
        if not subsidy:
            return "分析データ不足"
        
        recent_stats = AdoptionStatistics.objects.filter(
            subsidy_type=subsidy
        ).order_by('-year', '-round_number').first()
        
        if recent_stats:
            rate = recent_stats.adoption_rate
            apps = recent_stats.total_applications
            
            if rate > 65:
                return f"中程度の競争（採択率{rate}%・年間{apps:,}件申請）- 戦略的差別化で勝機あり"
            elif rate > 45:
                return f"やや激化（採択率{rate}%・年間{apps:,}件申請）- 高度な戦略必須"
            else:
                return f"激しい競争（採択率{rate}%・年間{apps:,}件申請）- 最高レベルの戦略要求"
        
        return "標準的な競争レベル"
    
    def _calculate_success_probability(self, subsidy, business_type, company_size):
        """成功確率計算"""
        base_rate = 50
        
        if subsidy:
            recent_stats = AdoptionStatistics.objects.filter(
                subsidy_type=subsidy
            ).order_by('-year', '-round_number').first()
            
            if recent_stats:
                base_rate = recent_stats.adoption_rate
        
        # 戦略的調整
        if business_type and subsidy:
            if ('IT' in business_type and 'IT導入' in subsidy.name) or \
               ('製造業' in business_type and 'ものづくり' in subsidy.name):
                base_rate += 15
        
        if '小規模' in str(company_size):
            base_rate += 8
        
        return min(95, max(30, int(base_rate)))
    
    def _analyze_optimal_timing(self):
        """最適タイミング分析"""
        current_month = datetime.now().month
        
        timing_map = {
            1: "1月下旬〜2月上旬（新年度準備期・競合少なめ）",
            2: "3月上旬〜中旬（年度末予算消化期・狙い目）", 
            3: "3月下旬〜4月上旬（新年度第1回公募・最重要）",
            4: "5月中旬〜下旬（第2回公募・早期申請狙い）",
            5: "6月上旬〜中旬（第2回公募・最終チャンス）",
            6: "7月上旬〜中旬（夏季公募・競合減少期）",
            7: "7月下旬〜8月上旬（夏季公募・穴場期間）",
            8: "9月上旬〜中旬（秋季公募・重要期間）",
            9: "9月下旬〜10月上旬（秋季公募・激戦期）",
            10: "11月上旬〜中旬（年末公募・最終機会）",
            11: "12月上旬（年内最終・来年準備期）",
            12: "来年1月中旬（新年度戦略立案期）"
        }
        
        return timing_map.get(current_month, "通年申請可能期間")
    
    def _get_strategic_tips(self, subsidy):
        """戦略的ティップス取得"""
        if not subsidy:
            return []
        
        tips = AdoptionTips.objects.filter(
            subsidy_type=subsidy,
            category='strategy'
        ).order_by('-importance')[:3]
        
        return [
            {
                'title': tip.title,
                'content': tip.content,
                'importance': tip.importance
            }
            for tip in tips
        ]
    
    def _format_strategic_tips(self, tips):
        """戦略ティップスのフォーマット"""
        if not tips:
            return "戦略データを準備中..."
        
        formatted = []
        for tip in tips:
            importance_stars = "★" * tip['importance'] + "☆" * (4 - tip['importance'])
            formatted.append(f"- {tip['title']} ({importance_stars})")
        
        return "\n".join(formatted)
    
    def _call_dify_api(self, query_text):
        """Dify API呼び出し"""
        try:
            request_data = {
                "inputs": {},
                "query": query_text,
                "response_mode": "blocking",
                "user": f"llm_enhanced_user_{hash(query_text) % 10000}"
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


# メインサービスとして設定
AIAdvisorService = LLMEnhancedAdvisorService