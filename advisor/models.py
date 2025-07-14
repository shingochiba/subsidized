from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime

class SubsidyType(models.Model):
    name = models.CharField(max_length=255, verbose_name="補助金名")
    description = models.TextField(verbose_name="説明")
    max_amount = models.IntegerField(verbose_name="最大金額（万円）")
    target_business_type = models.CharField(max_length=255, verbose_name="対象事業種別")
    requirements = models.TextField(verbose_name="申請要件")
    
    # 新機能: 予測関連フィールド
    typical_application_months = models.JSONField(
        default=list, 
        verbose_name="通常の申請月",
        help_text="例: [1, 4, 7, 10]"
    )
    average_preparation_weeks = models.IntegerField(
        default=8, 
        verbose_name="平均準備期間（週）"
    )
    historical_success_rate = models.FloatField(
        default=0.25, 
        verbose_name="過去の成功率"
    )
    application_difficulty = models.IntegerField(
        default=3, 
        verbose_name="申請難易度（1-5）",
        choices=[(i, f"レベル{i}") for i in range(1, 6)]
    )
    
    # メタデータ
    is_active = models.BooleanField(default=True, verbose_name="アクティブ")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="最終更新")
    
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
    """強化された会話履歴管理"""
    session_id = models.CharField(max_length=255, verbose_name="セッションID")
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="ユーザー"
    )
    message_type = models.CharField(
        max_length=20, 
        choices=[
            ('user', 'ユーザー'),
            ('assistant', 'アシスタント'),
            ('system', 'システム')
        ],
        verbose_name="メッセージ種別"
    )
    content = models.TextField(verbose_name="メッセージ内容")
    
    # 新機能: メタデータ
    metadata = models.JSONField(
        default=dict, 
        verbose_name="メタデータ",
        help_text="信頼度、推奨補助金、使用モデル等"
    )
    
    # 分析用フィールド
    intent_analysis = models.JSONField(
        default=dict, 
        verbose_name="意図分析結果"
    )
    user_context = models.JSONField(
        default=dict, 
        verbose_name="ユーザーコンテキスト"
    )
    
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="タイムスタンプ")
    
    class Meta:
        verbose_name = "会話履歴"
        verbose_name_plural = "会話履歴"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.session_id} - {self.message_type} - {self.timestamp}"




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
    """補助金予測データ"""
    subsidy_type = models.ForeignKey(
        SubsidyType, 
        on_delete=models.CASCADE, 
        verbose_name="補助金種別"
    )
    predicted_date = models.DateField(verbose_name="予測公募日")
    confidence_score = models.FloatField(
        verbose_name="信頼度スコア",
        help_text="0.0-1.0の範囲"
    )
    
    # 予測の詳細
    estimated_budget = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="予測予算（万円）"
    )
    preparation_deadline = models.DateField(verbose_name="準備期限")
    success_probability = models.FloatField(
        default=0.25, 
        verbose_name="成功確率"
    )
    recommendation_priority = models.FloatField(
        default=0.5, 
        verbose_name="推奨優先度"
    )
    
    # 予測根拠
    prediction_basis = models.JSONField(
        default=dict, 
        verbose_name="予測根拠",
        help_text="季節性、過去実績等の分析結果"
    )
    
    # システム管理
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    model_version = models.CharField(
        max_length=50, 
        default="v1.0", 
        verbose_name="予測モデルバージョン"
    )
    
    class Meta:
        verbose_name = "補助金予測"
        verbose_name_plural = "補助金予測"
        unique_together = ['subsidy_type', 'predicted_date']
        ordering = ['predicted_date']
    
    def __str__(self):
        return f"{self.subsidy_type.name} - {self.predicted_date}"
    
class UserAlert(models.Model):
    """ユーザーアラート管理"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="ユーザー"
    )
    alert_type = models.CharField(
        max_length=50,
        choices=[
            ('preparation_deadline', '準備期限'),
            ('high_opportunity', '高確率案件'),
            ('new_subsidy', '新規補助金'),
            ('trend_change', 'トレンド変化')
        ],
        verbose_name="アラート種別"
    )
    
    # アラート内容
    title = models.CharField(max_length=255, verbose_name="タイトル")
    message = models.TextField(verbose_name="メッセージ")
    priority = models.CharField(
        max_length=20,
        choices=[
            ('high', '高'),
            ('medium', '中'),
            ('low', '低')
        ],
        default='medium',
        verbose_name="優先度"
    )
    
    # 関連データ
    related_subsidy = models.ForeignKey(
        SubsidyType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="関連補助金"
    )
    action_required = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="必要なアクション"
    )
    deadline = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="期限"
    )
    
    # ステータス管理
    is_read = models.BooleanField(default=False, verbose_name="既読")
    is_dismissed = models.BooleanField(default=False, verbose_name="非表示")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="既読日時")
    
    class Meta:
        verbose_name = "ユーザーアラート"
        verbose_name_plural = "ユーザーアラート"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class TrendAnalysis(models.Model):
    """トレンド分析データ"""
    analysis_date = models.DateField(verbose_name="分析日")
    
    # 季節パターン
    seasonal_patterns = models.JSONField(
        default=dict, 
        verbose_name="季節パターン"
    )
    
    # 予算トレンド
    budget_trends = models.JSONField(
        default=dict, 
        verbose_name="予算トレンド"
    )
    
    # 競合分析
    competition_analysis = models.JSONField(
        default=dict, 
        verbose_name="競合分析"
    )
    
    # 成功率トレンド
    success_rate_trends = models.JSONField(
        default=dict, 
        verbose_name="成功率トレンド"
    )
    
    # 新機会の特定
    emerging_opportunities = models.JSONField(
        default=list, 
        verbose_name="新たな機会"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    
    class Meta:
        verbose_name = "トレンド分析"
        verbose_name_plural = "トレンド分析"
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"トレンド分析 - {self.analysis_date}"