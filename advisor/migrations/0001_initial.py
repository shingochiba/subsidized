# Generated by Django 5.2 on 2025-07-04 05:50

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SubsidyType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='補助金名')),
                ('description', models.TextField(verbose_name='概要')),
                ('target_business', models.TextField(verbose_name='対象事業')),
                ('application_period', models.CharField(max_length=100, verbose_name='申請期間')),
                ('max_amount', models.IntegerField(verbose_name='最大補助額')),
                ('subsidy_rate', models.CharField(max_length=50, verbose_name='補助率')),
                ('requirements', models.TextField(verbose_name='申請要件')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '補助金種別',
                'verbose_name_plural': '補助金種別',
            },
        ),
        migrations.CreateModel(
            name='ConversationHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(max_length=100)),
                ('message_type', models.CharField(choices=[('user', 'User'), ('ai', 'AI')], max_length=10)),
                ('content', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '会話履歴',
                'verbose_name_plural': '会話履歴',
                'ordering': ['timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(max_length=100, verbose_name='セッションID')),
                ('question_text', models.TextField(verbose_name='質問内容')),
                ('business_type', models.CharField(blank=True, max_length=100, verbose_name='事業種別')),
                ('company_size', models.CharField(blank=True, max_length=50, verbose_name='企業規模')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '質問',
                'verbose_name_plural': '質問',
            },
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_text', models.TextField(verbose_name='回答内容')),
                ('confidence_score', models.FloatField(default=0.0, verbose_name='信頼度スコア')),
                ('ai_model_used', models.CharField(max_length=50, verbose_name='使用AIモデル')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('question', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='advisor.question')),
                ('recommended_subsidies', models.ManyToManyField(blank=True, to='advisor.subsidytype')),
            ],
            options={
                'verbose_name': '回答',
                'verbose_name_plural': '回答',
            },
        ),
    ]
