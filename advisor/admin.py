# advisor/admin.py に追加する管理画面設定

from django.contrib import admin
from .models import (
    SubsidyType, Question, Answer, ConversationHistory,
    AdoptionStatistics, AdoptionTips, UserApplicationHistory, ApplicationScoreCard
)

# 既存の管理画面設定
@admin.register(SubsidyType)
class SubsidyTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_amount', 'subsidy_rate', 'application_period']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description', 'target_business']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'user', 'business_type', 'created_at']
    list_filter = ['business_type', 'company_size', 'created_at']
    search_fields = ['question_text', 'user__username']
    readonly_fields = ['created_at']
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = "質問内容"

# 🆕 採択統計の管理画面
@admin.register(AdoptionStatistics)
class AdoptionStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        'subsidy_type', 'year', 'round_number', 'adoption_rate', 
        'total_applications', 'total_adoptions'
    ]
    list_filter = ['year', 'subsidy_type', 'round_number']
    search_fields = ['subsidy_type__name']
    ordering = ['-year', '-round_number', 'subsidy_type']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('subsidy_type', 'year', 'round_number')
        }),
        ('統計データ', {
            'fields': (
                'total_applications', 'total_adoptions', 'adoption_rate',
                'small_business_applications', 'small_business_adoptions',
                'medium_business_applications', 'medium_business_adoptions'
            )
        }),
        ('業種別統計', {
            'fields': ('industry_statistics',),
            'classes': ('collapse',)
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': '自動入力項目'
        })
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subsidy_type')

# 🆕 採択ティップスの管理画面
@admin.register(AdoptionTips)
class AdoptionTipsAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'subsidy_type', 'category', 'importance', 
        'is_success_case', 'created_at'
    ]
    list_filter = [
        'category', 'importance', 'is_success_case', 
        'subsidy_type', 'created_at'
    ]
    search_fields = ['title', 'content', 'subsidy_type__name']
    ordering = ['subsidy_type', '-importance', 'category']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('subsidy_type', 'category', 'title', 'importance')
        }),
        ('内容', {
            'fields': ('content', 'effective_timing')
        }),
        ('参考情報', {
            'fields': ('reference_url', 'is_success_case'),
            'classes': ('collapse',)
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': '自動入力項目'
        })
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subsidy_type')

# 🆕 申請履歴の管理画面
@admin.register(UserApplicationHistory)
class UserApplicationHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'subsidy_type', 'application_date', 'status',
        'business_type_at_application', 'requested_amount'
    ]
    list_filter = [
        'status', 'application_date', 'subsidy_type',
        'business_type_at_application', 'company_size_at_application'
    ]
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'subsidy_type__name', 'feedback'
    ]
    date_hierarchy = 'application_date'
    ordering = ['-application_date']
    
    fieldsets = (
        ('申請者情報', {
            'fields': ('user', 'subsidy_type')
        }),
        ('申請情報', {
            'fields': (
                'application_date', 'application_round', 'requested_amount'
            )
        }),
        ('申請時企業情報', {
            'fields': (
                'business_type_at_application', 'company_size_at_application'
            )
        }),
        ('結果情報', {
            'fields': ('status', 'result_date', 'feedback')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': '自動入力項目'
        })
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'subsidy_type')

# 🆕 採択スコアカードの管理画面
@admin.register(ApplicationScoreCard)
class ApplicationScoreCardAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'subsidy_type', 'total_score',
        'business_plan_score', 'innovation_score', 'created_at'
    ]
    list_filter = [
        'total_score', 'subsidy_type', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'subsidy_type__name'
    ]
    ordering = ['-created_at', '-total_score']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('user', 'subsidy_type', 'total_score')
        }),
        ('詳細スコア', {
            'fields': (
                'business_plan_score', 'innovation_score', 'feasibility_score',
                'market_potential_score', 'financial_health_score'
            )
        }),
        ('改善提案', {
            'fields': ('improvement_suggestions',),
            'classes': ('collapse',)
        }),
        ('システム情報', {
            'fields': ('created_at',),
            'classes': ('collapse',),
            'description': '自動入力項目'
        })
    )
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'subsidy_type')

# 既存の管理画面登録
admin.site.register(Answer)
admin.site.register(ConversationHistory)

# 🆕 管理画面のカスタマイズ
admin.site.site_header = '補助金アドバイザー 管理システム'
admin.site.site_title = '補助金アドバイザー'
admin.site.index_title = 'システム管理'