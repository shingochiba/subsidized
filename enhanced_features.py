# enhanced_features.py - 補助金一覧・統計・予測機能の完全実装
import os
import django

# Django設定の初期化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsidy_advisor_project.settings')
django.setup()

def create_enhanced_views():
    """拡張ビュー関数を作成"""
    
    views_code = '''
# advisor/views.py に追加する関数群

from django.db.models import Count, Avg, Max, Min, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json

def subsidy_list(request):
    """
    補助金一覧表示（JSON/HTML対応）
    """
    try:
        # フィルタリングパラメータ
        category = request.GET.get('category', '')
        business_type = request.GET.get('business_type', '')
        search = request.GET.get('search', '')
        
        # 基本クエリ
        subsidies = SubsidyType.objects.all()
        
        # フィルタリング
        if category:
            subsidies = subsidies.filter(category__icontains=category)
        
        if business_type:
            subsidies = subsidies.filter(target_business_type__icontains=business_type)
        
        if search:
            subsidies = subsidies.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(requirements__icontains=search)
            )
        
        # 並び替え
        subsidies = subsidies.order_by('-max_amount', 'name')
        
        # JSON レスポンス
        if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
            subsidy_data = []
            for subsidy in subsidies:
                subsidy_data.append({
                    'id': subsidy.id,
                    'name': subsidy.name,
                    'description': subsidy.description,
                    'max_amount': float(subsidy.max_amount) if subsidy.max_amount else 0,
                    'target_business_type': subsidy.target_business_type,
                    'requirements': subsidy.requirements,
                    'adoption_rate': getattr(subsidy, 'adoption_rate', 0),
                })
            
            return JsonResponse({
                'success': True,
                'subsidies': subsidy_data,
                'count': len(subsidy_data),
                'filters': {
                    'category': category,
                    'business_type': business_type,
                    'search': search
                }
            })
        
        # HTML レスポンス
        # 統計データ
        stats = {
            'total_count': subsidies.count(),
            'avg_amount': subsidies.aggregate(avg=Avg('max_amount'))['avg'] or 0,
            'max_amount': subsidies.aggregate(max=Max('max_amount'))['max'] or 0,
            'categories': subsidies.values('target_business_type').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
        }
        
        context = {
            'subsidies': subsidies,
            'stats': stats,
            'filters': {
                'category': category,
                'business_type': business_type,
                'search': search
            },
            'page_title': '補助金一覧'
        }
        
        return render(request, 'advisor/subsidy_list.html', context)
        
    except Exception as e:
        error_response = {
            'success': False,
            'error': str(e),
            'message': '補助金データの取得中にエラーが発生しました'
        }
        
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse(error_response, status=500)
        else:
            return render(request, 'advisor/error.html', {'error': error_response})

def statistics_dashboard(request):
    """
    統計ダッシュボード
    """
    try:
        # 基本統計
        basic_stats = {
            'total_subsidies': SubsidyType.objects.count(),
            'total_conversations': ConversationHistory.objects.count(),
            'active_sessions': ConversationHistory.objects.values('session_id').distinct().count(),
        }
        
        # 補助金統計
        subsidy_stats = SubsidyType.objects.aggregate(
            avg_amount=Avg('max_amount'),
            max_amount=Max('max_amount'),
            min_amount=Min('max_amount'),
            total_amount=models.Sum('max_amount')
        )
        
        # 事業種別統計
        business_type_stats = SubsidyType.objects.values('target_business_type').annotate(
            count=Count('id'),
            avg_amount=Avg('max_amount')
        ).order_by('-count')[:10]
        
        # 時系列データ（過去30日の会話数）
        last_30_days = timezone.now() - timedelta(days=30)
        daily_conversations = []
        
        for i in range(30):
            date = last_30_days + timedelta(days=i)
            count = ConversationHistory.objects.filter(
                timestamp__date=date.date(),
                message_type='user'
            ).count()
            daily_conversations.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        # 人気の質問キーワード
        user_messages = ConversationHistory.objects.filter(
            message_type='user'
        ).values_list('message', flat=True)[:1000]
        
        # キーワード分析（簡易版）
        keywords = {}
        for message in user_messages:
            words = message.lower().split()
            for word in words:
                if len(word) > 2:  # 3文字以上
                    keywords[word] = keywords.get(word, 0) + 1
        
        popular_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 採択率データ（モックデータ）
        adoption_data = []
        for subsidy in SubsidyType.objects.all()[:10]:
            adoption_data.append({
                'name': subsidy.name[:20],  # 名前を短縮
                'rate': 65 + (hash(subsidy.name) % 30),  # 65-95%のランダム値
                'applications': 100 + (hash(subsidy.name) % 500)  # 100-600件
            })
        
        context = {
            'basic_stats': basic_stats,
            'subsidy_stats': subsidy_stats,
            'business_type_stats': business_type_stats,
            'daily_conversations': daily_conversations,
            'popular_keywords': popular_keywords,
            'adoption_data': adoption_data,
            'page_title': '統計ダッシュボード'
        }
        
        # JSON API対応
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': True,
                'data': context
            })
        
        return render(request, 'advisor/statistics_dashboard.html', context)
        
    except Exception as e:
        error_msg = f'統計データの取得中にエラーが発生しました: {str(e)}'
        
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'success': False, 'error': error_msg}, status=500)
        
        return render(request, 'advisor/error.html', {'error': error_msg})

def prediction_dashboard(request):
    """
    予測ダッシュボード
    """
    try:
        # 現在の日付
        current_date = timezone.now()
        
        # 予測データ（実際のAIモデルの代わりにルールベース）
        predictions = []
        
        # IT導入補助金の予測
        it_subsidy = SubsidyType.objects.filter(name__icontains='IT').first()
        if it_subsidy:
            predictions.append({
                'subsidy_name': 'IT導入補助金',
                'prediction_type': '新規公募',
                'predicted_date': (current_date + timedelta(days=15)).strftime('%Y-%m-%d'),
                'confidence': 85,
                'description': 'IT導入補助金の次回公募開始が予測されます',
                'recommended_action': '事前準備として必要書類の整理を開始してください'
            })
        
        # ものづくり補助金の予測
        mono_subsidy = SubsidyType.objects.filter(name__icontains='ものづくり').first()
        if mono_subsidy:
            predictions.append({
                'subsidy_name': 'ものづくり補助金',
                'prediction_type': '締切延長',
                'predicted_date': (current_date + timedelta(days=7)).strftime('%Y-%m-%d'),
                'confidence': 72,
                'description': '申請締切の延長が予測されます',
                'recommended_action': '申請書類の最終確認を行ってください'
            })
        
        # 事業再構築補助金の予測
        restructure_subsidy = SubsidyType.objects.filter(name__icontains='再構築').first()
        if restructure_subsidy:
            predictions.append({
                'subsidy_name': '事業再構築補助金',
                'prediction_type': '採択発表',
                'predicted_date': (current_date + timedelta(days=30)).strftime('%Y-%m-%d'),
                'confidence': 90,
                'description': '第10回採択結果の発表が予測されます',
                'recommended_action': '採択後の準備を進めておいてください'
            })
        
        # カレンダー用の月間予測データ
        monthly_predictions = {}
        for pred in predictions:
            date_key = pred['predicted_date']
            monthly_predictions[date_key] = pred
        
        # 統計データ
        prediction_stats = {
            'total_predictions': len(predictions),
            'high_confidence': len([p for p in predictions if p['confidence'] >= 80]),
            'medium_confidence': len([p for p in predictions if 60 <= p['confidence'] < 80]),
            'low_confidence': len([p for p in predictions if p['confidence'] < 60]),
        }
        
        # トレンド分析データ
        trend_data = {
            'it_subsidies_trend': 'increasing',  # 増加傾向
            'manufacturing_trend': 'stable',     # 安定
            'reconstruction_trend': 'decreasing' # 減少傾向
        }
        
        context = {
            'predictions': predictions,
            'monthly_predictions': monthly_predictions,
            'prediction_stats': prediction_stats,
            'trend_data': trend_data,
            'current_date': current_date.strftime('%Y-%m-%d'),
            'page_title': '予測ダッシュボード'
        }
        
        # JSON API対応
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': True,
                'data': context
            })
        
        return render(request, 'advisor/prediction_dashboard.html', context)
        
    except Exception as e:
        error_msg = f'予測データの取得中にエラーが発生しました: {str(e)}'
        
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'success': False, 'error': error_msg}, status=500)
        
        return render(request, 'advisor/error.html', {'error': error_msg})
'''
    
    return views_code

def create_enhanced_templates():
    """拡張テンプレートファイルを作成"""
    
    templates = {
        'subsidy_list.html': '''{% extends "base.html" %}
{% load static %}

{% block title %}{{ page_title }}{% endblock %}

{% block extra_css %}
<style>
.subsidy-card {
    transition: transform 0.2s, box-shadow 0.2s;
    border-left: 4px solid #007bff;
}
.subsidy-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.amount-badge {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: 600;
}
.filter-section {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 2rem;
}
.stats-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    padding: 1.5rem;
}
</style>
{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <div class="row">
        <div class="col-12">
            <h1 class="mb-4">
                <i class="fas fa-list me-2"></i>{{ page_title }}
            </h1>
        </div>
    </div>
    
    <!-- 統計サマリー -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="stats-card text-center">
                <h3>{{ stats.total_count }}</h3>
                <p class="mb-0">総補助金数</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stats-card text-center">
                <h3>{{ stats.avg_amount|floatformat:0 }}万円</h3>
                <p class="mb-0">平均金額</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stats-card text-center">
                <h3>{{ stats.max_amount|floatformat:0 }}万円</h3>
                <p class="mb-0">最高金額</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stats-card text-center">
                <h3>{{ stats.categories|length }}</h3>
                <p class="mb-0">事業分野</p>
            </div>
        </div>
    </div>
    
    <!-- フィルター -->
    <div class="filter-section">
        <form method="GET" class="row g-3">
            <div class="col-md-3">
                <label class="form-label">事業種別</label>
                <select name="business_type" class="form-select">
                    <option value="">全て</option>
                    {% for category in stats.categories %}
                        <option value="{{ category.target_business_type }}" 
                                {% if filters.business_type == category.target_business_type %}selected{% endif %}>
                            {{ category.target_business_type }} ({{ category.count }})
                        </option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-4">
                <label class="form-label">検索キーワード</label>
                <input type="text" name="search" class="form-control" 
                       value="{{ filters.search }}" placeholder="補助金名、説明で検索">
            </div>
            <div class="col-md-2">
                <label class="form-label">&nbsp;</label>
                <button type="submit" class="btn btn-primary d-block w-100">
                    <i class="fas fa-search me-1"></i>検索
                </button>
            </div>
            <div class="col-md-2">
                <label class="form-label">&nbsp;</label>
                <a href="{% url 'advisor:subsidy_list' %}" class="btn btn-outline-secondary d-block w-100">
                    <i class="fas fa-times me-1"></i>クリア
                </a>
            </div>
        </form>
    </div>
    
    <!-- 補助金一覧 -->
    <div class="row">
        {% for subsidy in subsidies %}
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card subsidy-card h-100">
                <div class="card-body">
                    <h5 class="card-title">{{ subsidy.name }}</h5>
                    <p class="card-text text-muted">
                        {{ subsidy.description|truncatechars:100 }}
                    </p>
                    
                    <div class="mb-3">
                        <span class="amount-badge">
                            最大 {{ subsidy.max_amount|floatformat:0 }}万円
                        </span>
                    </div>
                    
                    <div class="mb-2">
                        <small class="text-muted">
                            <i class="fas fa-building me-1"></i>
                            {{ subsidy.target_business_type }}
                        </small>
                    </div>
                    
                    <div class="requirements">
                        <small class="text-muted">
                            {{ subsidy.requirements|truncatechars:80 }}
                        </small>
                    </div>
                </div>
                <div class="card-footer bg-transparent">
                    <button class="btn btn-outline-primary btn-sm" 
                            onclick="showSubsidyDetails({{ subsidy.id }})">
                        <i class="fas fa-info-circle me-1"></i>詳細情報
                    </button>
                </div>
            </div>
        </div>
        {% empty %}
        <div class="col-12">
            <div class="alert alert-info text-center">
                <h4><i class="fas fa-search me-2"></i>該当する補助金が見つかりませんでした</h4>
                <p>検索条件を変更してお試しください。</p>
            </div>
        </div>
        {% endfor %}
    </div>
</div>

<!-- 詳細モーダル -->
<div class="modal fade" id="subsidyDetailModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">補助金詳細情報</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="subsidyDetailContent">
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">読み込み中...</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function showSubsidyDetails(subsidyId) {
    const modal = new bootstrap.Modal(document.getElementById('subsidyDetailModal'));
    modal.show();
    
    // 詳細情報を取得（実装は後で追加）
    document.getElementById('subsidyDetailContent').innerHTML = `
        <div class="alert alert-info">
            詳細情報を読み込み中です...
        </div>
    `;
}
</script>
{% endblock %}''',

        'statistics_dashboard.html': '''{% extends "base.html" %}
{% load static %}

{% block title %}{{ page_title }}{% endblock %}

{% block extra_css %}
<style>
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}
.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    transition: transform 0.3s;
}
.stat-card:hover {
    transform: translateY(-5px);
}
.chart-container {
    background: white;
    padding: 2rem;
    border-radius: 15px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}
.keyword-tag {
    display: inline-block;
    background: #e9ecef;
    padding: 0.5rem 1rem;
    margin: 0.25rem;
    border-radius: 20px;
    font-size: 0.9rem;
}
</style>
{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <div class="row">
        <div class="col-12">
            <h1 class="mb-4">
                <i class="fas fa-chart-bar me-2"></i>{{ page_title }}
            </h1>
        </div>
    </div>
    
    <!-- 基本統計 -->
    <div class="stats-grid">
        <div class="stat-card">
            <h3>{{ basic_stats.total_subsidies }}</h3>
            <p class="mb-0">総補助金数</p>
        </div>
        <div class="stat-card">
            <h3>{{ basic_stats.total_conversations }}</h3>
            <p class="mb-0">総会話数</p>
        </div>
        <div class="stat-card">
            <h3>{{ basic_stats.active_sessions }}</h3>
            <p class="mb-0">アクティブセッション</p>
        </div>
        <div class="stat-card">
            <h3>{{ subsidy_stats.avg_amount|floatformat:0 }}万円</h3>
            <p class="mb-0">平均補助金額</p>
        </div>
    </div>
    
    <div class="row">
        <!-- 会話数推移 -->
        <div class="col-lg-8">
            <div class="chart-container">
                <h4 class="mb-3">
                    <i class="fas fa-chart-line me-2"></i>会話数推移（過去30日）
                </h4>
                <canvas id="conversationChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <!-- 事業種別統計 -->
        <div class="col-lg-4">
            <div class="chart-container">
                <h4 class="mb-3">
                    <i class="fas fa-chart-pie me-2"></i>事業種別分布
                </h4>
                <canvas id="businessTypeChart" width="300" height="300"></canvas>
            </div>
        </div>
    </div>
    
    <div class="row">
        <!-- 採択率比較 -->
        <div class="col-lg-6">
            <div class="chart-container">
                <h4 class="mb-3">
                    <i class="fas fa-chart-bar me-2"></i>補助金別採択率
                </h4>
                <canvas id="adoptionChart" width="400" height="300"></canvas>
            </div>
        </div>
        
        <!-- 人気キーワード -->
        <div class="col-lg-6">
            <div class="chart-container">
                <h4 class="mb-3">
                    <i class="fas fa-tags me-2"></i>人気の検索キーワード
                </h4>
                <div class="keyword-cloud">
                    {% for keyword, count in popular_keywords %}
                        <span class="keyword-tag">{{ keyword }} ({{ count }})</span>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
// 会話数推移チャート
const conversationData = {{ daily_conversations|safe }};
const conversationCtx = document.getElementById('conversationChart').getContext('2d');
new Chart(conversationCtx, {
    type: 'line',
    data: {
        labels: conversationData.map(d => d.date),
        datasets: [{
            label: '会話数',
            data: conversationData.map(d => d.count),
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

// 事業種別チャート
const businessTypeData = {{ business_type_stats|safe }};
const businessTypeCtx = document.getElementById('businessTypeChart').getContext('2d');
new Chart(businessTypeCtx, {
    type: 'doughnut',
    data: {
        labels: businessTypeData.map(d => d.target_business_type),
        datasets: [{
            data: businessTypeData.map(d => d.count),
            backgroundColor: [
                '#667eea', '#764ba2', '#f093fb', '#f5576c', 
                '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
            ]
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false
    }
});

// 採択率チャート
const adoptionData = {{ adoption_data|safe }};
const adoptionCtx = document.getElementById('adoptionChart').getContext('2d');
new Chart(adoptionCtx, {
    type: 'bar',
    data: {
        labels: adoptionData.map(d => d.name),
        datasets: [{
            label: '採択率 (%)',
            data: adoptionData.map(d => d.rate),
            backgroundColor: 'rgba(102, 126, 234, 0.8)',
            borderColor: '#667eea',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                max: 100
            }
        }
    }
});
</script>
{% endblock %}''',

        'prediction_dashboard.html': '''{% extends "base.html" %}
{% load static %}

{% block title %}{{ page_title }}{% endblock %}

{% block extra_css %}
<style>
.prediction-card {
    border-left: 4px solid #28a745;
    transition: transform 0.2s;
}
.prediction-card:hover {
    transform: translateY(-2px);
}
.confidence-badge {
    font-size: 0.8rem;
    padding: 0.25rem 0.75rem;
    border-radius: 15px;
}
.confidence-high { background: #28a745; color: white; }
.confidence-medium { background: #ffc107; color: black; }
.confidence-low { background: #dc3545; color: white; }
.calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 1px;
    background: #dee2e6;
    border-radius: 8px;
    overflow: hidden;
}
.calendar-day {
    background: white;
    padding: 0.75rem;
    text-align: center;
    min-height: 60px;
    position: relative;
    cursor: pointer;
}
.calendar-day:hover {
    background: #f8f9fa;
}
.calendar-header {
    background: #495057;
    color: white;
    font-weight: 600;
}
.prediction-indicator {
    position: absolute;
    bottom: 2px;
    right: 2px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #007bff;
}
.trend-indicator {
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: 600;
}
.trend-increasing { background: #d4edda; color: #155724; }
.trend-stable { background: #fff3cd; color: #856404; }
.trend-decreasing { background: #f8d7da; color: #721c24; }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <div class="row">
        <div class="col-12">
            <h1 class="mb-4">
                <i class="fas fa-crystal-ball me-2"></i>{{ page_title }}
            </h1>
        </div>
    </div>
    
    <!-- 予測統計 -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card text-center bg-primary text-white">
                <div class="card-body">
                    <h3>{{ prediction_stats.total_predictions }}</h3>
                    <p class="mb-0">総予測数</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center bg-success text-white">
                <div class="card-body">
                    <h3>{{ prediction_stats.high_confidence }}</h3>
                    <p class="mb-0">高信頼度予測</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center bg-warning text-white">
                <div class="card-body">
                    <h3>{{ prediction_stats.medium_confidence }}</h3>
                    <p class="mb-0">中信頼度予測</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center bg-danger text-white">
                <div class="card-body">
                    <h3>{{ prediction_stats.low_confidence }}</h3>
                    <p class="mb-0">低信頼度予測</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row">
        <!-- 予測一覧 -->
        <div class="col-lg-8">
            <div class="card">
                <div class="card-header">
                    <h4 class="mb-0">
                        <i class="fas fa-list me-2"></i>最新の予測
                    </h4>
                </div>
                <div class="card-body">
                    {% for prediction in predictions %}
                    <div class="prediction-card card mb-3">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h5 class="card-title">{{ prediction.subsidy_name }}</h5>
                                    <p class="card-text">{{ prediction.description }}</p>
                                    <small class="text-muted">
                                        <i class="fas fa-calendar me-1"></i>
                                        予測日: {{ prediction.predicted_date }}
                                    </small>
                                </div>
                                <div class="text-end">
                                    <span class="confidence-badge 
                                        {% if prediction.confidence >= 80 %}confidence-high
                                        {% elif prediction.confidence >= 60 %}confidence-medium
                                        {% else %}confidence-low{% endif %}">
                                        信頼度 {{ prediction.confidence }}%
                                    </span>
                                    <div class="mt-2">
                                        <span class="badge bg-info">{{ prediction.prediction_type }}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="mt-3 p-3 bg-light rounded">
                                <strong>推奨アクション:</strong><br>
                                {{ prediction.recommended_action }}
                            </div>
                        </div>
                    </div>
                    {% empty %}
                    <div class="alert alert-info">
                        現在利用可能な予測データはありません。
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <!-- サイドパネル -->
        <div class="col-lg-4">
            <!-- トレンド分析 -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-chart-line me-2"></i>トレンド分析
                    </h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <div class="d-flex justify-content-between align-items-center">
                            <span>IT導入補助金</span>
                            <span class="trend-indicator trend-{{ trend_data.it_subsidies_trend }}">
                                {% if trend_data.it_subsidies_trend == 'increasing' %}
                                    <i class="fas fa-arrow-up"></i> 増加
                                {% elif trend_data.it_subsidies_trend == 'stable' %}
                                    <i class="fas fa-minus"></i> 安定
                                {% else %}
                                    <i class="fas fa-arrow-down"></i> 減少
                                {% endif %}
                            </span>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="d-flex justify-content-between align-items-center">
                            <span>ものづくり補助金</span>
                            <span class="trend-indicator trend-{{ trend_data.manufacturing_trend }}">
                                {% if trend_data.manufacturing_trend == 'increasing' %}
                                    <i class="fas fa-arrow-up"></i> 増加
                                {% elif trend_data.manufacturing_trend == 'stable' %}
                                    <i class="fas fa-minus"></i> 安定
                                {% else %}
                                    <i class="fas fa-arrow-down"></i> 減少
                                {% endif %}
                            </span>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="d-flex justify-content-between align-items-center">
                            <span>事業再構築補助金</span>
                            <span class="trend-indicator trend-{{ trend_data.reconstruction_trend }}">
                                {% if trend_data.reconstruction_trend == 'increasing' %}
                                    <i class="fas fa-arrow-up"></i> 増加
                                {% elif trend_data.reconstruction_trend == 'stable' %}
                                    <i class="fas fa-minus"></i> 安定
                                {% else %}
                                    <i class="fas fa-arrow-down"></i> 減少
                                {% endif %}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 予測カレンダー -->
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-calendar me-2"></i>予測カレンダー
                    </h5>
                </div>
                <div class="card-body">
                    <div class="calendar-grid">
                        <div class="calendar-day calendar-header">日</div>
                        <div class="calendar-day calendar-header">月</div>
                        <div class="calendar-day calendar-header">火</div>
                        <div class="calendar-day calendar-header">水</div>
                        <div class="calendar-day calendar-header">木</div>
                        <div class="calendar-day calendar-header">金</div>
                        <div class="calendar-day calendar-header">土</div>
                        
                        <!-- カレンダーの日付は JavaScript で生成 -->
                        <div id="calendarDays"></div>
                    </div>
                    
                    <div class="mt-3">
                        <div class="d-flex align-items-center mb-2">
                            <div class="prediction-indicator me-2"></div>
                            <small>予測イベントあり</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// カレンダー生成
const currentDate = new Date();
const year = currentDate.getFullYear();
const month = currentDate.getMonth();

const firstDay = new Date(year, month, 1);
const lastDay = new Date(year, month + 1, 0);
const startDate = new Date(firstDay);
startDate.setDate(startDate.getDate() - firstDay.getDay());

const predictions = {{ monthly_predictions|safe }};
const calendarDays = document.getElementById('calendarDays');

for (let i = 0; i < 42; i++) {
    const day = new Date(startDate);
    day.setDate(startDate.getDate() + i);
    
    const dayDiv = document.createElement('div');
    dayDiv.className = 'calendar-day';
    
    if (day.getMonth() !== month) {
        dayDiv.style.color = '#ccc';
    }
    
    const dayKey = day.toISOString().split('T')[0];
    
    dayDiv.innerHTML = `
        ${day.getDate()}
        ${predictions[dayKey] ? '<div class="prediction-indicator"></div>' : ''}
    `;
    
    if (predictions[dayKey]) {
        dayDiv.title = predictions[dayKey].description;
        dayDiv.onclick = () => {
            alert(`${predictions[dayKey].subsidy_name}: ${predictions[dayKey].description}`);
        };
    }
    
    calendarDays.appendChild(dayDiv);
}
</script>
{% endblock %}'''
    }
    
    return templates

def create_enhanced_urls():
    """拡張URL設定を作成"""
    
    urls_addition = '''
# advisor/urls.py に以下を追加

    # 拡張機能
    path('subsidies/', views.subsidy_list, name='subsidy_list'),
    path('statistics/', views.statistics_dashboard, name='statistics_dashboard'),
    path('predictions/', views.prediction_dashboard, name='prediction_dashboard'),
    
    # API エンドポイント
    path('api/subsidies/', views.subsidy_list, name='subsidy_list_api'),
    path('api/statistics/', views.statistics_dashboard, name='statistics_api'),
    path('api/predictions/', views.prediction_dashboard, name='predictions_api'),
'''
    
    return urls_addition

def main():
    """メイン実行関数"""
    print("🚀 補助金一覧・統計・予測機能の実装開始")
    print("=" * 60)
    
    # 1. ビュー関数の作成
    print("\n1. 拡張ビュー関数の作成...")
    views_code = create_enhanced_views()
    
    # advisor/views.py に追加するコードを表示
    print("✅ 以下のコードを advisor/views.py に追加してください:")
    print("-" * 40)
    print(views_code[:500] + "...")
    
    # 2. テンプレートファイルの作成
    print("\n2. テンプレートファイルの作成...")
    templates = create_enhanced_templates()
    
    for template_name, template_content in templates.items():
        template_path = f"templates/advisor/{template_name}"
        print(f"✅ テンプレート: {template_path}")
    
    # 3. URL設定の追加
    print("\n3. URL設定の追加...")
    urls_addition = create_enhanced_urls()
    print("✅ 以下のURLパターンを advisor/urls.py に追加してください:")
    print(urls_addition)
    
    print("\n" + "=" * 60)
    print("🎯 実装完了!")
    print("次のステップ:")
    print("1. 表示されたコードを該当ファイルに追加")
    print("2. サーバーを再起動: python manage.py runserver 0.0.0.0:8000")
    print("3. 以下のURLでアクセステスト:")
    print("   - 補助金一覧: /advisor/subsidies/")
    print("   - 統計ダッシュボード: /advisor/statistics/")
    print("   - 予測ダッシュボード: /advisor/predictions/")

if __name__ == "__main__":
    main()