from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime

class SubsidyType(models.Model):
    """補助金の種類"""
    name = models.CharField(max_length=200, verbose_name="補助金名")
    description = models.TextField(verbose_name="概要")
    target_business = models.TextField(verbose_name="対象事業")
    application_period = models.CharField(max_length=100, verbose_name="申請期間")
    max_amount = models.IntegerField(verbose_name="最大補助額")
    subsidy_rate = models.CharField(max_length=50, verbose_name="補助率")
    requirements = models.TextField(verbose_name="申請要件")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "補助金種別"
        verbose_name_plural = "補助金種別"

    def __str__(self):
        return self.name

class Question(models.Model):
    """ユーザーからの質問"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, verbose_name="セッションID")
    question_text = models.TextField(verbose_name="質問内容")
    business_type = models.CharField(max_length=100, blank=True, verbose_name="事業種別")
    company_size = models.CharField(max_length=50, blank=True, verbose_name="企業規模")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "質問"
        verbose_name_plural = "質問"

    def __str__(self):
        return f"{self.question_text[:50]}..."

class Answer(models.Model):
    """AIからの回答"""
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(verbose_name="回答内容")
    recommended_subsidies = models.ManyToManyField(SubsidyType, blank=True)
    confidence_score = models.FloatField(default=0.0, verbose_name="信頼度スコア")
    ai_model_used = models.CharField(max_length=50, verbose_name="使用AIモデル")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "回答"
        verbose_name_plural = "回答"

    def __str__(self):
        return f"回答: {self.question.question_text[:30]}..."

class ConversationHistory(models.Model):
    """会話履歴"""
    session_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message_type = models.CharField(max_length=10, choices=[('user', 'User'), ('ai', 'AI')])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = "会話履歴"
        verbose_name_plural = "会話履歴"


class AdoptionStatistics(models.Model):
    """補助金の採択統計データ"""
    subsidy_type = models.ForeignKey('SubsidyType', on_delete=models.CASCADE, related_name='statistics')
    year = models.IntegerField(verbose_name="年度")
    round_number = models.IntegerField(verbose_name="回次", default=1)
    
    # 統計データ
    total_applications = models.IntegerField(verbose_name="総申請数")
    total_adoptions = models.IntegerField(verbose_name="総採択数")
    adoption_rate = models.FloatField(verbose_name="採択率", validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # 規模別統計
    small_business_applications = models.IntegerField(verbose_name="小規模事業者申請数", default=0)
    small_business_adoptions = models.IntegerField(verbose_name="小規模事業者採択数", default=0)
    medium_business_applications = models.IntegerField(verbose_name="中小企業申請数", default=0)
    medium_business_adoptions = models.IntegerField(verbose_name="中小企業採択数", default=0)
    
    # 業種別統計（JSON形式で保存）
    industry_statistics = models.JSONField(verbose_name="業種別統計", default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "採択統計"
        verbose_name_plural = "採択統計"
        unique_together = ['subsidy_type', 'year', 'round_number']
        ordering = ['-year', '-round_number']

    def __str__(self):
        return f"{self.subsidy_type.name} {self.year}年度 第{self.round_number}回 ({self.adoption_rate}%)"

    @property
    def small_business_adoption_rate(self):
        """小規模事業者の採択率"""
        if self.small_business_applications > 0:
            return (self.small_business_adoptions / self.small_business_applications) * 100
        return 0

    @property
    def medium_business_adoption_rate(self):
        """中小企業の採択率"""
        if self.medium_business_applications > 0:
            return (self.medium_business_adoptions / self.medium_business_applications) * 100
        return 0


class AdoptionTips(models.Model):
    """採択率向上のためのティップス"""
    subsidy_type = models.ForeignKey('SubsidyType', on_delete=models.CASCADE, related_name='adoption_tips')
    category = models.CharField(max_length=50, verbose_name="カテゴリ", choices=[
        ('preparation', '事前準備'),
        ('application', '申請書作成'),
        ('documents', '必要書類'),
        ('strategy', '戦略・ポイント'),
        ('common_mistakes', 'よくある失敗'),
        ('success_factors', '成功要因'),
    ])
    title = models.CharField(max_length=200, verbose_name="タイトル")
    content = models.TextField(verbose_name="内容")
    importance = models.IntegerField(verbose_name="重要度", choices=[
        (1, '低'),
        (2, '中'),
        (3, '高'),
        (4, '最重要'),
    ], default=2)
    
    # 効果的な時期
    effective_timing = models.CharField(max_length=100, verbose_name="効果的な時期", blank=True)
    
    # 参考URL
    reference_url = models.URLField(verbose_name="参考URL", blank=True)
    
    # 実際の成功事例かどうか
    is_success_case = models.BooleanField(verbose_name="成功事例", default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "採択ティップス"
        verbose_name_plural = "採択ティップス"
        ordering = ['-importance', 'category']

    def __str__(self):
        return f"{self.subsidy_type.name} - {self.title}"


class UserApplicationHistory(models.Model):
    """ユーザーの申請履歴"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='application_history')
    subsidy_type = models.ForeignKey('SubsidyType', on_delete=models.CASCADE)
    
    # 申請情報
    application_date = models.DateField(verbose_name="申請日")
    application_round = models.IntegerField(verbose_name="申請回次", default=1)
    
    # 結果
    status = models.CharField(max_length=20, verbose_name="ステータス", choices=[
        ('preparing', '準備中'),
        ('submitted', '申請済み'),
        ('under_review', '審査中'),
        ('adopted', '採択'),
        ('rejected', '不採択'),
        ('withdrawn', '取り下げ'),
    ], default='preparing')
    
    result_date = models.DateField(verbose_name="結果発表日", null=True, blank=True)
    feedback = models.TextField(verbose_name="フィードバック・コメント", blank=True)
    
    # 申請時の企業情報
    business_type_at_application = models.CharField(max_length=100, verbose_name="申請時事業種別")
    company_size_at_application = models.CharField(max_length=50, verbose_name="申請時企業規模")
    requested_amount = models.IntegerField(verbose_name="申請金額", null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "申請履歴"
        verbose_name_plural = "申請履歴"
        ordering = ['-application_date']

    def __str__(self):
        return f"{self.user.username} - {self.subsidy_type.name} ({self.status})"


class ApplicationScoreCard(models.Model):
    """申請の採択可能性スコアカード"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subsidy_type = models.ForeignKey('SubsidyType', on_delete=models.CASCADE)
    
    # スコア要素
    business_plan_score = models.IntegerField(verbose_name="事業計画スコア", validators=[MinValueValidator(0), MaxValueValidator(100)])
    innovation_score = models.IntegerField(verbose_name="革新性スコア", validators=[MinValueValidator(0), MaxValueValidator(100)])
    feasibility_score = models.IntegerField(verbose_name="実現可能性スコア", validators=[MinValueValidator(0), MaxValueValidator(100)])
    market_potential_score = models.IntegerField(verbose_name="市場性スコア", validators=[MinValueValidator(0), MaxValueValidator(100)])
    financial_health_score = models.IntegerField(verbose_name="財務健全性スコア", validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # 総合スコア
    total_score = models.IntegerField(verbose_name="総合スコア", validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # 改善提案
    improvement_suggestions = models.JSONField(verbose_name="改善提案", default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "採択スコアカード"
        verbose_name_plural = "採択スコアカード"
        unique_together = ['user', 'subsidy_type']

    def __str__(self):
        return f"{self.user.username} - {self.subsidy_type.name} (スコア: {self.total_score})"
    



class SubsidySchedule(models.Model):
    """補助金の公募スケジュール"""
    subsidy_type = models.ForeignKey('SubsidyType', on_delete=models.CASCADE, related_name='schedules')
    year = models.IntegerField(verbose_name="年度")
    round_number = models.IntegerField(verbose_name="公募回次", default=1)
    
    # 公募期間
    application_start_date = models.DateField(verbose_name="申請開始日")
    application_end_date = models.DateField(verbose_name="申請締切日")
    
    # 結果発表
    result_announcement_date = models.DateField(verbose_name="結果発表予定日", null=True, blank=True)
    
    # 事業実施期間
    project_start_date = models.DateField(verbose_name="事業開始日", null=True, blank=True)
    project_end_date = models.DateField(verbose_name="事業終了日", null=True, blank=True)
    
    # 予算情報
    total_budget = models.BigIntegerField(verbose_name="総予算額", null=True, blank=True)
    allocated_budget = models.BigIntegerField(verbose_name="配分予算額", null=True, blank=True)
    
    # ステータス
    STATUS_CHOICES = [
        ('scheduled', '予定'),
        ('active', '公募中'),
        ('closed', '締切済み'),
        ('completed', '完了'),
        ('cancelled', '中止'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="ステータス")
    
    # メタ情報
    notes = models.TextField(verbose_name="備考", blank=True)
    is_prediction = models.BooleanField(verbose_name="予測データ", default=False)
    confidence_level = models.IntegerField(
        verbose_name="予測信頼度", 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=50,
        help_text="予測の信頼度（0-100%）"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "補助金スケジュール"
        verbose_name_plural = "補助金スケジュール"
        unique_together = ['subsidy_type', 'year', 'round_number']
        ordering = ['year', 'application_start_date', 'round_number']

    def __str__(self):
        return f"{self.subsidy_type.name} {self.year}年度第{self.round_number}回"

    @property
    def is_active(self):
        """現在公募中かどうか"""
        today = datetime.date.today()
        return (self.application_start_date <= today <= self.application_end_date 
                and self.status == 'active')

    @property
    def is_upcoming(self):
        """今後予定されているかどうか"""
        today = datetime.date.today()
        return self.application_start_date > today

    @property
    def days_until_start(self):
        """開始までの日数"""
        if self.is_upcoming:
            return (self.application_start_date - datetime.date.today()).days
        return 0

    @property
    def days_until_deadline(self):
        """締切までの日数"""
        if self.is_active:
            return (self.application_end_date - datetime.date.today()).days
        return 0

class SubsidyPrediction(models.Model):
    """補助金公募予測"""
    subsidy_type = models.ForeignKey('SubsidyType', on_delete=models.CASCADE, related_name='predictions')
    predicted_year = models.IntegerField(verbose_name="予測年度")
    predicted_round = models.IntegerField(verbose_name="予測回次", default=1)
    
    # 予測日程
    predicted_start_date = models.DateField(verbose_name="予測開始日")
    predicted_end_date = models.DateField(verbose_name="予測締切日")
    predicted_announcement_date = models.DateField(verbose_name="予測発表日", null=True, blank=True)
    
    # 予測根拠
    PREDICTION_BASIS_CHOICES = [
        ('historical', '過去実績'),
        ('official_announcement', '公式発表'),
        ('budget_cycle', '予算サイクル'),
        ('policy_change', '政策変更'),
        ('trend_analysis', 'トレンド分析'),
    ]
    prediction_basis = models.CharField(
        max_length=30, 
        choices=PREDICTION_BASIS_CHOICES, 
        default='historical',
        verbose_name="予測根拠"
    )
    
    # 信頼度と確率
    confidence_score = models.IntegerField(
        verbose_name="信頼度スコア", 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=70
    )
    
    probability_percentage = models.FloatField(
        verbose_name="実施確率", 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=80.0
    )
    
    # 予測詳細
    prediction_notes = models.TextField(verbose_name="予測詳細", blank=True)
    risk_factors = models.TextField(verbose_name="リスク要因", blank=True)
    
    # 参考データ
    historical_data_years = models.IntegerField(verbose_name="参考年数", default=3)
    last_year_date = models.DateField(verbose_name="昨年実施日", null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "補助金予測"
        verbose_name_plural = "補助金予測"
        unique_together = ['subsidy_type', 'predicted_year', 'predicted_round']
        ordering = ['predicted_start_date']

    def __str__(self):
        return f"{self.subsidy_type.name} {self.predicted_year}年度第{self.predicted_round}回 予測"

    @property
    def confidence_level_display(self):
        """信頼度の表示"""
        if self.confidence_score >= 90:
            return "非常に高い"
        elif self.confidence_score >= 70:
            return "高い"
        elif self.confidence_score >= 50:
            return "中程度"
        else:
            return "低い"

    @property
    def status_color(self):
        """ステータス表示用の色"""
        if self.confidence_score >= 80:
            return "success"
        elif self.confidence_score >= 60:
            return "primary"
        elif self.confidence_score >= 40:
            return "warning"
        else:
            return "secondary"