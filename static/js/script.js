document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    // Hàm để thêm tin nhắn vào khung chat
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        const bubbleDiv = document.createElement('div');
        bubbleDiv.classList.add('message-bubble');
        bubbleDiv.textContent = text;
        messageDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return bubbleDiv;
    }

    // --- HỆ THỐNG "ĐÁNH THỨC" SERVER ---
    function warmUpSystem() {
        console.log("Bắt đầu quá trình 'đánh thức' server...");
        userInput.disabled = true;
        sendBtn.disabled = true;
        userInput.placeholder = "Hệ thống đang khởi động, vui lòng chờ...";
        const statusBubble = addMessage('Xin chào! Đang kết nối tới Trợ lý AI...', 'bot');

        const warmUpInterval = setInterval(async () => {
            try {
                // Gửi một câu hỏi "ping" đặc biệt để kích hoạt và kiểm tra server
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: "__WARM_UP_PING__" }),
                });

                // Nếu server trả về OK (mã 200), nghĩa là đã khởi tạo xong
                if (response.ok) {
                    const data = await response.json();
                    if (data.status === 'ready') {
                        console.log("Server đã sẵn sàng!");
                        clearInterval(warmUpInterval);
                        statusBubble.textContent = 'Hệ thống đã sẵn sàng! Tôi có thể giúp gì cho bạn?';
                        userInput.disabled = false;
                        sendBtn.disabled = false;
                        userInput.placeholder = "Nhập câu hỏi của bạn ở đây...";
                        userInput.focus();
                    }
                } else {
                    // Nếu server trả về lỗi (ví dụ 503), nghĩa là nó vẫn đang khởi tạo
                    console.log("Server đang khởi tạo, đang thử lại...");
                    statusBubble.textContent = 'Đang khởi tạo bộ não AI, vui lòng chờ...';
                }
            } catch (error) {
                console.error("Lỗi trong quá trình 'đánh thức':", error);
                statusBubble.textContent = 'Lỗi kết nối. Đang thử lại...';
            }
        }, 4000); // Tăng thời gian chờ giữa các lần ping lên 4 giây
    }

    // Hàm chính để gửi tin nhắn
    async function handleSendMessage() {
        const question = userInput.value.trim();
        if (question === '' || userInput.disabled) return;
        addMessage(question, 'user');
        userInput.value = '';
        const loadingBubble = showLoadingIndicator();
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question }),
            });
            const data = await response.json();
            updateOrAddMessage(loadingBubble, data.answer);
        } catch (error) {
            console.error('Lỗi khi gửi câu hỏi:', error);
            updateOrAddMessage(loadingBubble, 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.');
        }
    }

    function showLoadingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'bot-message');
        const bubbleDiv = document.createElement('div');
        bubbleDiv.classList.add('message-bubble', 'loading-indicator');
        bubbleDiv.innerHTML = `<div class="dot"></div><div class="dot"></div><div class="dot"></div>`;
        messageDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return bubbleDiv;
    }

    function updateOrAddMessage(bubble, text) {
        if (bubble) {
            bubble.textContent = text;
            bubble.classList.remove('loading-indicator');
        } else {
            addMessage(text, 'bot');
        }
    }

    sendBtn.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') handleSendMessage();
    });

    warmUpSystem();
});
