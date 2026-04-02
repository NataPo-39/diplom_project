// chat.js - Логика работы чата

class ChatInterface {
    constructor() {
        this.messageContainer = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.sendButton = document.getElementById('sendButton');
        this.infoPanel = document.getElementById('infoPanel');
        this.collectedDataDiv = document.getElementById('collectedData');

        this.sessionId = 'session_' + Date.now();
        this.isWaiting = false;

        this.init();
    }

    init() {
        // Обработчики событий
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Фокус на поле ввода
        this.userInput.focus();
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message || this.isWaiting) return;

        // Очищаем поле ввода
        this.userInput.value = '';

        // Показываем сообщение пользователя
        this.addMessage(message, 'user');

        // Показываем индикатор печатания
        this.showTypingIndicator();

        // Отправляем запрос
        this.isWaiting = true;
        this.sendButton.disabled = true;

        try {
            const response = await this.callAPI(message);
            this.hideTypingIndicator();
            this.addMessage(response.response, 'assistant');

            // Если нужно передать человеку
            if (response.needs_human) {
                this.showHumanTransfer(response.collected_data);
            }

            // Обновляем панель с собранными данными
            this.updateCollectedData(response.collected_data);

        } catch (error) {
            console.error('Ошибка:', error);
            this.hideTypingIndicator();
            this.addMessage('Извините, произошла ошибка. Попробуйте позже.', 'assistant');
        } finally {
            this.isWaiting = false;
            this.sendButton.disabled = false;
            this.userInput.focus();
        }
    }

    async callAPI(message) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: this.sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;

        messageDiv.appendChild(contentDiv);
        this.messageContainer.appendChild(messageDiv);

        // Скролл вниз
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }

    showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'message assistant';
        indicator.id = 'typingIndicator';

        const content = document.createElement('div');
        content.className = 'typing-indicator';
        content.innerHTML = '<span></span><span></span><span></span>';

        indicator.appendChild(content);
        this.messageContainer.appendChild(indicator);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    showHumanTransfer(data) {
        this.infoPanel.style.display = 'block';
        this.addMessage('Спасибо! Я передал ваши данные специалисту. Он свяжется с вами в ближайшее время.', 'assistant');
    }

    updateCollectedData(data) {
        if (Object.values(data).some(v => v !== null && v !== false)) {
            this.infoPanel.style.display = 'block';
            this.collectedDataDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }
    }
}

// Запускаем чат после загрузки страницы
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});