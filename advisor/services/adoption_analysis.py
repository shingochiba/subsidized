# advisor/services/adoption_analysis.py

import json
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q
from django.contrib.auth.models import User
from ..models import (
    SubsidyType, AdoptionStatistics, AdoptionTips, 
    UserApplicationHistory, ApplicationScoreCard
)

class AdoptionAnalysisService:
    """採択率分析・向上支援サービス"""
    
    def get_adoption_statistics(self, subsidy_type_id=None, years=3):
        """採択統計データを取得"""
        current_year = datetime.now().year
        start_year = current_year - years
        
        query = AdoptionStatistics.objects.filter(year__gte=start_year)
        if subsidy_type_id:
            query = query.filter(subsidy_type_id=subsidy_type_id)
        
        statistics = query.select_related('subsidy_type').order_by('-year', '-round_number')
        
        # データを整理
        result = {}
        for stat in statistics:
            subsidy_name = stat.subsidy_type.name
            if subsidy_name not in result:
                result[subsidy_name] = {
                    'subsidy_type': stat.subsidy_type,
                    'yearly_data': [],
                    'average_adoption_rate': 0,
                    'trend': 'stable'
                }
            
            result[subsidy_name]['yearly_data'].append({
                'year': stat.year,
                'round': stat.round_number,
                'total_applications': stat.total_applications,
                'total_adoptions': stat.total_adoptions,
                'adoption_rate': stat.adoption_rate,
                'small_business_rate': stat.small_business_adoption_rate,
                'medium_business_rate': stat.medium_business_adoption_rate,
                'industry_stats': stat.industry_statistics
            })
        
        # 平均採択率とトレンドを計算
        for subsidy_name, data in result.items():
            if data['yearly_data']:
                rates = [item['adoption_rate'] for item in data['yearly_data']]
                data['average_adoption_rate'] = sum(rates) / len(rates)
                
                # トレンド分析（直近3年のデータがある場合）
                if len(rates) >= 3:
                    recent_avg = sum(rates[:2]) / 2  # 直近2年
                    older_avg = sum(rates[2:]) / (len(rates) - 2)  # それ以前
                    
                    if recent_avg > older_avg + 5:
                        data['trend'] = 'improving'
                    elif recent_avg < older_avg - 5:
                        data['trend'] = 'declining'
        
        return result
    
    def get_adoption_tips(self, subsidy_type_id, user_profile=None):
        """採択率向上のためのティップスを取得"""
        tips = AdoptionTips.objects.filter(
            subsidy_type_id=subsidy_type_id
        ).order_by('-importance', 'category')
        
        # カテゴリ別に整理
        categorized_tips = {}
        for tip in tips:
            category = tip.get_category_display()
            if category not in categorized_tips:
                categorized_tips[category] = []
            
            categorized_tips[category].append({
                'title': tip.title,
                'content': tip.content,
                'importance': tip.importance,
                'importance_display': tip.get_importance_display(),
                'effective_timing': tip.effective_timing,
                'reference_url': tip.reference_url,
                'is_success_case': tip.is_success_case
            })
        
        return categorized_tips
    
    def calculate_adoption_probability(self, user, subsidy_type, user_context):
        """ユーザーの採択可能性を計算"""
        # 基本確率は過去の採択率から
        recent_stats = AdoptionStatistics.objects.filter(
            subsidy_type=subsidy_type,
            year__gte=datetime.now().year - 2
        ).order_by('-year', '-round_number').first()
        
        if recent_stats:
            base_probability = recent_stats.adoption_rate
            
            # 企業規模による調整
            company_size = user_context.get('company_size', '')
            if '小規模' in company_size and recent_stats.small_business_adoption_rate > 0:
                base_probability = recent_stats.small_business_adoption_rate
            elif '中小企業' in company_size and recent_stats.medium_business_adoption_rate > 0:
                base_probability = recent_stats.medium_business_adoption_rate
        else:
            base_probability = 30.0  # デフォルト値
        
        # ユーザーの過去の申請履歴による調整
        user_history = UserApplicationHistory.objects.filter(user=user)
        success_rate = 0
        if user_history.exists():
            total_applications = user_history.count()
            successful_applications = user_history.filter(status='adopted').count()
            success_rate = (successful_applications / total_applications) * 100
            
            # 過去の成功率で調整（±10%の範囲）
            history_adjustment = min(10, max(-10, (success_rate - 30) * 0.3))
            base_probability += history_adjustment
        
        # 業種適合度による調整
        business_type = user_context.get('business_type', '')
        if business_type and recent_stats and recent_stats.industry_statistics:
            industry_stats = recent_stats.industry_statistics.get(business_type)
            if industry_stats:
                industry_rate = industry_stats.get('adoption_rate', base_probability)
                base_probability = (base_probability + industry_rate) / 2
        
        return min(95, max(5, base_probability))  # 5-95%の範囲に制限
    
    def generate_scorecard(self, user, subsidy_type, user_context):
        """採択スコアカードを生成"""
        # 既存のスコアカードがあるかチェック
        existing_scorecard = ApplicationScoreCard.objects.filter(
            user=user, subsidy_type=subsidy_type
        ).first()
        
        if existing_scorecard:
            return self._format_scorecard(existing_scorecard)
        
        # 新しいスコアカードを生成
        scores = self._calculate_scores(user, subsidy_type, user_context)
        
        scorecard = ApplicationScoreCard.objects.create(
            user=user,
            subsidy_type=subsidy_type,
            **scores
        )
        
        return self._format_scorecard(scorecard)
    
    def _calculate_scores(self, user, subsidy_type, user_context):
        """各種スコアを計算"""
        # 基本スコア（実際の実装では、より詳細な分析が必要）
        business_plan_score = 70  # 事業計画の充実度
        innovation_score = 60     # 革新性
        feasibility_score = 75    # 実現可能性
        market_potential_score = 65  # 市場性
        financial_health_score = 80  # 財務健全性
        
        # 企業規模による調整
        company_size = user_context.get('company_size', '')
        if '小規模' in company_size:
            # 小規模事業者は申請書作成支援が手厚い傾向
            business_plan_score += 5
            feasibility_score += 10
        
        # 業種による調整
        business_type = user_context.get('business_type', '')
        if 'IT' in business_type and 'IT導入' in subsidy_type.name:
            innovation_score += 15
            market_potential_score += 10
        
        # 過去の申請履歴による調整
        user_history = UserApplicationHistory.objects.filter(user=user)
        if user_history.filter(status='adopted').exists():
            # 過去に採択経験がある場合
            business_plan_score += 10
            feasibility_score += 10
        
        total_score = (
            business_plan_score + innovation_score + feasibility_score + 
            market_potential_score + financial_health_score
        ) // 5
        
        # 改善提案を生成
        improvement_suggestions = self._generate_improvement_suggestions({
            'business_plan': business_plan_score,
            'innovation': innovation_score,
            'feasibility': feasibility_score,
            'market_potential': market_potential_score,
            'financial_health': financial_health_score
        })
        
        return {
            'business_plan_score': business_plan_score,
            'innovation_score': innovation_score,
            'feasibility_score': feasibility_score,
            'market_potential_score': market_potential_score,
            'financial_health_score': financial_health_score,
            'total_score': total_score,
            'improvement_suggestions': improvement_suggestions
        }
    
    def _generate_improvement_suggestions(self, scores):
        """スコアに基づく改善提案を生成"""
        suggestions = []
        
        if scores['business_plan'] < 70:
            suggestions.append({
                'category': '事業計画',
                'priority': 'high',
                'suggestion': '事業計画書をより具体的かつ詳細に作成してください。数値目標や実行スケジュールを明確にしましょう。'
            })
        
        if scores['innovation'] < 60:
            suggestions.append({
                'category': '革新性',
                'priority': 'medium',
                'suggestion': '既存事業との差別化ポイントや新規性を明確にアピールしてください。'
            })
        
        if scores['feasibility'] < 70:
            suggestions.append({
                'category': '実現可能性',
                'priority': 'high',
                'suggestion': '実行体制や必要なリソース、リスク対策を詳細に記載してください。'
            })
        
        if scores['market_potential'] < 65:
            suggestions.append({
                'category': '市場性',
                'priority': 'medium',
                'suggestion': '市場調査データや競合分析を充実させ、市場ニーズを明確に示してください。'
            })
        
        if scores['financial_health'] < 75:
            suggestions.append({
                'category': '財務',
                'priority': 'high',
                'suggestion': '財務計画や資金調達計画を見直し、事業の持続可能性を示してください。'
            })
        
        return suggestions
    
    def _format_scorecard(self, scorecard):
        """スコアカードをフォーマット"""
        return {
            'total_score': scorecard.total_score,
            'scores': {
                'business_plan': scorecard.business_plan_score,
                'innovation': scorecard.innovation_score,
                'feasibility': scorecard.feasibility_score,
                'market_potential': scorecard.market_potential_score,
                'financial_health': scorecard.financial_health_score
            },
            'improvement_suggestions': scorecard.improvement_suggestions,
            'score_interpretation': self._interpret_score(scorecard.total_score),
            'created_at': scorecard.created_at
        }
    
    def _interpret_score(self, score):
        """スコアの解釈"""
        if score >= 85:
            return {
                'level': 'excellent',
                'message': '採択可能性が非常に高いです。申請書の最終チェックを行い、自信を持って申請してください。',
                'color': 'success'
            }
        elif score >= 70:
            return {
                'level': 'good',
                'message': '採択可能性が高いです。いくつかの改善点を確認して申請準備を進めてください。',
                'color': 'primary'
            }
        elif score >= 55:
            return {
                'level': 'fair',
                'message': '採択の可能性はありますが、改善の余地があります。提案された改善点を重点的に見直してください。',
                'color': 'warning'
            }
        else:
            return {
                'level': 'needs_improvement',
                'message': '申請前に事業計画の見直しが必要です。専門家への相談も検討してください。',
                'color': 'danger'
            }
    
    def get_success_factors_analysis(self, subsidy_type):
        """成功要因分析を取得"""
        # 採択された申請の共通要因を分析
        adopted_applications = UserApplicationHistory.objects.filter(
            subsidy_type=subsidy_type,
            status='adopted'
        )
        
        if not adopted_applications.exists():
            return None
        
        # 業種別成功率
        industry_success = {}
        for app in adopted_applications:
            industry = app.business_type_at_application
            if industry not in industry_success:
                industry_success[industry] = {'adopted': 0, 'total': 0}
            industry_success[industry]['adopted'] += 1
        
        # 全申請も含めて成功率を計算
        all_applications = UserApplicationHistory.objects.filter(subsidy_type=subsidy_type)
        for app in all_applications:
            industry = app.business_type_at_application
            if industry not in industry_success:
                industry_success[industry] = {'adopted': 0, 'total': 0}
            industry_success[industry]['total'] += 1
        
        # 成功率を計算
        for industry, data in industry_success.items():
            if data['total'] > 0:
                data['success_rate'] = (data['adopted'] / data['total']) * 100
            else:
                data['success_rate'] = 0
        
        return {
            'industry_success_rates': industry_success,
            'total_applications': all_applications.count(),
            'total_adoptions': adopted_applications.count(),
            'overall_success_rate': (adopted_applications.count() / all_applications.count() * 100) if all_applications.exists() else 0
        }