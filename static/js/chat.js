// advisor/static/js/enhanced_chat.js - アプリ専用チャット機能
console.log("Advisor Enhanced Chat JS 読み込み開始");

// 全体設定をグローバルスコープで定義
window.advisorChatConfig = {
    apiUrl: '/advisor/api/enhanced-chat/',
    sessionId: `advisor_chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    debug: true
};

class AdvisorChatManager {
    constructor() {
        console.log("AdvisorChatManager 初期化中...");
        
        this.config = window.advisorChatConfig;
        this.isLoading = false;
        
        this.initializeElements();
        this.bindEvents();
        
        console.log("AdvisorChatManager 初期化完了");
    }
    
    initializeElements() {
        console.log("要素の初期化中...");
        
        // 基本要素の取得
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        
        if (this.config.debug) {
            console.log("Chat Messages:", this.chatMessages);
            console.log("Message Input:", this.messageInput);
            console.log("Send Button:", this.sendButton);
        }
        
        // 要素が見つからない場合のエラーハンドリング
        if (!this.chatMessages || !this.messageInput || !this.sendButton) {
            console.error("重要な要素が見つかりません");
            this.showError("チャット要素の初期化に失敗しました");
            return false;
        }
        
        console.log("すべての要素が正常に取得されました");
        return true;
    }
    
    bindEvents() {
        console.log("イベントのバインド中...");
        
        // 送信ボタンのクリックイベント
        this.sendButton.addEventListener('click', (e) => {
            e.preventDefault();
            console.log("送信ボタンクリック");
            this.sendMessage();
        });
        
        // Enterキーの処理
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log("Enterキー押下");
                this.sendMessage();
            }
        });
        
        // フォーカス処理
        this.messageInput.addEventListener('focus', () => {
            console.log("入力フィールドにフォーカス");
        });
        
        console.log("イベントバインド完了");
    }
    
    async sendMessage() {
        if (this.isLoading) {
            console.log("送信処理中です");
            return;
        }
        
        const message = this.messageInput.value.trim();
        console.log("送信メッセージ:", message);
        
        if (!message) {
            console.log("メッセージが空です");
            return;
        }
        
        // UI更新
        this.addUserMessage(message);
        this.messageInput.value = '';
        this.setLoading(true);
        this.showTypingIndicator();
        
        try {
            console.log("API呼び出し開始:", this.config.apiUrl);
            
            const response = await fetch(this.config.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.config.sessionId
                })
            });
            
            console.log("API応答ステータス:", response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log("API応答データ:", data);
            
            this.hideTypingIndicator();
            
            if (data.success && data.response) {
                // APIレスポンスの構造に対応
                const answer = typeof data.response === 'string' 
                    ? data.response 
                    : data.response.answer || data.response;
                    
                this.addAssistantMessage(answer || 'すみません、回答を生成できませんでした。');
            } else {
                throw new Error(data.error || '不明なエラーが発生しました');
            }
            
        } catch (error) {
            console.error('チャットAPI呼び出しエラー:', error);
            this.hideTypingIndicator();
            this.addAssistantMessage(`申し訳ございません、エラーが発生しました: ${error.message}`);
        } finally {
            this.setLoading(false);
        }
    }
    
    addUserMessage(message) {
        const messageElement = this.createMessageElement('user', message);
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    addAssistantMessage(message) {
        const messageElement = this.createMessageElement('assistant', message);
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    createMessageElement(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const timestamp = new Date().toLocaleTimeString();
        const senderName = sender === 'user' ? 'あなた' : 'アシスタント';
        const icon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <strong><i class="${icon}"></i> ${senderName}</strong>
                <div class="mt-2">${this.formatMessage(message)}</div>
            </div>
            <div class="message-time">${timestamp}</div>
        `;
        
        return messageDiv;
    }
    
    formatMessage(message) {
        // HTMLエスケープ
        const div = document.createElement('div');
        div.textContent = message;
        let escaped = div.innerHTML;
        
        // Markdown風のフォーマットを適用
        escaped = escaped
            // 見出し（##）
            .replace(/^## (.+)$/gm, '<h4 style="color: #2d3748; margin: 12px 0 8px 0; font-weight: 600;">$1</h4>')
            // 見出し（###）
            .replace(/^### (.+)$/gm, '<h5 style="color: #4a5568; margin: 10px 0 6px 0; font-weight: 600;">$1</h5>')
            // 太字（**text**）
            .replace(/\*\*(.+?)\*\*/g, '<strong style="color: #2d3748;">$1</strong>')
            // リストアイテム（- item）
            .replace(/^- (.+)$/gm, '<div style="margin: 4px 0; padding-left: 16px;">• $1</div>')
            // 改行を<br>に変換
            .replace(/\n/g, '<br>');
        
        return escaped;
    }
    
    showTypingIndicator() {
        const existingIndicator = document.querySelector('.typing-indicator');
        if (existingIndicator) {
            return;
        }
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant-message';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.closest('.message').remove();
        }
    }
    
    setLoading(loading) {
        console.log("Loading状態変更:", loading);
        this.isLoading = loading;
        
        if (this.sendButton) {
            this.sendButton.disabled = loading;
            const icon = this.sendButton.querySelector('i');
            if (icon) {
                icon.className = loading ? 'fas fa-spinner fa-spin' : 'fas fa-paper-plane';
            }
        }
        
        if (this.messageInput) {
            this.messageInput.disabled = loading;
        }
    }
    
    scrollToBottom() {
        if (this.chatMessages) {
            setTimeout(() => {
                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
            }, 100);
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                     document.querySelector('meta[name="csrf-token"]')?.content ||
                     '';
        
        if (this.config.debug) {
            console.log("CSRF Token:", token ? "取得済み" : "未取得");
        }
        
        return token;
    }
    
    showError(message) {
        console.error("Error:", message);
        if (this.chatMessages) {
            this.addAssistantMessage(`システムエラー: ${message}`);
        }
    }
}

// DOM読み込み完了後に初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM読み込み完了 - Advisor チャット初期化開始");
    
    // チャット要素の存在確認
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        console.log("チャット要素が見つかりました - AdvisorChatManager開始");
        window.advisorChatManager = new AdvisorChatManager();
    } else {
        console.log("チャット要素が見つかりません - 通常ページ");
    }
});

console.log("Advisor Enhanced Chat JS 読み込み完了");