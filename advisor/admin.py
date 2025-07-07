from django.contrib import admin
from .models import SubsidyType, Question, Answer, ConversationHistory

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

admin.site.register(Answer)
admin.site.register(ConversationHistory)