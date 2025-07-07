from django.db import models
from django.contrib.auth.models import User

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