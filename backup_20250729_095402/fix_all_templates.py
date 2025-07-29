# fix_all_templates.py
# 全テンプレートのURL参照を一括修正

import os
import re
import glob

def fix_all_template_files():
    """全HTMLテンプレートファイルのURL参照を修正"""
    
    # 修正対象のパターン
    url_replacements = [
        # 存在しないURL名を正しいものに修正
        (r"{% url 'advisor:chat_interface' %}", "{% url 'advisor:chat' %}"),
        (r"{% url 'advisor:enhanced_chat_interface' %}", "{% url 'advisor:chat' %}"),
        (r"{% url 'advisor:enhanced_chat' %}", "{% url 'advisor:chat' %}"),
        (r"{% url 'advisor:statistics' %}", "{% url 'advisor:trend_analysis' %}"),
        (r"{% url 'advisor:subsidy_search' %}", "{% url 'advisor:subsidies' %}"),
        (r"{% url 'advisor:subsidy_recommendations' %}", "{% url 'advisor:subsidies' %}"),
    ]
    
    # テンプレートディレクトリを検索
    template_patterns = [
        'templates/**/*.html',
        'advisor/templates/**/*.html',
        '**/*.html'
    ]
    
    modified_files = []
    
    for pattern in template_patterns:
        html_files = glob.glob(pattern, recursive=True)
        
        for file_path in html_files:
            if fix_template_file(file_path, url_replacements):
                modified_files.append(file_path)
    
    return modified_files

def fix_template_file(file_path, replacements):
    """個別のテンプレートファイルを修正"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # 各パターンで置換
        for pattern, replacement in replacements:
            if pattern in content:
                content = content.replace(pattern, replacement)
                modified = True
                print(f"✅ {file_path}: {pattern} -> {replacement}")
        
        # ファイルが変更された場合のみ保存
        if modified:
            # バックアップ作成
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # 修正版を保存
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ {file_path} 修正エラー: {e}")
        return False

def create_clean_index_template():
    """クリーンなindex.htmlを作成"""
    
    clean_index = '''{% extends 'base.html' %}
{% load static %}

{% block title %}補助金アドバイザー - ホーム{% endblock %}

{% block content %}
<div class="row">
    <!-- ヒーローセクション -->
    <div class="col-12 mb-5">
        <div class="hero-section bg-primary text-white rounded p-5 text-center">
            <h1 class="display-4 fw-bold mb-3">
                <i class="fas fa-handshake"></i> 補助金アドバイザー
            </h1>
            <p class="lead mb-4">
                AIが最適な補助金制度をご提案します<br>
                事業内容に合わせたパーソナライズされたアドバイスを提供
            </p>
            <div class="d-flex justify-content-center gap-3 flex-wrap">
                <a href="{% url 'advisor:chat' %}" class="btn btn-light btn-lg">
                    <i class="fas fa-comments"></i> AI相談を始める
                </a>
                <a href="{% url 'advisor:subsidies' %}" class="btn btn-outline-light btn-lg">
                    <i class="fas fa-list"></i> 補助金一覧
                </a>
            </div>
        </div>
    </div>

    <!-- 主要な補助金制度 -->
    <div class="col-12 mb-5">
        <h2 class="text-center mb-4">
            <i class="fas fa-star"></i> 主要な補助金制度
        </h2>
        <div class="row g-4">
            <div class="col-md-6 col-lg-3">
                <div class="card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <div class="text-primary mb-3">
                            <i class="fas fa-laptop-code fa-3x"></i>
                        </div>
                        <h5 class="card-title">IT導入補助金</h5>
                        <p class="card-text">ITツール導入で業務効率化</p>
                        <p class="fw-bold text-success">最大450万円</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6 col-lg-3">
                <div class="card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <div class="text-primary mb-3">
                            <i class="fas fa-industry fa-3x"></i>
                        </div>
                        <h5 class="card-title">ものづくり補助金</h5>
                        <p class="card-text">革新的な設備投資を支援</p>
                        <p class="fw-bold text-success">最大1,250万円</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6 col-lg-3">
                <div class="card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <div class="text-primary mb-3">
                            <i class="fas fa-store fa-3x"></i>
                        </div>
                        <h5 class="card-title">持続化補助金</h5>
                        <p class="card-text">小規模事業者の販路開拓</p>
                        <p class="fw-bold text-success">最大200万円</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6 col-lg-3">
                <div class="card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <div class="text-primary mb-3">
                            <i class="fas fa-robot fa-3x"></i>
                        </div>
                        <h5 class="card-title">省力化投資補助金</h5>
                        <p class="card-text">人手不足解消・自動化</p>
                        <p class="fw-bold text-success">最大1,000万円</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 特徴セクション -->
    <div class="col-12 mb-5">
        <h2 class="text-center mb-4">
            <i class="fas fa-magic"></i> 補助金アドバイザーの特徴
        </h2>
        <div class="row g-4">
            <div class="col-md-4">
                <div class="feature-item text-center p-4">
                    <div class="text-primary mb-3">
                        <i class="fas fa-brain fa-3x"></i>
                    </div>
                    <h5>AI診断</h5>
                    <p class="text-muted">
                        事業内容を分析し、最適な補助金制度をAIが自動で提案します
                    </p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="feature-item text-center p-4">
                    <div class="text-primary mb-3">
                        <i class="fas fa-clock fa-3x"></i>
                    </div>
                    <h5>24時間対応</h5>
                    <p class="text-muted">
                        いつでもお気軽にご相談いただけます。迅速な回答をお約束します
                    </p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="feature-item text-center p-4">
                    <div class="text-primary mb-3">
                        <i class="fas fa-chart-line fa-3x"></i>
                    </div>
                    <h5>成功率向上</h5>
                    <p class="text-muted">
                        採択率向上のための具体的なアドバイスを提供します
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- CTAセクション -->
    <div class="col-12">
        <div class="cta-section bg-light rounded p-5 text-center">
            <h3 class="mb-3">今すぐ始めましょう</h3>
            <p class="lead mb-4">
                あなたの事業に最適な補助金制度を見つけて、成長を加速させましょう
            </p>
            <a href="{% url 'advisor:chat' %}" class="btn btn-primary btn-lg">
                <i class="fas fa-rocket"></i> 無料相談を開始
            </a>
        </div>
    </div>
</div>

<style>
.hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.feature-item {
    transition: transform 0.3s ease;
}

.feature-item:hover {
    transform: translateY(-5px);
}

.cta-section {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
}
</style>
{% endblock %}'''
    
    try:
        with open('templates/advisor/index.html', 'w', encoding='utf-8') as f:
            f.write(clean_index)
        print("✅ クリーンなindex.htmlを作成しました")
        return True
    except Exception as e:
        print(f"❌ index.html作成エラー: {e}")
        return False

def create_clean_chat_template():
    """クリーンなchat.htmlを作成"""
    
    clean_chat = '''{% extends 'base.html' %}
{% load static %}

{% block title %}AI相談 - 補助金アドバイザー{% endblock %}

{% block extra_css %}
<style>
.chat-container {
    height: 70vh;
    display: flex;
    flex-direction: column;
}

.chat-messages {
    flex-grow: 1;
    overflow-y: auto;
    padding: 20px;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
}

.message {
    margin-bottom: 15px;
    padding: 12px 16px;
    border-radius: 18px;
    max-width: 80%;
    word-wrap: break-word;
}

.user-message {
    background-color: #007bff;
    color: white;
    margin-left: auto;
    text-align: right;
}

.assistant-message {
    background-color: white;
    border: 1px solid #dee2e6;
    margin-right: auto;
}

.typing-indicator {
    display: none;
    padding: 10px;
    font-style: italic;
    color: #6c757d;
}

.chat-input-container {
    margin-top: 20px;
}

.loading {
    opacity: 0.7;
    pointer-events: none;
}

#sendButton:disabled {
    background-color: #6c757d;
    border-color: #6c757d;
}
</style>
{% endblock %}

{% block content %}
<div class="container">
    <div class="row justify-content-center">
        <div class="col-lg-10">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0">
                        <i class="fas fa-robot"></i> AI補助金アドバイザー
                    </h4>
                    <small>事業内容に最適な補助金制度をご提案します</small>
                </div>
                
                <div class="card-body">
                    <!-- チャットメッセージエリア -->
                    <div class="chat-container">
                        <div id="chatMessages" class="chat-messages">
                            <div class="message assistant-message">
                                <strong>🤖 補助金アドバイザー:</strong><br>
                                こんにちは！補助金に関するご相談をお受けします。<br>
                                以下のような質問をお気軽にどうぞ：<br><br>
                                • 「IT導入補助金について教えて」<br>
                                • 「ものづくり補助金の申請方法は？」<br>
                                • 「小規模事業者持続化補助金の要件は？」<br>
                                • 「採択率を上げるコツは？」
                            </div>
                        </div>
                        
                        <div id="typingIndicator" class="typing-indicator">
                            <i class="fas fa-spinner fa-spin"></i> 回答を作成中...
                        </div>
                    </div>
                    
                    <!-- メッセージ入力エリア -->
                    <div class="chat-input-container">
                        <div class="input-group">
                            <input type="text" 
                                   id="messageInput" 
                                   class="form-control" 
                                   placeholder="補助金について質問してください..."
                                   maxlength="500">
                            <button id="sendButton" class="btn btn-primary" type="button">
                                <i class="fas fa-paper-plane"></i> 送信
                            </button>
                        </div>
                        <div class="form-text mt-2">
                            <i class="fas fa-info-circle"></i> 
                            具体的な補助金名や申請方法について質問すると、より詳しい回答が得られます
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- サンプル質問ボタン -->
<div class="container mt-4">
    <div class="row justify-content-center">
        <div class="col-lg-10">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-lightbulb"></i> よくある質問</h6>
                </div>
                <div class="card-body">
                    <div class="row g-2">
                        <div class="col-md-6">
                            <button class="btn btn-outline-primary btn-sm w-100 sample-question" 
                                    data-question="IT導入補助金について教えて">
                                IT導入補助金について
                            </button>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-outline-primary btn-sm w-100 sample-question" 
                                    data-question="ものづくり補助金の申請方法を教えて">
                                ものづくり補助金の申請方法
                            </button>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-outline-primary btn-sm w-100 sample-question" 
                                    data-question="小規模事業者持続化補助金について教えて">
                                小規模事業者持続化補助金
                            </button>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-outline-primary btn-sm w-100 sample-question" 
                                    data-question="採択率を上げるコツは？">
                                採択率を上げるコツ
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
class ChatInterface {
    constructor() {
        this.apiUrl = '{% url "advisor:enhanced_chat_api" %}';
        this.sessionId = this.generateSessionId();
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const sampleQuestions = document.querySelectorAll('.sample-question');

        // 送信ボタンクリック
        sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enterキー送信
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // サンプル質問ボタン
        sampleQuestions.forEach(button => {
            button.addEventListener('click', (e) => {
                const question = e.target.getAttribute('data-question');
                messageInput.value = question;
                this.sendMessage();
            });
        });
    }

    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message) return;

        // ユーザーメッセージを表示
        this.addMessage(message, 'user');
        messageInput.value = '';
        
        // 送信ボタンを無効化
        this.setLoading(true);

        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            const data = await response.json();

            if (data.success) {
                this.addMessage(data.response.answer, 'assistant');
            } else {
                this.addMessage('申し訳ございません。エラーが発生しました。', 'assistant');
            }
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('通信エラーが発生しました。もう一度お試しください。', 'assistant');
        } finally {
            this.setLoading(false);
        }
    }

    addMessage(content, sender) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        if (sender === 'user') {
            messageDiv.innerHTML = `<strong>あなた:</strong><br>${this.escapeHtml(content)}`;
        } else {
            messageDiv.innerHTML = `<strong>🤖 アドバイザー:</strong><br>${content}`;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    setLoading(loading) {
        const sendButton = document.getElementById('sendButton');
        const messageInput = document.getElementById('messageInput');
        const typingIndicator = document.getElementById('typingIndicator');
        
        sendButton.disabled = loading;
        messageInput.disabled = loading;
        typingIndicator.style.display = loading ? 'block' : 'none';
        
        if (loading) {
            sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 送信中';
        } else {
            sendButton.innerHTML = '<i class="fas fa-paper-plane"></i> 送信';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
}

// ページ読み込み時にチャットインターフェースを初期化
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});
</script>
{% endblock %}'''
    
    try:
        with open('templates/advisor/chat.html', 'w', encoding='utf-8') as f:
            f.write(clean_chat)
        print("✅ クリーンなchat.htmlを作成しました")
        return True
    except Exception as e:
        print(f"❌ chat.html作成エラー: {e}")
        return False

def main():
    """メイン実行"""
    print("🔧 全テンプレートのURL参照を一括修正中...")
    print("=" * 50)
    
    # 1. 既存のテンプレートを修正
    print("1. 既存テンプレートの修正中...")
    modified_files = fix_all_template_files()
    
    if modified_files:
        print(f"✅ {len(modified_files)}個のファイルを修正しました:")
        for file_path in modified_files:
            print(f"  - {file_path}")
    else:
        print("ℹ️ 修正が必要なファイルはありませんでした")
    
    # 2. 問題のあるテンプレートを新規作成
    print("\n2. クリーンなテンプレートの作成中...")
    
    # index.htmlを作成
    if os.path.exists('templates/advisor/index.html'):
        create_clean_index_template()
    
    # chat.htmlを作成
    if os.path.exists('templates/advisor/chat.html'):
        create_clean_chat_template()
    
    print("=" * 50)
    print("✅ 全テンプレート修正完了！")
    print("\n📋 次のステップ:")
    print("1. python manage.py runserver 0.0.0.0:8000 で再起動")
    print("2. http://192.168.128.196:8000/advisor/ でホームページ確認")
    print("3. http://192.168.128.196:8000/advisor/chat/ でチャット機能テスト")

if __name__ == "__main__":
    main()