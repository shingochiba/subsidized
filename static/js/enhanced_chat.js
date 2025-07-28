// static/js/enhanced_chat.js - エラー修正版
console.log("Enhanced Chat JS 読み込み開始");

class EnhancedChatInterface {
    constructor() {
        console.log("EnhancedChatInterface 初期化中...");
        
        this.apiUrl = '/advisor/api/enhanced-chat/';
        this.sessionId = this.generateSessionId();
        this.isLoading = false;
        
        this.initializeElements();
        this.bindEvents();
        
        console.log("EnhancedChatInterface 初期化完了");
        this.addMessageToChat('assistant', 'こんにちは！補助金について何でもお聞きください。');
    }
    
    initializeElements() {
        console.log("要素の初期化中...");
        
        // 基本要素の取得（複数のID候補をチェック）
        this.chatMessages = document.getElementById('chat-messages') || 
                           document.querySelector('.chat-messages') ||
                           document.querySelector('#chatMessages');
                           
        this.messageInput = document.getElementById('message-input') || 
                          document.getElementById('chat-input') ||
                          document.querySelector('input[type="text"]');
                          
        this.sendButton = document.getElementById('send-button') || 
                         document.getElementById('sendButton') ||
                         document.querySelector('button[type="submit"]');
        
        console.log("Chat Messages:", this.chatMessages);
        console.log("Message Input:", this.messageInput);
        console.log("Send Button:", this.sendButton);
        
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
        
        if (this.sendButton) {
            this.sendButton.addEventListener('click', (e) => {
                e.preventDefault();
                console.log("送信ボタンクリック");
                this.sendMessage();
            });
        }
        
        if (this.messageInput) {
            this.messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    console.log("Enterキー押下");
                    this.sendMessage();
                }
            });
            
            this.messageInput.addEventListener('focus', () => {
                console.log("入力フィールドにフォーカス");
            });
        }
        
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
        this.addMessageToChat('user', message);
        this.messageInput.value = '';
        this.setLoading(true);
        this.showTypingIndicator();
        
        try {
            console.log("API呼び出し開始:", this.apiUrl);
            
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
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
                    : data.response.answer || data.response || 'すみません、回答を生成できませんでした。';
                    
                this.addMessageToChat('assistant', answer);
            } else {
                throw new Error(data.error || '不明なエラーが発生しました');
            }
            
        } catch (error) {
            console.error('Chat API Error:', error);
            this.hideTypingIndicator();
            this.addMessageToChat('assistant', `申し訳ございません、エラーが発生しました: ${error.message}`);
        } finally {
            this.setLoading(false);
        }
    }
    
    addMessageToChat(sender, message) {
        console.log(`メッセージ追加: ${sender} - ${message ? message.substring(0, 50) + '...' : 'undefined'}`);
        
        if (!this.chatMessages) {
            console.error("chatMessages要素がありません");
            return;
        }
        
        // メッセージの安全性チェック
        if (typeof message !== 'string') {
            console.warn("メッセージがstring型ではありません:", typeof message, message);
            message = String(message || '回答を取得できませんでした');
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message`;
        
        const timestamp = new Date().toLocaleTimeString();
        const senderName = sender === 'user' ? 'あなた' : 'アシスタント';
        const icon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
        
        // メッセージの内容をフォーマット
        let formattedMessage;
        if (sender === 'assistant') {
            formattedMessage = this.formatAssistantMessage(message);
        } else {
            formattedMessage = this.escapeHtml(message);
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="${icon}"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <strong>${senderName}</strong>
                    <span class="message-time">${timestamp}</span>
                </div>
                <div class="message-text">${formattedMessage}</div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatAssistantMessage(message) {
        // 安全性チェック
        if (typeof message !== 'string') {
            console.warn("formatAssistantMessage: メッセージがstring型ではありません:", typeof message, message);
            return this.escapeHtml(String(message || ''));
        }
        
        // HTMLエスケープ
        let escaped = this.escapeHtml(message);
        
        try {
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
        } catch (error) {
            console.error("Markdown フォーマットエラー:", error);
            // フォーマットに失敗した場合は基本的なHTMLエスケープのみ適用
            escaped = this.escapeHtml(message).replace(/\n/g, '<br>');
        }
        
        return escaped;
    }
    
    escapeHtml(text) {
        // 安全性チェック
        if (typeof text !== 'string') {
            text = String(text || '');
        }
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showTypingIndicator() {
        const existingIndicator = document.querySelector('.typing-indicator');
        if (existingIndicator) {
            return;
        }
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message assistant-message typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-animation">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
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
        
        console.log("CSRF Token:", token ? "取得済み" : "未取得");
        return token;
    }
    
    generateSessionId() {
        const sessionId = `enhanced_chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        console.log("セッションID生成:", sessionId);
        return sessionId;
    }
    
    showError(message) {
        console.error("Error:", message);
        if (this.chatMessages) {
            this.addMessageToChat('assistant', `システムエラー: ${message}`);
        }
    }
}

// DOM読み込み完了後に初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM読み込み完了 - Enhanced チャット初期化開始");
    
    // チャット要素の存在確認
    const chatContainer = document.querySelector('.chat-container') || 
                         document.getElementById('chat-messages') ||
                         document.querySelector('.enhanced-chat-wrapper');
                         
    if (chatContainer) {
        console.log("チャット要素が見つかりました - EnhancedChatInterface開始");
        window.enhancedChatInterface = new EnhancedChatInterface();
    } else {
        console.log("チャット要素が見つかりません - 通常ページ");
    }
});

console.log("Enhanced Chat JS 読み込み完了");