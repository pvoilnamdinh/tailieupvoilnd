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
        
        // Tự động cuộn xuống tin nhắn mới nhất
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Hàm hiển thị chỉ báo "đang tải"
    function showLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'bot-message', 'loading-indicator');
        loadingDiv.id = 'loading'; // Gán ID để có thể xóa sau

        const bubbleDiv = document.createElement('div');
        bubbleDiv.classList.add('message-bubble');
        bubbleDiv.innerHTML = `
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        `;
        
        loadingDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Hàm xóa chỉ báo "đang tải"
    function hideLoadingIndicator() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.remove();
        }
    }

    // Hàm chính để xử lý việc gửi tin nhắn
    async function handleSendMessage() {
        const question = userInput.value.trim();
        if (question === '') {
            return; // Không gửi nếu không có nội dung
        }

        // 1. Hiển thị câu hỏi của người dùng
        addMessage(question, 'user');
        userInput.value = ''; // Xóa nội dung trong ô nhập liệu

        // 2. Hiển thị chỉ báo đang tải
        showLoadingIndicator();

        // 3. Gửi câu hỏi đến server
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question }),
            });

            const data = await response.json();
            
            // 4. Xóa chỉ báo tải và hiển thị câu trả lời của bot
            hideLoadingIndicator();
            addMessage(data.answer, 'bot');

        } catch (error) {
            console.error('Lỗi khi gửi câu hỏi:', error);
            hideLoadingIndicator();
            addMessage('Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.', 'bot');
        }
    }

    // Gán sự kiện cho nút gửi và phím Enter
    sendBtn.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            handleSendMessage();
        }
    });

    // Tin nhắn chào mừng ban đầu
    addMessage('Xin chào! Tôi là Trợ lý AI của PVOIL Nam Định. Tôi có thể giúp gì cho bạn hôm nay?', 'bot');
});
