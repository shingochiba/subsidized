import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from ..models import SubsidyType, AdoptionStatistics

class SubsidyPredictionService:
    """AIによる補助金公募予測とスケジュール管理"""
    
    def __init__(self):
        self.prediction_cache = {}
        
    def predict_next_opportunities(self, months_ahead=12):
        """
        今後12ヶ月の補助金公募スケジュールを予測
        """
        
        predictions = []
        current_date = timezone.now().date()
        
        # アクティブな補助金を取得
        subsidies = SubsidyType.objects.filter(is_active=True)
        
        for month_offset in range(1, months_ahead + 1):
            target_date = current_date + timedelta(days=30 * month_offset)
            
            month_predictions = self._predict_for_month(target_date, subsidies)
            predictions.extend(month_predictions)
        
        return self._format_prediction_results(predictions)
    
    def _predict_for_month(self, target_date, subsidies):
        """特定月の公募予測"""
        month = target_date.month
        predictions = []
        
        for subsidy in subsidies:
            # 申請月の判定
            typical_months = getattr(subsidy, 'typical_application_months', None)
            if not typical_months:
                typical_months = self._get_default_application_months(subsidy)
            
            if month in typical_months:
                prediction = {
                    'subsidy_id': subsidy.id,
                    'subsidy_name': subsidy.name,
                    'predicted_date': target_date,
                    'confidence': self._calculate_prediction_confidence(subsidy, target_date),
                    'estimated_budget': subsidy.max_amount,
                    'preparation_deadline': target_date - timedelta(
                        weeks=getattr(subsidy, 'average_preparation_weeks', 8)
                    ),
                    'success_probability': getattr(subsidy, 'historical_success_rate', 0.25),
                    'recommendation_priority': self._calculate_priority_score(subsidy)
                }
                predictions.append(prediction)
        
        return predictions
    
    def _get_default_application_months(self, subsidy):
        """デフォルトの申請月を取得"""
        if "事業再構築" in subsidy.name:
            return [1, 4, 7, 10]  # 年4回
        elif "ものづくり" in subsidy.name:
            return [2, 6, 10]     # 年3回
        elif "小規模事業者" in subsidy.name:
            return [3, 6, 9, 12]  # 年4回
        elif "IT導入" in subsidy.name:
            return [1, 7]         # 年2回
        else:
            return [4, 9]         # 年2回（デフォルト）
    
    def _calculate_prediction_confidence(self, subsidy, target_date):
        """予測信頼度の計算"""
        base_confidence = 0.7
        
        # 過去の実績による調整
        success_rate = getattr(subsidy, 'historical_success_rate', 0.25)
        if success_rate > 0.2:
            base_confidence += 0.1
        
        # 季節性による調整
        current_month = target_date.month
        if current_month in [1, 4, 7, 10]:  # 四半期始まり
            base_confidence += 0.1
        
        return min(base_confidence, 0.95)
    
    def _calculate_priority_score(self, subsidy):
        """推奨優先度スコアの計算"""
        score = 0.0
        
        # 成功率
        success_rate = getattr(subsidy, 'historical_success_rate', 0.25)
        score += success_rate * 0.4
        
        # 予算規模
        if subsidy.max_amount > 1000:  # 1000万円以上
            score += 0.3
        elif subsidy.max_amount > 500:  # 500万円以上
            score += 0.2
        else:
            score += 0.1
        
        # 申請難易度（逆算）
        difficulty = getattr(subsidy, 'application_difficulty', 3)
        score += (5 - difficulty) * 0.1
        
        # 準備時間
        prep_weeks = getattr(subsidy, 'average_preparation_weeks', 8)
        if prep_weeks <= 4:
            score += 0.2
        elif prep_weeks <= 8:
            score += 0.1
        
        return min(score, 1.0)
    
    def _format_prediction_results(self, predictions):
        """予測結果のフォーマット"""
        return sorted(predictions, key=lambda x: x['predicted_date'])
    
    def generate_prediction_calendar(self):
        """予測カレンダーの生成"""
        predictions = self.predict_next_opportunities()
        
        calendar_data = {}
        
        for pred in predictions:
            month_key = pred['predicted_date'].strftime('%Y-%m')
            
            if month_key not in calendar_data:
                calendar_data[month_key] = {
                    'month': pred['predicted_date'].strftime('%Y年%m月'),
                    'opportunities': [],
                    'total_opportunities': 0,
                    'high_priority_count': 0
                }
            
            calendar_data[month_key]['opportunities'].append(pred)
            calendar_data[month_key]['total_opportunities'] += 1
            
            if pred['recommendation_priority'] >= 0.7:
                calendar_data[month_key]['high_priority_count'] += 1
        
        return calendar_data
    
    def setup_alert_system(self, user_preferences):
        """アラート機能の設定"""
        alerts = []
        predictions = self.predict_next_opportunities(months_ahead=6)
        
        for pred in predictions:
            # 準備期限が近い場合のアラート
            days_to_prep_deadline = (pred['preparation_deadline'] - timezone.now().date()).days
            
            if days_to_prep_deadline <= 30 and pred['confidence'] >= 0.6:
                alerts.append({
                    'type': 'preparation_deadline',
                    'priority': 'high' if days_to_prep_deadline <= 14 else 'medium',
                    'message': f"{pred['subsidy_name']}の準備期限まで{days_to_prep_deadline}日です",
                    'subsidy_name': pred['subsidy_name'],
                    'deadline': pred['preparation_deadline'],
                    'action_required': '申請準備を開始してください'
                })
            
            # 高確率案件のアラート
            if pred['confidence'] >= 0.8 and pred['success_probability'] >= 0.3:
                alerts.append({
                    'type': 'high_opportunity',
                    'priority': 'medium',
                    'message': f"{pred['subsidy_name']}の公募が予想されます（信頼度: {pred['confidence']:.0%}）",
                    'subsidy_name': pred['subsidy_name'],
                    'predicted_date': pred['predicted_date'],
                    'action_required': '詳細情報の確認をお勧めします'
                })
        
        return sorted(alerts, key=lambda x: x['priority'] == 'high', reverse=True)
    
    def analyze_subsidy_trends(self):
        """補助金トレンド分析"""
        
        trends = {
            'seasonal_patterns': self._analyze_seasonal_patterns(),
            'budget_trends': self._analyze_budget_trends(),
            'competition_analysis': self._analyze_competition_trends(),
            'success_rate_trends': self._analyze_success_rate_trends(),
            'emerging_opportunities': self._identify_emerging_opportunities()
        }
        
        return trends
    
    def _analyze_seasonal_patterns(self):
        """季節パターンの分析"""
        monthly_activity = {month: 0 for month in range(1, 13)}
        
        subsidies = SubsidyType.objects.filter(is_active=True)
        for subsidy in subsidies:
            typical_months = getattr(subsidy, 'typical_application_months', None)
            if not typical_months:
                typical_months = self._get_default_application_months(subsidy)
            
            for month in typical_months:
                monthly_activity[month] += 1
        
        # 活発な月の特定
        peak_months = sorted(monthly_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'monthly_distribution': monthly_activity,
            'peak_months': [f"{month}月" for month, _ in peak_months],
            'peak_activity_score': sum(count for _, count in peak_months) / max(sum(monthly_activity.values()), 1)
        }
    
    def _analyze_budget_trends(self):
        """予算トレンドの分析"""
        subsidies = SubsidyType.objects.filter(is_active=True)
        
        budget_ranges = {
            '100万円以下': 0,
            '100-500万円': 0,
            '500-1000万円': 0,
            '1000万円以上': 0
        }
        
        for subsidy in subsidies:
            amount = subsidy.max_amount
            if amount <= 100:
                budget_ranges['100万円以下'] += 1
            elif amount <= 500:
                budget_ranges['100-500万円'] += 1
            elif amount <= 1000:
                budget_ranges['500-1000万円'] += 1
            else:
                budget_ranges['1000万円以上'] += 1
        
        return budget_ranges
    
    def _analyze_competition_trends(self):
        """競合分析"""
        return {
            'low_competition': ['小規模事業者持続化補助金'],
            'medium_competition': ['IT導入補助金', 'ものづくり補助金'],
            'high_competition': ['事業再構築補助金']
        }
    
    def _analyze_success_rate_trends(self):
        """成功率トレンド"""
        subsidies = SubsidyType.objects.filter(is_active=True)
        
        success_rates = {}
        for subsidy in subsidies:
            rate = getattr(subsidy, 'historical_success_rate', 0.25)
            success_rates[subsidy.name] = f"{rate:.0%}"
        
        return success_rates
    
    def _identify_emerging_opportunities(self):
        """新機会の特定"""
        return [
            'デジタル化支援補助金',
            'カーボンニュートラル補助金',
            'スタートアップ支援制度'
        ]