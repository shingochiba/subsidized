# advisor/admin.py - 修正版
# 現在のモデル構造に対応した管理画面設定

from django.contrib import admin
from .models import (
    SubsidyType, Question, Answer, ConversationHistory, 
    AdoptionStatistics, AdoptionTips
)

# 新しいモデル（マイグレーション後に利用可能）
try:
    from .models import SubsidyPrediction, UserAlert, TrendAnalysis
    NEW_MODELS_AVAILABLE = True
except ImportError:
    NEW_MODELS_AVAILABLE = False

@admin.register(SubsidyType)
class SubsidyTypeAdmin(admin.ModelAdmin):
    """補助金種別の管理画面"""
    
    list_display = [
        'name', 
        'max_amount', 
        'target_business_type',
        'get_requirements_preview'
    ]
    
    # 新しいモデル構造に対応したフィールドのみ使用
    list_filter = [
        'target_business_type',
        'max_amount'
    ]
    
    search_fields = [
        'name', 
        'description', 
        'target_business_type'
    ]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'description', 'target_business_type')
        }),
        ('金額・条件', {
            'fields': ('max_amount', 'requirements')
        }),
    )
    
    # 新機能が利用可能な場合のフィールドを追加
    if NEW_MODELS_AVAILABLE:
        # 新しいフィールドがある場合の設定
        fieldsets += (
            ('予測設定', {
                'fields': ('typical_application_months', 'average_preparation_weeks', 
                          'historical_success_rate', 'application_difficulty'),
                'classes': ('collapse',),
            }),
            ('システム', {
                'fields': ('is_active', 'last_updated'),
                'classes': ('collapse',),
            }),
        )
        
        list_display.extend(['historical_success_rate', 'is_active'])
        list_filter.extend(['is_active', 'application_difficulty'])
        readonly_fields = ['last_updated']
    else:
        readonly_fields = []
    
    def get_requirements_preview(self, obj):
        """要件のプレビュー表示"""
        return obj.requirements[:100] + '...' if len(obj.requirements) > 100 else obj.requirements
    get_requirements_preview.short_description = '要件プレビュー'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """質問の管理画面"""
    
    list_display = [
        'id',
        'get_user_display',
        'get_question_preview',
        'business_type',
        'company_size',
        'created_at'
    ]
    
    list_filter = [
        'business_type',
        'company_size',
        'created_at'
    ]
    
    search_fields = [
        'question_text',
        'session_id',
        'user__username'
    ]
    
    readonly_fields = ['created_at']
    
    def get_user_display(self, obj):
        return obj.user.username if obj.user else f'匿名 ({obj.session_id[:8]})'
    get_user_display.short_description = 'ユーザー'
    
    def get_question_preview(self, obj):
        return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
    get_question_preview.short_description = '質問内容'

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """回答の管理画面"""
    
    list_display = [
        'id',
        'get_question_preview',
        'confidence_score',
        'ai_model_used',
        'created_at'
    ]
    
    list_filter = [
        'ai_model_used',
        'confidence_score',
        'created_at'
    ]
    
    search_fields = [
        'answer_text',
        'question__question_text'
    ]
    
    readonly_fields = ['created_at']
    
    def get_question_preview(self, obj):
        return obj.question.question_text[:50] + '...' if len(obj.question.question_text) > 50 else obj.question.question_text
    get_question_preview.short_description = '対応する質問'

@admin.register(ConversationHistory)
class ConversationHistoryAdmin(admin.ModelAdmin):
    """会話履歴の管理画面"""
    
    list_display = [
        'session_id',
        'get_user_display',
        'message_type',
        'get_content_preview',
        'timestamp'
    ]
    
    list_filter = [
        'message_type',
        'timestamp'
    ]
    
    search_fields = [
        'session_id',
        'content',
        'user__username'
    ]
    
    readonly_fields = ['timestamp']
    
    # 新機能が利用可能な場合のフィールドを追加
    if NEW_MODELS_AVAILABLE:
        list_display.extend(['get_intent_preview'])
        readonly_fields.extend(['intent_analysis', 'user_context', 'metadata'])
        
        fieldsets = (
            ('基本情報', {
                'fields': ('session_id', 'user', 'message_type', 'content')
            }),
            ('分析データ', {
                'fields': ('intent_analysis', 'user_context', 'metadata'),
                'classes': ('collapse',),
            }),
            ('システム', {
                'fields': ('timestamp',),
                'classes': ('collapse',),
            }),
        )
        
        def get_intent_preview(self, obj):
            if hasattr(obj, 'intent_analysis') and obj.intent_analysis:
                return obj.intent_analysis.get('primary_intent', '未分析')
            return '未分析'
        get_intent_preview.short_description = '意図分析'
    
    def get_user_display(self, obj):
        return obj.user.username if obj.user else f'匿名 ({obj.session_id[:8]})'
    get_user_display.short_description = 'ユーザー'
    
    def get_content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    get_content_preview.short_description = 'メッセージ内容'

@admin.register(AdoptionStatistics)
class AdoptionStatisticsAdmin(admin.ModelAdmin):
    """採択統計の管理画面"""
    
    list_display = [
        'subsidy_type',
        'year',
        'round_number',
        'total_applications',
        'total_adoptions',
        'get_adoption_rate'
    ]
    
    list_filter = [
        'year',
        'round_number',
        'subsidy_type'
    ]
    
    search_fields = [
        'subsidy_type__name'
    ]
    
    def get_adoption_rate(self, obj):
        if obj.total_applications > 0:
            rate = (obj.total_adoptions / obj.total_applications) * 100
            return f"{rate:.1f}%"
        return "0%"
    get_adoption_rate.short_description = '採択率'

@admin.register(AdoptionTips)
class AdoptionTipsAdmin(admin.ModelAdmin):
    """採択ティップスの管理画面"""
    
    list_display = [
        'title',
        'subsidy_type',
        'category',
        'importance',
        'get_content_preview'
    ]
    
    list_filter = [
        'subsidy_type',
        'category',
        'importance'
    ]
    
    search_fields = [
        'title',
        'content',
        'subsidy_type__name'
    ]
    
    def get_content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    get_content_preview.short_description = 'コンテンツプレビュー'

# 新しいモデルの管理画面（利用可能な場合のみ）
if NEW_MODELS_AVAILABLE:
    
    @admin.register(SubsidyPrediction)
    class SubsidyPredictionAdmin(admin.ModelAdmin):
        """補助金予測の管理画面"""
        
        list_display = [
            'subsidy_type',
            'predicted_date',
            'confidence_score',
            'get_success_probability',
            'recommendation_priority',
            'model_version'
        ]
        
        list_filter = [
            'predicted_date',
            'confidence_score',
            'model_version',
            'subsidy_type'
        ]
        
        search_fields = [
            'subsidy_type__name'
        ]
        
        readonly_fields = ['created_at']
        
        date_hierarchy = 'predicted_date'
        
        fieldsets = (
            ('予測情報', {
                'fields': ('subsidy_type', 'predicted_date', 'confidence_score')
            }),
            ('詳細データ', {
                'fields': ('estimated_budget', 'preparation_deadline', 
                          'success_probability', 'recommendation_priority')
            }),
            ('分析根拠', {
                'fields': ('prediction_basis',),
                'classes': ('collapse',),
            }),
            ('システム', {
                'fields': ('model_version', 'created_at'),
                'classes': ('collapse',),
            }),
        )
        
        def get_success_probability(self, obj):
            return f"{obj.success_probability * 100:.1f}%"
        get_success_probability.short_description = '成功確率'
    
    @admin.register(UserAlert)
    class UserAlertAdmin(admin.ModelAdmin):
        """ユーザーアラートの管理画面"""
        
        list_display = [
            'user',
            'alert_type',
            'title',
            'priority',
            'is_read',
            'is_dismissed',
            'created_at'
        ]
        
        list_filter = [
            'alert_type',
            'priority',
            'is_read',
            'is_dismissed',
            'created_at'
        ]
        
        search_fields = [
            'user__username',
            'title',
            'message'
        ]
        
        readonly_fields = ['created_at', 'read_at']
        
        fieldsets = (
            ('基本情報', {
                'fields': ('user', 'alert_type', 'title', 'message', 'priority')
            }),
            ('関連情報', {
                'fields': ('related_subsidy', 'action_required', 'deadline')
            }),
            ('ステータス', {
                'fields': ('is_read', 'is_dismissed', 'read_at')
            }),
            ('システム', {
                'fields': ('created_at',),
                'classes': ('collapse',),
            }),
        )
    
    @admin.register(TrendAnalysis)
    class TrendAnalysisAdmin(admin.ModelAdmin):
        """トレンド分析の管理画面"""
        
        list_display = [
            'analysis_date',
            'get_seasonal_peak',
            'get_emerging_count',
            'created_at'
        ]
        
        list_filter = [
            'analysis_date',
            'created_at'
        ]
        
        readonly_fields = ['created_at']
        
        fieldsets = (
            ('基本情報', {
                'fields': ('analysis_date',)
            }),
            ('分析データ', {
                'fields': ('seasonal_patterns', 'budget_trends', 
                          'competition_analysis', 'success_rate_trends', 
                          'emerging_opportunities'),
                'classes': ('collapse',),
            }),
            ('システム', {
                'fields': ('created_at',),
                'classes': ('collapse',),
            }),
        )
        
        def get_seasonal_peak(self, obj):
            if obj.seasonal_patterns and 'peak_months' in obj.seasonal_patterns:
                return ', '.join(obj.seasonal_patterns['peak_months'][:2])
            return '未分析'
        get_seasonal_peak.short_description = 'ピーク月'
        
        def get_emerging_count(self, obj):
            if obj.emerging_opportunities:
                return len(obj.emerging_opportunities)
            return 0
        get_emerging_count.short_description = '新機会数'

# サイト設定
admin.site.site_header = '補助金アドバイザー管理画面'
admin.site.site_title = '補助金アドバイザー'
admin.site.index_title = 'システム管理'

# カスタムアクション
def mark_alerts_as_read(modeladmin, request, queryset):
    """選択されたアラートを既読にする"""
    from django.utils import timezone
    
    updated = queryset.update(is_read=True, read_at=timezone.now())
    modeladmin.message_user(
        request,
        f'{updated}件のアラートを既読にしました。'
    )

mark_alerts_as_read.short_description = "選択されたアラートを既読にする"

# アクションを追加（UserAlertがある場合のみ）
if NEW_MODELS_AVAILABLE and 'UserAlert' in globals():
    UserAlertAdmin.actions = [mark_alerts_as_read]

# 管理画面のカスタマイズ
class CustomAdminSite(admin.AdminSite):
    """カスタム管理画面"""
    
    def index(self, request, extra_context=None):
        """管理画面トップページのカスタマイズ"""
        extra_context = extra_context or {}
        
        # 基本統計
        extra_context['stats'] = {
            'total_subsidies': SubsidyType.objects.count(),
            'total_questions': Question.objects.count(),
            'total_conversations': ConversationHistory.objects.count(),
        }
        
        # 新機能の統計
        if NEW_MODELS_AVAILABLE:
            if SubsidyPrediction:
                extra_context['stats']['total_predictions'] = SubsidyPrediction.objects.count()
            if UserAlert:
                extra_context['stats']['unread_alerts'] = UserAlert.objects.filter(is_read=False).count()
        
        return super().index(request, extra_context)

# カスタム管理サイトの設定は通常のadmin.pyでは不要
# 必要に応じて別途設定可能