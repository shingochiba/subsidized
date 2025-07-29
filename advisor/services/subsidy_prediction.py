# advisor/services/subsidy_prediction.py

from datetime import datetime, date, timedelta
from django.db.models import Q, Avg
from ..models import SubsidyType, SubsidySchedule, SubsidyPrediction, AdoptionStatistics
import calendar

class SubsidyPredictionService:
    """補助金公募予測サービス"""
    
    def get_prediction_calendar(self, year=None, months=6):
        """予測カレンダーを取得"""
        if year is None:
            year = datetime.now().year
        
        start_date = date.today()
        end_date = start_date + timedelta(days=months * 30)
        
        # 既存スケジュール（確定情報）
        confirmed_schedules = SubsidySchedule.objects.filter(
            year=year,
            application_start_date__gte=start_date,
            application_start_date__lte=end_date,
            is_prediction=False
        ).select_related('subsidy_type').order_by('application_start_date')
        
        # 予測データ
        predictions = SubsidyPrediction.objects.filter(
            predicted_year=year,
            predicted_start_date__gte=start_date,
            predicted_start_date__lte=end_date
        ).select_related('subsidy_type').order_by('predicted_start_date')
        
        # 月別にグループ化
        calendar_data = {}
        
        # 確定スケジュールを追加
        for schedule in confirmed_schedules:
            month_key = schedule.application_start_date.strftime('%Y-%m')
            if month_key not in calendar_data:
                calendar_data[month_key] = {
                    'month': schedule.application_start_date.strftime('%Y年%m月'),
                    'confirmed': [],
                    'predicted': []
                }
            
            calendar_data[month_key]['confirmed'].append({
                'subsidy': schedule.subsidy_type,
                'schedule': schedule,
                'type': 'confirmed',
                'start_date': schedule.application_start_date,
                'end_date': schedule.application_end_date,
                'status': schedule.status,
                'days_until': schedule.days_until_start if schedule.is_upcoming else None
            })
        
        # 予測データを追加
        for prediction in predictions:
            month_key = prediction.predicted_start_date.strftime('%Y-%m')
            if month_key not in calendar_data:
                calendar_data[month_key] = {
                    'month': prediction.predicted_start_date.strftime('%Y年%m月'),
                    'confirmed': [],
                    'predicted': []
                }
            
            calendar_data[month_key]['predicted'].append({
                'subsidy': prediction.subsidy_type,
                'prediction': prediction,
                'type': 'predicted',
                'start_date': prediction.predicted_start_date,
                'end_date': prediction.predicted_end_date,
                'confidence': prediction.confidence_score,
                'probability': prediction.probability_percentage,
                'days_until': (prediction.predicted_start_date - date.today()).days if prediction.predicted_start_date > date.today() else None
            })
        
        return dict(sorted(calendar_data.items()))
    
    def generate_predictions_for_year(self, year=None):
        """年度の予測を生成"""
        if year is None:
            year = datetime.now().year
        
        subsidies = SubsidyType.objects.all()
        predictions_created = 0
        
        for subsidy in subsidies:
            created_count = self._generate_subsidy_predictions(subsidy, year)
            predictions_created += created_count
        
        return predictions_created
    
    def _generate_subsidy_predictions(self, subsidy, year):
        """特定補助金の予測を生成"""
        # 過去3年のスケジュールを分析
        historical_schedules = SubsidySchedule.objects.filter(
            subsidy_type=subsidy,
            year__in=[year-3, year-2, year-1]
        ).order_by('year', 'round_number')
        
        if not historical_schedules.exists():
            return 0
        
        # パターン分析
        schedule_patterns = self._analyze_schedule_patterns(historical_schedules)
        
        predictions_created = 0
        
        for pattern in schedule_patterns:
            # 既存の予測があるかチェック
            existing_prediction = SubsidyPrediction.objects.filter(
                subsidy_type=subsidy,
                predicted_year=year,
                predicted_round=pattern['round']
            ).first()
            
            if not existing_prediction:
                # 新しい予測を作成
                prediction = self._create_prediction_from_pattern(subsidy, year, pattern)
                if prediction:
                    predictions_created += 1
        
        return predictions_created
    
    def _analyze_schedule_patterns(self, schedules):
        """スケジュールパターンを分析"""
        patterns = {}
        
        for schedule in schedules:
            round_key = schedule.round_number
            
            if round_key not in patterns:
                patterns[round_key] = {
                    'round': round_key,
                    'dates': [],
                    'durations': [],
                    'months': []
                }
            
            patterns[round_key]['dates'].append(schedule.application_start_date)
            patterns[round_key]['months'].append(schedule.application_start_date.month)
            
            if schedule.application_end_date:
                duration = (schedule.application_end_date - schedule.application_start_date).days
                patterns[round_key]['durations'].append(duration)
        
        # パターンから予測を計算
        predicted_patterns = []
        
        for round_num, data in patterns.items():
            if len(data['dates']) >= 2:  # 最低2年のデータが必要
                # 最頻月を計算
                most_common_month = max(set(data['months']), key=data['months'].count)
                
                # 平均日数を計算
                avg_duration = sum(data['durations']) / len(data['durations']) if data['durations'] else 30
                
                # 昨年の日付を基準に予測
                last_year_date = max(data['dates'])
                
                predicted_patterns.append({
                    'round': round_num,
                    'predicted_month': most_common_month,
                    'avg_duration': int(avg_duration),
                    'last_year_date': last_year_date,
                    'confidence': self._calculate_pattern_confidence(data),
                    'frequency': len(data['dates'])
                })
        
        return predicted_patterns
    
    def _create_prediction_from_pattern(self, subsidy, year, pattern):
        """パターンから予測を作成"""
        # 予測開始日を計算
        predicted_month = pattern['predicted_month']
        
        # 昨年の同月の日付を基準に予測
        try:
            if pattern['last_year_date']:
                # 昨年の日付に1年を加算
                predicted_start = date(year, predicted_month, pattern['last_year_date'].day)
            else:
                # デフォルトで月の初旬
                predicted_start = date(year, predicted_month, 15)
                
        except ValueError:
            # 2月29日などの場合の対応
            predicted_start = date(year, predicted_month, 28)
        
        # 既に過ぎている場合は次回に調整
        if predicted_start < date.today():
            predicted_start = predicted_start.replace(year=year+1)
        
        # 終了日を計算
        predicted_end = predicted_start + timedelta(days=pattern['avg_duration'])
        
        # 発表日を計算（通常2-3ヶ月後）
        predicted_announcement = predicted_end + timedelta(days=75)
        
        # 信頼度を計算
        confidence = pattern['confidence']
        probability = min(95, 60 + pattern['frequency'] * 10)  # 実績回数に基づく確率
        
        # 予測を作成
        prediction = SubsidyPrediction.objects.create(
            subsidy_type=subsidy,
            predicted_year=year,
            predicted_round=pattern['round'],
            predicted_start_date=predicted_start,
            predicted_end_date=predicted_end,
            predicted_announcement_date=predicted_announcement,
            prediction_basis='historical',
            confidence_score=confidence,
            probability_percentage=probability,
            prediction_notes=f"過去{pattern['frequency']}年の実績に基づく予測",
            historical_data_years=pattern['frequency'],
            last_year_date=pattern['last_year_date']
        )
        
        return prediction
    
    def _calculate_pattern_confidence(self, pattern_data):
        """パターンの信頼度を計算"""
        # データ数が多いほど信頼度が高い
        data_count = len(pattern_data['dates'])
        base_confidence = min(90, 40 + data_count * 15)
        
        # 月の一貫性をチェック
        months = pattern_data['months']
        if months:
            most_common_count = months.count(max(set(months), key=months.count))
            consistency_bonus = (most_common_count / len(months)) * 20
            base_confidence += consistency_bonus
        
        return int(min(95, base_confidence))
    
    def get_upcoming_subsidies(self, days=30):
        """今後指定日数以内の補助金を取得"""
        end_date = date.today() + timedelta(days=days)
        
        # 確定スケジュール
        confirmed = SubsidySchedule.objects.filter(
            application_start_date__gte=date.today(),
            application_start_date__lte=end_date,
            is_prediction=False
        ).select_related('subsidy_type').order_by('application_start_date')
        
        # 予測データ
        predicted = SubsidyPrediction.objects.filter(
            predicted_start_date__gte=date.today(),
            predicted_start_date__lte=end_date,
            confidence_score__gte=70  # 信頼度70%以上のみ
        ).select_related('subsidy_type').order_by('predicted_start_date')
        
        upcoming = []
        
        # 確定データを追加
        for schedule in confirmed:
            upcoming.append({
                'type': 'confirmed',
                'subsidy': schedule.subsidy_type,
                'date': schedule.application_start_date,
                'days_until': (schedule.application_start_date - date.today()).days,
                'confidence': 100,
                'schedule': schedule
            })
        
        # 予測データを追加
        for prediction in predicted:
            upcoming.append({
                'type': 'predicted',
                'subsidy': prediction.subsidy_type,
                'date': prediction.predicted_start_date,
                'days_until': (prediction.predicted_start_date - date.today()).days,
                'confidence': prediction.confidence_score,
                'prediction': prediction
            })
        
        # 日付順でソート
        upcoming.sort(key=lambda x: x['date'])
        
        return upcoming
    
    def get_subsidy_trend_analysis(self, subsidy_id):
        """特定補助金のトレンド分析"""
        try:
            subsidy = SubsidyType.objects.get(id=subsidy_id)
        except SubsidyType.DoesNotExist:
            return None
        
        # 過去5年のスケジュール
        current_year = datetime.now().year
        schedules = SubsidySchedule.objects.filter(
            subsidy_type=subsidy,
            year__gte=current_year-5
        ).order_by('year', 'round_number')
        
        # 年度別統計
        yearly_stats = {}
        for schedule in schedules:
            year = schedule.year
            if year not in yearly_stats:
                yearly_stats[year] = {
                    'rounds': 0,
                    'months': [],
                    'total_days': 0
                }
            
            yearly_stats[year]['rounds'] += 1
            yearly_stats[year]['months'].append(schedule.application_start_date.month)
            
            if schedule.application_end_date:
                duration = (schedule.application_end_date - schedule.application_start_date).days
                yearly_stats[year]['total_days'] += duration
        
        # トレンド分析
        trend_analysis = {
            'subsidy': subsidy,
            'yearly_data': yearly_stats,
            'patterns': self._identify_trends(yearly_stats),
            'next_prediction': self._get_next_prediction(subsidy)
        }
        
        return trend_analysis
    
    def _identify_trends(self, yearly_stats):
        """トレンドを特定"""
        if len(yearly_stats) < 2:
            return {"trend": "insufficient_data"}
        
        years = sorted(yearly_stats.keys())
        rounds_per_year = [yearly_stats[year]['rounds'] for year in years]
        
        # 公募回数のトレンド
        if len(rounds_per_year) >= 3:
            recent_avg = sum(rounds_per_year[-2:]) / 2
            older_avg = sum(rounds_per_year[:-2]) / (len(rounds_per_year) - 2)
            
            if recent_avg > older_avg:
                trend = "increasing"
            elif recent_avg < older_avg:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # 最頻月の特定
        all_months = []
        for year_data in yearly_stats.values():
            all_months.extend(year_data['months'])
        
        if all_months:
            most_common_month = max(set(all_months), key=all_months.count)
            month_names = ['', '1月', '2月', '3月', '4月', '5月', '6月', 
                          '7月', '8月', '9月', '10月', '11月', '12月']
            common_month_name = month_names[most_common_month]
        else:
            common_month_name = "不明"
        
        return {
            "trend": trend,
            "most_common_month": common_month_name,
            "average_rounds_per_year": sum(rounds_per_year) / len(rounds_per_year) if rounds_per_year else 0
        }
    
    def _get_next_prediction(self, subsidy):
        """次回の予測を取得"""
        next_prediction = SubsidyPrediction.objects.filter(
            subsidy_type=subsidy,
            predicted_start_date__gte=date.today()
        ).order_by('predicted_start_date').first()
        
        return next_prediction