/**
 * Enhanced Chat Interface JavaScript
 * 改良版チャットインターフェース
 */

class EnhancedChatInterface {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.isTyping = false;
        this.conversationHistory = [];
        this.messageQueue = [];
        this.isProcessingQueue = false;
        this.settings = {
            autoScroll: true,
            soundEnabled: false,
            animationsEnabled: true,
            typingSpeed: 50, // ms per character
            maxRetries: 3
        };
        
        this.init();
    }

    /**
     * 初期化メソッド
     */
    init() {
        this.initializeEventListeners();
        this.initializeElements();
        this.loadSettings();
        this.setupKeyboardShortcuts();
        this.startHeartbeat();
        
        // アクセシビリティの改善
        this.setupAccessibility();
        
        // パフォーマンス監視
        this.setupPerformanceMonitoring();
    }

    /**
     * 要素の初期化
     */
    initializeElements() {
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-chat');
        this.chatMessages = document.getElementById('chat-messages');
        this.welcomeScreen = document.getElementById('welcome-screen');
        
        // 要素が存在しない場合のエラーハンドリング
        if (!this.chatInput || !this.sendButton || !this.chatMessages) {
            console.error('Required chat elements not found');
            return;
        }
        
        this.autoResizeTextarea();
        this.updateSendButtonState();
    }

    /**
     * イベントリスナーの設定
     */
    initializeEventListeners() {
        // 送信ボタン
        this.sendButton?.addEventListener('click', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // テキストエリアのイベント
        this.chatInput?.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.chatInput?.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateSendButtonState();
            this.handleTypingIndicator();
        });
        this.chatInput?.addEventListener('paste', (e) => this.handlePaste(e));

        // ウィンドウイベント
        window.addEventListener('beforeunload', () => this.saveConversation());
        window.addEventListener('online', () => this.handleOnlineStatus(true));
        window.addEventListener('offline', () => this.handleOnlineStatus(false));
        
        // Intersection Observer for auto-scroll
        if (this.chatMessages) {
            this.setupScrollObserver();
        }
    }

    /**
     * キーボードショートカットの設定
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Enter で送信
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                this.sendMessage();
            }
            
            // Escape でフォーカスをリセット
            if (e.key === 'Escape') {
                this.chatInput?.blur();
            }
        });
    }

    /**
     * アクセシビリティの設定
     */
    setupAccessibility() {
        // スクリーンリーダー用のlive region
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        liveRegion.id = 'chat-live-region';
        document.body.appendChild(liveRegion);
        
        // キーボードナビゲーション
        this.chatMessages?.setAttribute('role', 'log');
        this.chatMessages?.setAttribute('aria-label', '会話履歴');
        
        this.chatInput?.setAttribute('aria-label', 'メッセージを入力');
        this.sendButton?.setAttribute('aria-label', 'メッセージを送信');
    }

    /**
     * パフォーマンス監視の設定
     */
    setupPerformanceMonitoring() {
        this.performance = {
            messageCount: 0,
            totalResponseTime: 0,
            averageResponseTime: 0,
            errors: 0
        };
    }

    /**
     * スクロール監視の設定
     */
    setupScrollObserver() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                this.settings.autoScroll = entry.isIntersecting;
            });
        }, { threshold: 0.1 });

        // ダミー要素を作成してスクロール位置を監視
        const scrollSentinel = document.createElement('div');
        scrollSentinel.style.height = '1px';
        scrollSentinel.style.marginTop = '-1px';
        this.chatMessages.appendChild(scrollSentinel);
        observer.observe(scrollSentinel);
    }

    /**
     * セッションIDの生成
     */
    generateSessionId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 9);
        return `enhanced_chat_${timestamp}_${random}`;
    }

    /**
     * キーダウンイベントの処理
     */
    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    /**
     * ペーストイベントの処理
     */
    handlePaste(e) {
        // 画像ペーストの場合の処理（将来の機能拡張用）
        const items = e.clipboardData?.items;
        if (items) {
            for (let item of items) {
                if (item.type.indexOf('image') !== -1) {
                    e.preventDefault();
                    this.showMessage('画像の送信は現在サポートされていません。', 'warning');
                    return;
                }
            }
        }
    }

    /**
     * タイピングインジケーターの処理
     */
    handleTypingIndicator() {
        // 将来の機能拡張用（リアルタイムタイピング表示）
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
        }
        
        this.typingTimer = setTimeout(() => {
            // タイピング停止の処理
        }, 1000);
    }

    /**
     * オンライン状態の処理
     */
    handleOnlineStatus(isOnline) {
        const statusMessage = isOnline ? 'オンライン状態に復帰しました' : 'オフライン状態です';
        const messageType = isOnline ? 'success' : 'warning';
        
        this.showMessage(statusMessage, messageType);
        this.updateConnectionStatus(isOnline);
    }

    /**
     * 接続状態の更新
     */
    updateConnectionStatus(isOnline) {
        const statusIndicator = document.querySelector('.status-indicator');
        if (statusIndicator) {
            statusIndicator.style.background = isOnline ? '#38a169' : '#e53e3e';
        }
        
        const statusText = document.querySelector('.chat-status span');
        if (statusText) {
            statusText.textContent = isOnline ? 'AIアドバイザーがオンラインです' : 'オフライン状態です';
        }
    }

    /**
     * テキストエリアの自動リサイズ
     */
    autoResizeTextarea() {
        if (!this.chatInput) return;
        
        this.chatInput.style.height = 'auto';
        const newHeight = Math.min(this.chatInput.scrollHeight, 120);
        this.chatInput.style.height = newHeight + 'px';
    }

    /**
     * 送信ボタンの状態更新
     */
    updateSendButtonState() {
        if (!this.sendButton || !this.chatInput) return;
        
        const hasText = this.chatInput.value.trim().length > 0;
        const isEnabled = hasText && !this.isTyping && navigator.onLine;
        
        this.sendButton.disabled = !isEnabled;
        this.sendButton.setAttribute('aria-disabled', (!isEnabled).toString());
    }

    /**
     * メッセージ送信
     */
    async sendMessage(retryCount = 0) {
        const message = this.chatInput?.value.trim();
        
        if (!message || this.isTyping) return;
        
        // 入力値の検証
        if (message.length > 1000) {
            this.showMessage('メッセージは1000文字以内で入力してください。', 'warning');
            return;
        }

        // ウェルカムスクリーンを非表示
        this.hideWelcomeScreen();

        // ユーザーメッセージを表示
        this.addMessageToChat('user', message);
        this.clearInput();

        // パフォーマンス測定開始
        const startTime = performance.now();

        try {
            // タイピングインジケーターを表示
            this.showTypingIndicator();
            
            const response = await this.callChatAPI(message);
            
            // レスポンス時間を記録
            const responseTime = performance.now() - startTime;
            this.updatePerformanceMetrics(responseTime);
            
            this.hideTypingIndicator();
            
            if (response.success) {
                await this.typewriterEffect(response.response.answer);
                this.announceToScreenReader(`AIの回答: ${response.response.answer.substring(0, 100)}...`);
            } else {
                throw new Error(response.error || 'Unknown error');
            }
            
        } catch (error) {
            this.hideTypingIndicator();
            this.handleError(error, retryCount, message);
        }
    }

    /**
     * エラーハンドリング
     */
    handleError(error, retryCount, originalMessage) {
        console.error('Chat API Error:', error);
        this.performance.errors++;
        
        if (retryCount < this.settings.maxRetries && navigator.onLine) {
            setTimeout(() => {
                this.sendMessage(retryCount + 1);
            }, Math.pow(2, retryCount) * 1000); // 指数バックオフ
            
            this.showMessage(`再試行中... (${retryCount + 1}/${this.settings.maxRetries})`, 'info');
        } else {
            const errorMessage = this.getErrorMessage(error);
            this.addMessageToChat('assistant', errorMessage);
            this.showMessage('エラーが発生しました', 'error');
        }
    }

    /**
     * エラーメッセージの取得
     */
    getErrorMessage(error) {
        if (!navigator.onLine) {
            return 'インターネット接続を確認してください。オフライン状態では回答できません。';
        }
        
        if (error.name === 'TimeoutError') {
            return 'リクエストがタイムアウトしました。もう一度お試しください。';
        }
        
        if (error.status === 429) {
            return 'リクエストが多すぎます。しばらく待ってからお試しください。';
        }
        
        if (error.status >= 500) {
            return 'サーバーエラーが発生しました。しばらく待ってからお試しください。';
        }
        
        return '申し訳ございません。技術的な問題が発生しました。しばらく待ってからお試しください。';
    }

    /**
     * パフォーマンス指標の更新
     */
    updatePerformanceMetrics(responseTime) {
        this.performance.messageCount++;
        this.performance.totalResponseTime += responseTime;
        this.performance.averageResponseTime = this.performance.totalResponseTime / this.performance.messageCount;
        
        // コンソールに統計情報を出力（開発用）
        if (this.performance.messageCount % 10 === 0) {
            console.log('Chat Performance:', {
                messages: this.performance.messageCount,
                avgResponseTime: Math.round(this.performance.averageResponseTime),
                errors: this.performance.errors,
                errorRate: (this.performance.errors / this.performance.messageCount * 100).toFixed(2) + '%'
            });
        }
    }

    /**
     * Chat API呼び出し（フォールバック対応）
     */
    async callChatAPI(message) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒タイムアウト

        try {
            // まず enhanced-chat API を試行
            const response = await fetch('/advisor/api/enhanced-chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    user_context: this.getUserContext()
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                // enhanced-chat が失敗した場合、従来の analyze API にフォールバック
                return await this.fallbackToAnalyzeAPI(message);
            }

            return await response.json();
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            
            // ネットワークエラーの場合、フォールバックを試行
            try {
                return await this.fallbackToAnalyzeAPI(message);
            } catch (fallbackError) {
                throw error; // 元のエラーを投げる
            }
        }
    }

    /**
     * 従来のanalyze APIへのフォールバック
     */
    async fallbackToAnalyzeAPI(message) {
        try {
            const response = await fetch('/advisor/api/analyze/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    question: message,
                    session_id: this.sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // レスポンス形式を enhanced-chat 形式に変換
            return {
                success: true,
                response: {
                    answer: data.answer || '申し訳ございません。回答を生成できませんでした。',
                    recommended_subsidies: data.recommended_subsidies || [],
                    confidence_score: data.confidence_score || 0.5,
                    model_used: 'fallback-analyze'
                }
            };
            
        } catch (error) {
            console.warn('Fallback API also failed:', error);
            throw error;
        }
    }

    /**
     * ユーザーコンテキストの取得
     */
    getUserContext() {
        return {
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            language: navigator.language,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            messageCount: this.performance.messageCount
        };
    }

    /**
     * CSRFトークンの取得
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    /**
     * 入力フィールドのクリア
     */
    clearInput() {
        if (this.chatInput) {
            this.chatInput.value = '';
            this.autoResizeTextarea();
            this.updateSendButtonState();
        }
    }

    /**
     * ウェルカムスクリーンの非表示
     */
    hideWelcomeScreen() {
        if (this.welcomeScreen) {
            this.welcomeScreen.style.display = 'none';
        }
    }

    /**
     * タイピングインジケーターの表示
     */
    showTypingIndicator() {
        this.isTyping = true;
        this.updateSendButtonState();
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-content">
                <span>AIが回答を作成中</span>
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        this.chatMessages?.appendChild(typingDiv);
        this.scrollToBottom();
    }

    /**
     * タイピングインジケーターの非表示
     */
    hideTypingIndicator() {
        this.isTyping = false;
        this.updateSendButtonState();
        
        const typingIndicator = document.getElementById('typing-indicator');
        typingIndicator?.remove();
    }

    /**
     * タイプライター効果でメッセージを表示
     */
    async typewriterEffect(content) {
        if (!this.settings.animationsEnabled) {
            this.addMessageToChat('assistant', content);
            return;
        }

        // メッセージコンテナを作成
        const messageDiv = this.createMessageElement('assistant', '');
        this.chatMessages?.appendChild(messageDiv);
        
        const messageTextElement = messageDiv.querySelector('.message-text');
        if (!messageTextElement) return;

        // HTMLタグを保持しながらタイプライター効果を実現
        const formattedContent = this.formatAssistantMessage(content);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = formattedContent;
        
        let displayText = '';
        const textContent = tempDiv.textContent || tempDiv.innerText || '';
        
        for (let i = 0; i < textContent.length; i++) {
            displayText += textContent[i];
            messageTextElement.textContent = displayText;
            
            if (this.settings.autoScroll) {
                this.scrollToBottom();
            }
            
            // 句読点で少し長めの間隔
            const delay = /[。、！？\.\!\?]/.test(textContent[i]) ? 
                         this.settings.typingSpeed * 3 : this.settings.typingSpeed;
            
            await this.sleep(delay);
        }
        
        // 最終的にHTMLフォーマットを適用
        messageTextElement.innerHTML = formattedContent;
        this.scrollToBottom();
    }

    /**
     * sleep関数
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * メッセージ要素の作成
     */
    createMessageElement(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}-message slide-up`;
        
        const timestamp = new Date().toLocaleTimeString('ja-JP', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        if (type === 'user') {
            messageDiv.innerHTML = `
                <div class="message-content user-content">
                    <div class="message-text">${this.escapeHtml(content)}</div>
                    <div class="message-time">${timestamp}</div>
                </div>
                <div class="message-avatar user-avatar">
                    <i class="fas fa-user"></i>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-avatar assistant-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content assistant-content">
                    <div class="message-text">${this.formatAssistantMessage(content)}</div>
                    <div class="message-time">${timestamp}</div>
                </div>
            `;
        }
        
        return messageDiv;
    }

    /**
     * チャットにメッセージを追加
     */
    addMessageToChat(type, content) {
        const messageDiv = this.createMessageElement(type, content);
        this.chatMessages?.appendChild(messageDiv);
        
        if (this.settings.autoScroll) {
            this.scrollToBottom();
        }
        
        // 会話履歴に追加
        this.conversationHistory.push({
            type: type,
            content: content,
            timestamp: new Date()
        });
        
        // ローカルストレージに保存
        this.saveConversation();
    }

    /**
     * アシスタントメッセージのフォーマット
     */
    formatAssistantMessage(content) {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^### (.*$)/gm, '<h4>$1</h4>')
            .replace(/^## (.*$)/gm, '<h3>$1</h3>')
            .replace(/^# (.*$)/gm, '<h2>$1</h2>')
            .replace(/^\* (.+$)/gm, '<li>$1</li>')
            .replace(/^(\d+)\. (.+$)/gm, '<li>$1. $2</li>')
            .replace(/(<li>.*<\/li>)/gs, (match) => {
                if (!match.includes('<ul>') && !match.includes('<ol>')) {
                    return `<ul>${match}</ul>`;
                }
                return match;
            })
            .replace(/^> (.+$)/gm, '<blockquote>$1</blockquote>');
    }

    /**
     * HTMLエスケープ
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 底部へスクロール
     */
    scrollToBottom() {
        if (this.chatMessages && this.settings.autoScroll) {
            requestAnimationFrame(() => {
                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
            });
        }
    }

    /**
     * スクリーンリーダーへの通知
     */
    announceToScreenReader(message) {
        const liveRegion = document.getElementById('chat-live-region');
        if (liveRegion) {
            liveRegion.textContent = message;
            setTimeout(() => {
                liveRegion.textContent = '';
            }, 1000);
        }
    }

    /**
     * 通知メッセージの表示
     */
    showMessage(message, type = 'info', duration = 5000) {
        // トースト通知の作成
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${this.getIconForType(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // トーストコンテナがない場合は作成
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                pointer-events: none;
            `;
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.appendChild(toast);
        
        // 自動削除
        setTimeout(() => {
            toast.remove();
        }, duration);
    }

    /**
     * タイプに応じたアイコンの取得
     */
    getIconForType(type) {
        const icons = {
            'info': 'info-circle',
            'success': 'check-circle',
            'warning': 'exclamation-triangle',
            'error': 'times-circle'
        };
        return icons[type] || 'info-circle';
    }

    /**
     * 設定の読み込み
     */
    loadSettings() {
        try {
            const savedSettings = localStorage.getItem('chatSettings');
            if (savedSettings) {
                this.settings = { ...this.settings, ...JSON.parse(savedSettings) };
            }
        } catch (error) {
            console.warn('Failed to load settings:', error);
        }
    }

    /**
     * 設定の保存
     */
    saveSettings() {
        try {
            localStorage.setItem('chatSettings', JSON.stringify(this.settings));
        } catch (error) {
            console.warn('Failed to save settings:', error);
        }
    }

    /**
     * 会話の保存
     */
    saveConversation() {
        try {
            const conversationData = {
                sessionId: this.sessionId,
                history: this.conversationHistory,
                timestamp: new Date().toISOString()
            };
            localStorage.setItem('lastConversation', JSON.stringify(conversationData));
        } catch (error) {
            console.warn('Failed to save conversation:', error);
        }
    }

    /**
     * ハートビートの開始
     */
    startHeartbeat() {
        setInterval(() => {
            this.updateConnectionStatus(navigator.onLine);
        }, 30000); // 30秒ごと
    }

    /**
     * クリーンアップ
     */
    destroy() {
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
        }
        
        // イベントリスナーの削除
        this.sendButton?.removeEventListener('click', this.sendMessage);
        this.chatInput?.removeEventListener('keydown', this.handleKeyDown);
        this.chatInput?.removeEventListener('input', this.autoResizeTextarea);
        
        // 保存
        this.saveSettings();
        this.saveConversation();
    }
}

/**
 * クイックアクション用のグローバル関数
 */
function sendQuickMessage(message) {
    if (window.chatInterface) {
        window.chatInterface.chatInput.value = message;
        window.chatInterface.sendMessage();
    }
}

/**
 * 設定変更用のグローバル関数
 */
function toggleChatSettings() {
    if (window.chatInterface) {
        const settings = window.chatInterface.settings;
        settings.animationsEnabled = !settings.animationsEnabled;
        window.chatInterface.saveSettings();
        window.chatInterface.showMessage(
            `アニメーション: ${settings.animationsEnabled ? 'ON' : 'OFF'}`, 
            'info'
        );
    }
}

/**
 * ページ読み込み時の初期化
 */
document.addEventListener('DOMContentLoaded', function() {
    try {
        window.chatInterface = new EnhancedChatInterface();
        
        // グローバルエラーハンドラ
        window.addEventListener('error', (e) => {
            console.error('Global error:', e);
            if (window.chatInterface) {
                window.chatInterface.showMessage('予期しないエラーが発生しました', 'error');
            }
        });
        
        // Unhandled promise rejection
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled promise rejection:', e);
            if (window.chatInterface) {
                window.chatInterface.showMessage('ネットワークエラーが発生しました', 'error');
            }
        });
        
    } catch (error) {
        console.error('Failed to initialize chat interface:', error);
    }
});

/**
 * ページアンロード時のクリーンアップ
 */
window.addEventListener('beforeunload', function() {
    if (window.chatInterface) {
        window.chatInterface.destroy();
    }
});