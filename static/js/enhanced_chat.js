class EnhancedChatInterface {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.conversationHistory = [];
        this.isTyping = false;
        this.setupEventListeners();
        this.setupStreamingChat();
    }
    
    generateSessionId() {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    setupEventListeners() {
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-chat');
        
        // Enter キーでの送信
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // 送信ボタンクリック
        sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // 入力中の表示
        chatInput.addEventListener('input', () => {
            this.handleTypingIndicator();
        });
    }
    
    setupStreamingChat() {
        // WebSocket または Server-Sent Events の設定
        // リアルタイム回答のための準備
        this.streamingEnabled = true;
    }
    
    async sendMessage() {
        const chatInput = document.getElementById('chat-input');
        const message = chatInput.value.trim();
        
        if (!message) return;
        
        // ユーザーメッセージを表示
        this.addMessageToChat('user', message);
        
        // 入力欄をクリア
        chatInput.value = '';
        
        // タイピングインジケーター表示
        this.showTypingIndicator();
        
        try {
            // ユーザーコンテキストの取得
            const userContext = this.getUserContext();
            
            // APIリクエスト
            const response = await fetch('/api/enhanced-chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    user_context: userContext
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideTypingIndicator();
                this.addMessageToChat('assistant', data.response.answer);
                
                // 推奨補助金があれば表示
                if (data.response.recommended_subsidies && data.response.recommended_subsidies.length > 0) {
                    this.showRecommendedSubsidies(data.response.recommended_subsidies);
                }
                
                // 信頼度スコアの表示
                this.showConfidenceScore(data.response.confidence_score);
                
            } else {
                this.hideTypingIndicator();
                this.addMessageToChat('assistant', 'エラーが発生しました。もう一度お試しください。');
            }
            
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            this.addMessageToChat('assistant', '接続エラーが発生しました。');
        }
    }
    
    addMessageToChat(type, content) {
        const chatContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}-message`;
        
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
                <div class="message-avatar user-avatar">👤</div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-avatar assistant-avatar">🤖</div>
                <div class="message-content assistant-content">
                    <div class="message-text">${this.formatAssistantMessage(content)}</div>
                    <div class="message-time">${timestamp}</div>
                </div>
            `;
        }
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // 会話履歴に追加
        this.conversationHistory.push({
            type: type,
            content: content,
            timestamp: new Date()
        });
    }
    
    formatAssistantMessage(content) {
        // Markdownライクな書式を HTML に変換
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/###\s*(.*)/g, '<h4>$1</h4>')
            .replace(/##\s*(.*)/g, '<h3>$1</h3>')
            .replace(/---/g, '<hr>');
    }
    
    showTypingIndicator() {
        const chatContainer = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'chat-message assistant-message typing';
        typingDiv.innerHTML = `
            <div class="message-avatar assistant-avatar">🤖</div>
            <div class="message-content assistant-content">
                <div class="typing-animation">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        
        chatContainer.appendChild(typingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    showRecommendedSubsidies(subsidies) {
        const recommendationsDiv = document.createElement('div');
        recommendationsDiv.className = 'recommended-subsidies';
        
        let html = '<div class="recommendations-header">💡 おすすめの補助金</div>';
        
        subsidies.forEach(subsidy => {
            html += `
                <div class="subsidy-recommendation">
                    <h4>${subsidy.name}</h4>
                    <p>${subsidy.description}</p>
                    <div class="subsidy-details">
                        <span class="budget">💰 最大${subsidy.max_amount.toLocaleString()}万円</span>
                        <span class="target">🎯 ${subsidy.target_business_type}</span>
                    </div>
                </div>
            `;
        });
        
        const chatContainer = document.getElementById('chat-messages');
        chatContainer.appendChild(recommendationsDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    showConfidenceScore(score) {
        if (!score || score < 0.5) return;
        
        const scoreDiv = document.createElement('div');
        scoreDiv.className = 'confidence-score';
        
        const percentage = Math.round(score * 100);
        const scoreClass = score >= 0.8 ? 'high' : score >= 0.6 ? 'medium' : 'low';
        
        scoreDiv.innerHTML = `
            <div class="confidence-indicator ${scoreClass}">
                信頼度: ${percentage}% 
                <span class="confidence-bar">
                    <span class="confidence-fill" style="width: ${percentage}%"></span>
                </span>
            </div>
        `;
        
        const lastMessage = document.querySelector('.chat-message:last-child .message-content');
        if (lastMessage) {
            lastMessage.appendChild(scoreDiv);
        }
    }
    
    getUserContext() {
        // フォームから現在のユーザー情報を取得
        return {
            business_type: document.getElementById('business-type')?.value || '',
            company_size: document.getElementById('company-size')?.value || '',
            region: document.getElementById('region')?.value || '',
            industry: document.getElementById('industry')?.value || ''
        };
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

// 補助金予測カレンダー機能
class SubsidyPredictionCalendar {
    constructor() {
        this.currentDate = new Date();
        this.predictions = {};
        this.alerts = [];
        this.setupCalendar();
        this.loadPredictions();
    }
    
    async loadPredictions() {
        try {
            const response = await fetch('/api/subsidy-predictions/');
            const data = await response.json();
            
            if (data.success) {
                this.predictions = data.data.calendar;
                this.alerts = data.data.alerts;
                this.trends = data.data.trends;
                
                this.renderCalendar();
                this.showAlerts();
                this.showTrends();
            }
        } catch (error) {
            console.error('Failed to load predictions:', error);
        }
    }
    
    setupCalendar() {
        this.calendarContainer = document.getElementById('prediction-calendar');
        if (!this.calendarContainer) {
            console.warn('Calendar container not found');
            return;
        }
        
        // カレンダーヘッダー
        const header = document.createElement('div');
        header.className = 'calendar-header';
        header.innerHTML = `
            <div class="calendar-nav">
                <button id="prev-month">‹</button>
                <h3 id="current-month"></h3>
                <button id="next-month">›</button>
            </div>
            <div class="calendar-legend">
                <span class="legend-item high">🔴 高確率</span>
                <span class="legend-item medium">🟡 中確率</span>
                <span class="legend-item low">🟢 低確率</span>
            </div>
        `;
        
        this.calendarContainer.appendChild(header);
        
        // ナビゲーションイベント
        document.getElementById('prev-month').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this.renderCalendar();
        });
        
        document.getElementById('next-month').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this.renderCalendar();
        });
    }
    
    renderCalendar() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const monthKey = `${year}-${String(month + 1).padStart(2, '0')}`;
        
        // 月表示更新
        document.getElementById('current-month').textContent = 
            `${year}年${month + 1}月`;
        
        // カレンダーグリッド
        let calendarGrid = document.getElementById('calendar-grid');
        if (calendarGrid) {
            calendarGrid.remove();
        }
        
        calendarGrid = document.createElement('div');
        calendarGrid.id = 'calendar-grid';
        calendarGrid.className = 'calendar-grid';
        
        // 曜日ヘッダー
        const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
        weekdays.forEach(day => {
            const dayHeader = document.createElement('div');
            dayHeader.className = 'calendar-day-header';
            dayHeader.textContent = day;
            calendarGrid.appendChild(dayHeader);
        });
        
        // 日付セル
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());
        
        for (let i = 0; i < 42; i++) {
            const cellDate = new Date(startDate);
            cellDate.setDate(startDate.getDate() + i);
            
            const dayCell = this.createDayCell(cellDate, monthKey);
            calendarGrid.appendChild(dayCell);
        }
        
        this.calendarContainer.appendChild(calendarGrid);
        
        // 月の詳細情報
        this.renderMonthDetails(monthKey);
    }
    
    createDayCell(date, monthKey) {
        const dayCell = document.createElement('div');
        dayCell.className = 'calendar-day';
        
        const isCurrentMonth = date.getMonth() === this.currentDate.getMonth();
        const isToday = this.isToday(date);
        
        if (!isCurrentMonth) {
            dayCell.classList.add('other-month');
        }
        if (isToday) {
            dayCell.classList.add('today');
        }
        
        dayCell.innerHTML = `<span class="day-number">${date.getDate()}</span>`;
        
        // 予測データがある場合
        const predictions = this.getPredictionsForDate(date);
        if (predictions.length > 0) {
            dayCell.classList.add('has-predictions');
            
            const indicator = document.createElement('div');
            indicator.className = 'prediction-indicator';
            
            const highPriority = predictions.filter(p => p.recommendation_priority >= 0.7).length;
            if (highPriority > 0) {
                indicator.classList.add('high-priority');
                indicator.innerHTML = '🔴';
            } else {
                indicator.classList.add('medium-priority');
                indicator.innerHTML = '🟡';
            }
            
            dayCell.appendChild(indicator);
            
            // クリックイベント
            dayCell.addEventListener('click', () => {
                this.showDayDetails(date, predictions);
            });
        }
        
        return dayCell;
    }
    
    getPredictionsForDate(date) {
        const dateKey = date.toISOString().split('T')[0];
        
        // 全予測データから該当日のものを抽出
        let dayPredictions = [];
        
        Object.values(this.predictions).forEach(monthData => {
            if (monthData.opportunities) {
                dayPredictions = dayPredictions.concat(
                    monthData.opportunities.filter(pred => {
                        const predDate = new Date(pred.predicted_date);
                        return predDate.toISOString().split('T')[0] === dateKey;
                    })
                );
            }
        });
        
        return dayPredictions;
    }
    
    showDayDetails(date, predictions) {
        const modal = document.createElement('div');
        modal.className = 'prediction-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${date.toLocaleDateString('ja-JP')} の補助金予測</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    ${this.renderPredictionsList(predictions)}
                </div>
            </div>
        `;
        
        // モーダル表示
        document.body.appendChild(modal);
        
        // 閉じるイベント
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    renderPredictionsList(predictions) {
        if (predictions.length === 0) {
            return '<p>この日の予測はありません。</p>';
        }
        
        let html = '<div class="predictions-list">';
        
        predictions.forEach(pred => {
            const confidenceClass = pred.confidence >= 0.8 ? 'high' : 
                                  pred.confidence >= 0.6 ? 'medium' : 'low';
            
            html += `
                <div class="prediction-item">
                    <h4>${pred.subsidy_name}</h4>
                    <div class="prediction-stats">
                        <span class="confidence ${confidenceClass}">
                            信頼度: ${Math.round(pred.confidence * 100)}%
                        </span>
                        <span class="success-rate">
                            成功率: ${Math.round(pred.success_probability * 100)}%
                        </span>
                    </div>
                    <div class="prediction-details">
                        <p>💰 予算: ${pred.estimated_budget?.toLocaleString() || '未定'}万円</p>
                        <p>📅 準備期限: ${new Date(pred.preparation_deadline).toLocaleDateString('ja-JP')}</p>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    showAlerts() {
        const alertsContainer = document.getElementById('prediction-alerts');
        if (!alertsContainer || this.alerts.length === 0) return;
        
        let alertsHtml = '<div class="alerts-header"><h3>🚨 重要なお知らせ</h3></div>';
        
        this.alerts.forEach(alert => {
            const priorityIcon = alert.priority === 'high' ? '🔴' : 
                               alert.priority === 'medium' ? '🟡' : '🟢';
            
            alertsHtml += `
                <div class="alert-item ${alert.priority}">
                    <div class="alert-header">
                        ${priorityIcon} ${alert.message}
                    </div>
                    <div class="alert-action">
                        ${alert.action_required}
                    </div>
                </div>
            `;
        });
        
        alertsContainer.innerHTML = alertsHtml;
    }
    
    showTrends() {
        const trendsContainer = document.getElementById('trends-analysis');
        if (!trendsContainer || !this.trends) return;
        
        const trends = this.trends;
        
        let trendsHtml = `
            <div class="trends-header">
                <h3>📊 補助金トレンド分析</h3>
            </div>
            
            <div class="trends-content">
                <div class="trend-section">
                    <h4>季節パターン</h4>
                    <p>最も活発な月: ${trends.seasonal_patterns?.peak_months?.join('、') || '分析中'}</p>
                </div>
                
                <div class="trend-section">
                    <h4>新着チャンス</h4>
                    <div class="emerging-opportunities">
                        ${trends.emerging_opportunities?.map(opp => 
                            `<span class="opportunity-tag">${opp}</span>`
                        ).join('') || '分析中...'}
                    </div>
                </div>
            </div>
        `;
        
        trendsContainer.innerHTML = trendsHtml;
    }
    
    isToday(date) {
        const today = new Date();
        return date.toDateString() === today.toDateString();
    }
    
    renderMonthDetails(monthKey) {
        const monthData = this.predictions[monthKey];
        if (!monthData) return;
        
        const detailsContainer = document.getElementById('month-details');
        if (!detailsContainer) return;
        
        detailsContainer.innerHTML = `
            <div class="month-summary">
                <h4>${monthData.month} の予測サマリー</h4>
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-number">${monthData.total_opportunities}</span>
                        <span class="stat-label">予測案件数</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${monthData.high_priority_count}</span>
                        <span class="stat-label">高優先度案件</span>
                    </div>
                </div>
            </div>
        `;
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    // 強化チャット機能の初期化
    if (document.getElementById('chat-input')) {
        window.enhancedChat = new EnhancedChatInterface();
    }
    
    // 予測カレンダーの初期化
    if (document.getElementById('prediction-calendar')) {
        window.predictionCalendar = new SubsidyPredictionCalendar();
    }
});