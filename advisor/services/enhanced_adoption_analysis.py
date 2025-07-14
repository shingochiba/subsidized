# advisor/services/enhanced_adoption_analysis.py

import json
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q, Max, Min, Sum
from django.contrib.auth.models import User
from ..models import (
    SubsidyType, AdoptionStatistics, AdoptionTips, 
    UserApplicationHistory, StrategicTips
)

class EnhancedAdoptionAnalysisService:
    """採択率分析の強化サービス"""
    
    def __init__(self):
        self.current_year = datetime.now().year
    
    def get_comprehensive_overview(self):
        """全補助金の統合概要分析"""
        # 全補助金の統計取得
        all_stats = AdoptionStatistics.objects.filter(
            year__gte=self.current_year - 3
        ).select_related('subsidy_type')
        
        if not all_stats.exists():
            return self._empty_overview()
        
        # 全体統計計算
        total_applications = all_stats.aggregate(Sum('total_applications'))['total_applications__sum'] or 0
        total_adoptions = all_stats.aggregate(Sum('total_adoptions'))['total_adoptions__sum'] or 0
        overall_rate = (total_adoptions / total_applications * 100) if total_applications > 0 else 0
        
        # 年度別統計
        yearly_stats = []
        for year in range(self.current_year - 3, self.current_year + 1):
            year_stats = all_stats.filter(year=year)
            if year_stats.exists():
                year_apps = year_stats.aggregate(Sum('total_applications'))['total_applications__sum'] or 0
                year_adoptions = year_stats.aggregate(Sum('total_adoptions'))['total_adoptions__sum'] or 0
                year_rate = (year_adoptions / year_apps * 100) if year_apps > 0 else 0
                
                yearly_stats.append({
                    'year': year,
                    'total_applications': year_apps,
                    'total_adoptions': year_adoptions,
                    'adoption_rate': round(year_rate, 1)
                })
        
        # トレンド分析
        trend = self._analyze_trend(yearly_stats)
        
        # 補助金別統計
        subsidy_stats = {}
        for subsidy in SubsidyType.objects.filter(is_active=True):
            subsidy_data = all_stats.filter(subsidy_type=subsidy)
            if subsidy_data.exists():
                subsidy_apps = subsidy_data.aggregate(Sum('total_applications'))['total_applications__sum'] or 0
                subsidy_adoptions = subsidy_data.aggregate(Sum('total_adoptions'))['total_adoptions__sum'] or 0
                subsidy_rate = (subsidy_adoptions / subsidy_apps * 100) if subsidy_apps > 0 else 0
                
                subsidy_stats[subsidy.name] = {
                    'adoption_rate': round(subsidy_rate, 1),
                    'total_applications': subsidy_apps,
                    'total_adoptions': subsidy_adoptions,
                    'competitiveness': self._calculate_competitiveness(subsidy_rate)
                }
        
        return {
            'overall_stats': {
                'adoption_rate': round(overall_rate, 1),
                'total_applications': total_applications,
                'total_adoptions': total_adoptions,
                'trend': trend
            },
            'yearly_stats': yearly_stats,
            'subsidy_breakdown': subsidy_stats,
            'analysis_period': f'{self.current_year - 3}-{self.current_year}',
            'last_updated': datetime.now().isoformat()
        }
    
    def get_detailed_statistics(self, subsidy_type):
        """特定補助金の詳細統計"""
        stats = AdoptionStatistics.objects.filter(
            subsidy_type=subsidy_type,
            year__gte=self.current_year - 3
        ).order_by('-year', '-round_number')
        
        if not stats.exists():
            return self._empty_detailed_stats(subsidy_type)
        
        # 年度別・回次別統計
        detailed_stats = []
        yearly_summary = {}
        
        for stat in stats:
            detailed_stats.append({
                'year': stat.year,
                'round_number': stat.round_number,
                'total_applications': stat.total_applications,
                'total_adoptions': stat.total_adoptions,
                'adoption_rate': stat.adoption_rate,
                'small_business_rate': stat.small_business_adoption_rate,
                'medium_business_rate': stat.medium_business_adoption_rate,
                'average_amount': stat.average_adoption_amount
            })
            
            # 年度別サマリー
            if stat.year not in yearly_summary:
                yearly_summary[stat.year] = {
                    'total_applications': 0,
                    'total_adoptions': 0,
                    'rounds': 0
                }
            
            yearly_summary[stat.year]['total_applications'] += stat.total_applications
            yearly_summary[stat.year]['total_adoptions'] += stat.total_adoptions
            yearly_summary[stat.year]['rounds'] += 1
        
        # 年度別採択率計算
        for year_data in yearly_summary.values():
            if year_data['total_applications'] > 0:
                year_data['adoption_rate'] = round(
                    year_data['total_adoptions'] / year_data['total_applications'] * 100, 1
                )
            else:
                year_data['adoption_rate'] = 0
        
        # 業種別分析
        industry_analysis = self._get_industry_analysis(subsidy_type)
        
        # 成功要因分析
        success_factors = self._analyze_success_factors(subsidy_type)
        
        # トレンド予測
        trend_prediction = self._predict_trend(stats)
        
        return {
            'subsidy_info': {
                'id': subsidy_type.id,
                'name': subsidy_type.name,
                'description': subsidy_type.description,
                'max_amount': subsidy_type.max_amount
            },
            'detailed_statistics': detailed_stats,
            'yearly_summary': yearly_summary,
            'industry_analysis': industry_analysis,
            'success_factors': success_factors,
            'trend_prediction': trend_prediction,
            'analysis_date': datetime.now().isoformat()
        }
    
    def get_strategic_tips(self, subsidy_type, user_profile=None):
        """戦略的ティップス取得（カスタマイズ版）"""
        # 基本ティップス
        basic_tips = AdoptionTips.objects.filter(
            subsidy_type=subsidy_type
        ).order_by('-importance', 'category')
        
        # 戦略的ティップス
        strategic_tips = StrategicTips.objects.filter(
            subsidy_name=subsidy_type.name
        ).order_by('-importance')
        
        # カテゴリ別整理
        categorized_tips = {
            '事前準備': [],
            '申請書作成': [],
            '戦略・ポイント': [],
            '成功事例': [],
            'AI推奨戦略': []
        }
        
        # 基本ティップスの分類
        for tip in basic_tips:
            category = tip.get_category_display()
            if category in categorized_tips:
                categorized_tips[category].append({
                    'title': tip.title,
                    'content': tip.content,
                    'importance': tip.importance,
                    'importance_display': tip.get_importance_display(),
                    'effective_timing': tip.effective_timing,
                    'success_rate_impact': getattr(tip, 'success_rate_impact', None),
                    'is_success_case': tip.is_success_case,
                    'source': 'basic'
                })
        
        # 戦略的ティップスの追加
        for tip in strategic_tips:
            category = 'AI推奨戦略'
            categorized_tips[category].append({
                'title': tip.title,
                'content': tip.content,
                'importance': tip.importance,
                'effective_timing': tip.effective_timing,
                'is_success_case': tip.is_success_case,
                'source': 'strategic'
            })
        
        # ユーザープロファイルに基づくカスタマイズ
        if user_profile:
            categorized_tips = self._customize_tips_for_user(categorized_tips, user_profile)
        
        # 空のカテゴリを削除
        categorized_tips = {k: v for k, v in categorized_tips.items() if v}
        
        return categorized_tips
    
    def calculate_adoption_probability(self, user_profile, subsidy_id=None):
        """採択確率の詳細計算"""
        if subsidy_id:
            subsidy = SubsidyType.objects.get(id=subsidy_id)
        else:
            # デフォルトで最も一般的な補助金を選択
            subsidy = SubsidyType.objects.filter(name__contains='IT導入').first()
            if not subsidy:
                subsidy = SubsidyType.objects.first()
        
        if not subsidy:
            return self._default_probability_result()
        
        # 基本確率（過去の採択率）
        recent_stats = AdoptionStatistics.objects.filter(
            subsidy_type=subsidy,
            year__gte=self.current_year - 2
        ).aggregate(
            avg_rate=Avg('adoption_rate'),
            total_apps=Sum('total_applications'),
            total_adoptions=Sum('total_adoptions')
        )
        
        base_probability = recent_stats['avg_rate'] or 50.0
        
        # 調整要因
        adjustments = []
        final_probability = base_probability
        
        # 業種による調整
        business_type = user_profile.get('business_type', '')
        business_adjustment = self._get_business_type_adjustment(business_type, subsidy)
        final_probability += business_adjustment
        if business_adjustment != 0:
            adjustments.append(f"業種補正: {business_adjustment:+.1f}%")
        
        # 企業規模による調整
        company_size = user_profile.get('company_size', '')
        size_adjustment = self._get_company_size_adjustment(company_size, subsidy)
        final_probability += size_adjustment
        if size_adjustment != 0:
            adjustments.append(f"企業規模補正: {size_adjustment:+.1f}%")
        
        # 経験による調整
        experience = user_profile.get('experience', 'none')
        experience_adjustment = self._get_experience_adjustment(experience)
        final_probability += experience_adjustment
        if experience_adjustment != 0:
            adjustments.append(f"経験補正: {experience_adjustment:+.1f}%")
        
        # 支援機関連携による調整
        support_agency = user_profile.get('support_agency', 'none')
        support_adjustment = self._get_support_adjustment(support_agency)
        final_probability += support_adjustment
        if support_adjustment != 0:
            adjustments.append(f"支援機関補正: {support_adjustment:+.1f}%")
        
        # 確率の範囲制限
        final_probability = max(5.0, min(95.0, final_probability))
        
        # 評価とアドバイス
        assessment = self._assess_probability(final_probability)
        improvement_suggestions = self._generate_improvement_suggestions(
            final_probability, user_profile, subsidy
        )
        
        return {
            'probability': round(final_probability, 1),
            'base_probability': round(base_probability, 1),
            'adjustments': adjustments,
            'assessment': assessment,
            'improvement_suggestions': improvement_suggestions,
            'calculation_details': {
                'subsidy_name': subsidy.name,
                'data_period': f'{self.current_year - 2}-{self.current_year}',
                'total_applications': recent_stats['total_apps'] or 0,
                'user_profile': user_profile
            }
        }
    
    def get_industry_comparison(self):
        """業種別比較分析"""
        industries = [
            '製造業', 'IT・情報通信業', 'サービス業', 
            '建設業', '卸売業', '小売業', 'その他'
        ]
        
        comparison_data = {}
        
        for industry in industries:
            # 業種別の統計計算（簡易版、実際にはより詳細なデータが必要）
            industry_stats = self._calculate_industry_stats(industry)
            comparison_data[industry] = industry_stats
        
        return comparison_data
    
    def get_user_history_analysis(self, user):
        """ユーザーの申請履歴分析"""
        history = UserApplicationHistory.objects.filter(user=user)
        
        if not history.exists():
            return {'message': '申請履歴がありません'}
        
        total_applications = history.count()
        adopted_count = history.filter(status='adopted').count()
        success_rate = (adopted_count / total_applications * 100) if total_applications > 0 else 0
        
        # 補助金別成功率
        subsidy_breakdown = {}
        for subsidy in SubsidyType.objects.all():
            subsidy_apps = history.filter(subsidy_type=subsidy)
            if subsidy_apps.exists():
                subsidy_total = subsidy_apps.count()
                subsidy_adopted = subsidy_apps.filter(status='adopted').count()
                subsidy_rate = (subsidy_adopted / subsidy_total * 100) if subsidy_total > 0 else 0
                
                subsidy_breakdown[subsidy.name] = {
                    'total_applications': subsidy_total,
                    'adopted_count': subsidy_adopted,
                    'success_rate': round(subsidy_rate, 1)
                }
        
        # 改善提案
        improvement_advice = self._generate_user_improvement_advice(user, history)
        
        return {
            'total_applications': total_applications,
            'adopted_count': adopted_count,
            'success_rate': round(success_rate, 1),
            'subsidy_breakdown': subsidy_breakdown,
            'improvement_advice': improvement_advice,
            'last_application': history.order_by('-application_date').first().application_date if history.exists() else None
        }
    
    # プライベートメソッド
    def _empty_overview(self):
        return {
            'overall_stats': {'adoption_rate': 0, 'total_applications': 0, 'total_adoptions': 0, 'trend': 'stable'},
            'yearly_stats': [],
            'subsidy_breakdown': {},
            'message': 'データが不足しています'
        }
    
    def _empty_detailed_stats(self, subsidy_type):
        return {
            'subsidy_info': {'id': subsidy_type.id, 'name': subsidy_type.name},
            'detailed_statistics': [],
            'yearly_summary': {},
            'message': 'データが不足しています'
        }
    
    def _analyze_trend(self, yearly_stats):
        if len(yearly_stats) < 2:
            return 'stable'
        
        recent_rate = yearly_stats[-1]['adoption_rate']
        previous_rate = yearly_stats[-2]['adoption_rate']
        
        if recent_rate > previous_rate + 5:
            return 'improving'
        elif recent_rate < previous_rate - 5:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_competitiveness(self, adoption_rate):
        if adoption_rate >= 70:
            return 'low'  # 低競争
        elif adoption_rate >= 50:
            return 'medium'  # 中競争
        else:
            return 'high'  # 高競争
    
    def _get_business_type_adjustment(self, business_type, subsidy):
        # 業種と補助金の適合性による調整
        adjustments = {
            'IT導入補助金2025': {
                'IT・情報通信業': 5.0,
                '製造業': 3.0,
                'サービス業': 2.0,
                '建設業': 1.0,
                '卸売業': 0.0,
                '小売業': -1.0
            },
            'ものづくり補助金': {
                '製造業': 8.0,
                '建設業': 3.0,
                'IT・情報通信業': 1.0,
                'サービス業': -2.0,
                '卸売業': -3.0,
                '小売業': -5.0
            }
        }
        
        subsidy_adjustments = adjustments.get(subsidy.name, {})
        return subsidy_adjustments.get(business_type, 0.0)
    
    def _get_company_size_adjustment(self, company_size, subsidy):
        # 企業規模による調整
        if '小規模' in company_size:
            return 5.0  # 小規模事業者は優遇される傾向
        elif '中小企業' in company_size:
            return 2.0
        elif '中堅企業' in company_size:
            return -3.0  # 中堅企業は競争が激しい
        return 0.0
    
    def _get_experience_adjustment(self, experience):
        adjustments = {
            'none': 0.0,
            'once': 5.0,
            'multiple': 10.0,
            'adopted': 15.0
        }
        return adjustments.get(experience, 0.0)
    
    def _get_support_adjustment(self, support_agency):
        adjustments = {
            'none': 0.0,
            'planned': 8.0,
            'confirmed': 15.0
        }
        return adjustments.get(support_agency, 0.0)
    
    def _assess_probability(self, probability):
        if probability >= 75:
            return {
                'level': 'excellent',
                'message': '採択の可能性が非常に高いです。自信を持って申請を進めてください。',
                'color': 'success'
            }
        elif probability >= 60:
            return {
                'level': 'good',
                'message': '採択の可能性が高いです。準備を確実に進めれば良い結果が期待できます。',
                'color': 'primary'
            }
        elif probability >= 40:
            return {
                'level': 'fair',
                'message': '採択の可能性はありますが、申請書の質向上が重要です。',
                'color': 'warning'
            }
        else:
            return {
                'level': 'needs_improvement',
                'message': '申請前に戦略の見直しが必要です。専門家への相談をお勧めします。',
                'color': 'danger'
            }
    
    def _generate_improvement_suggestions(self, probability, user_profile, subsidy):
        suggestions = []
        
        if probability < 70:
            if user_profile.get('support_agency') == 'none':
                suggestions.append('認定支援機関との連携により採択率を大幅に向上できます')
            
            if user_profile.get('experience') == 'none':
                suggestions.append('過去の採択事例を研究し、成功パターンを学習しましょう')
            
            suggestions.append('申請書の事前レビューを複数回実施してください')
            suggestions.append('数値目標を具体的かつ保守的に設定しましょう')
        
        return suggestions
    
    def _calculate_industry_stats(self, industry):
        # 実際の実装では、より詳細なデータベースクエリが必要
        # ここでは簡易的な計算例
        return {
            'adoption_rate': 65.0,  # サンプル値
            'total_applications': 1000,
            'total_adoptions': 650,
            'trend': 'stable',
            'difficulty': 'medium'
        }
    
    def _customize_tips_for_user(self, tips, user_profile):
        # ユーザープロファイルに基づくティップスのカスタマイズ
        return tips
    
    def _default_probability_result(self):
        return {
            'probability': 50.0,
            'assessment': {'level': 'fair', 'message': 'データ不足のため標準確率を表示'},
            'improvement_suggestions': ['データを充実させてより正確な分析を行いましょう'],
            'calculation_details': {}
        }
    
    def _get_industry_analysis(self, subsidy_type):
        # 業種別分析の詳細実装
        return {}
    
    def _analyze_success_factors(self, subsidy_type):
        # 成功要因分析の詳細実装
        return {}
    
    def _predict_trend(self, stats):
        # トレンド予測の詳細実装
        return {'direction': 'stable', 'confidence': 'medium'}
    
    def _generate_user_improvement_advice(self, user, history):
        return ['申請書の質向上に取り組みましょう', '専門家との連携を強化してください']