
// static/js/main.js - 基本的なJavaScript

console.log("メイン JavaScript ファイルが読み込まれました");

// 共通のユーティリティ関数
window.utils = {
    // CSRF トークンの取得
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    },
    
    // 簡単な通知表示
    showNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // 簡単なアラート表示（後で改善可能）
        if (type === 'error') {
            alert(`エラー: ${message}`);
        } else if (type === 'success') {
            console.log(`成功: ${message}`);
        }
    },
    
    // 読み込み状態の管理
    setLoading(element, isLoading) {
        if (element) {
            element.disabled = isLoading;
            if (isLoading) {
                element.textContent = '処理中...';
            }
        }
    }
};

// DOM読み込み完了後の初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM読み込み完了");
    
    // 基本的なフォーム処理
    const forms = document.querySelectorAll('form[data-ajax]');
    forms.forEach(form => {
        form.addEventListener('submit', handleAjaxForm);
    });
});

// Ajax フォーム処理
function handleAjaxForm(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const url = form.action || window.location.href;
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': window.utils.getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.utils.showNotification('送信完了', 'success');
        } else {
            window.utils.showNotification(data.error || '送信エラー', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        window.utils.showNotification('ネットワークエラー', 'error');
    });
}
