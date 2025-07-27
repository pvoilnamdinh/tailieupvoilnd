document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    // Hàm để thêm tin nhắn vào khung chat và trả về bubble
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);

        const bubbleDiv = document.createElement('div');
        bubbleDiv.classList.add('message-bubble');
        bubbleDiv.textContent = text;
        
        messageDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return bubbleDiv; // Trả về để có thể cập nhật
    }

    // --- **HỆ THỐNG KIỂM TRA TRẠNG THÁI SERVER** ---
    function initializeChat() {
        console.log("Bắt đầu kiểm tra trạng thái server...");
        
        // Vô hiệu hóa giao diện
        userInput.disabled = true;
        sendBtn.disabled = true;
        userInput.placeholder = "Hệ thống đang khởi động, vui lòng chờ...";

        // Hiển thị tin nhắn chờ
        const statusBubble = addMessage('Xin chào! Đang kết nối tới Trợ lý AI...', 'bot');

        // Bắt đầu hỏi thăm trạng thái server mỗi 3 giây
        const statusInterval = setInterval(async () => {
            try {
                const response = await fetch('/status');
                const data = await response.json();

                if (data.status === 'ready') {
                    // Nếu server sẵn sàng, dừng hỏi thăm và kích hoạt giao diện
                    console.log("Server đã sẵn sàng!");
                    clearInterval(statusInterval);
                    statusBubble.textContent = 'Hệ thống đã sẵn sàng! Tôi có thể giúp gì cho bạn?';
                    userInput.disabled = false;
                    sendBtn.disabled = false;
                    userInput.placeholder = "Nhập câu hỏi của bạn ở đây...";
                    userInput.focus();
                } else if (data.status === 'error') {
                    // Nếu server báo lỗi, dừng lại và thông báo lỗi
                    console.error("Server báo lỗi trong quá trình khởi tạo.");
                    clearInterval(statusInterval);
                    statusBubble.textContent = 'Lỗi: Hệ thống không thể khởi động. Vui lòng liên hệ quản trị viên.';
                } else {
                    // Nếu vẫn đang khởi tạo, cứ tiếp tục chờ
                    console.log("Server đang khởi tạo...");
                }
            } catch (error) {
                console.error("Không thể kết nối tới server:", error);
                statusBubble.textContent = 'Lỗi: Mất kết nối tới server. Vui lòng tải lại trang.';
                clearInterval(statusInterval);
            }
        }, 3000); // Tần suất hỏi thăm
    }

    // Hàm chính để xử lý việc gửi tin nhắn
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

    // Hàm hiển thị chỉ báo "đang tải"
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

    // Hàm cập nhật tin nhắn đang tải
    function updateOrAddMessage(bubble, text) {
        if (bubble) {
            bubble.textContent = text;
            bubble.classList.remove('loading-indicator');
        } else {
            addMessage(text, 'bot');
        }
    }

    // Gán sự kiện
    sendBtn.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') handleSendMessage();
    });

    // Bắt đầu quá trình kiểm tra trạng thái ngay khi trang được tải
    initializeChat();
});
