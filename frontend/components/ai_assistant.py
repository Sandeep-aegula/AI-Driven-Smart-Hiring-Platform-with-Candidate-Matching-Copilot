import streamlit as st
import base64

def render_ai_assistant() -> None:
    """
    Render a true floating AI assistant by injecting a vanilla JS application directly 
    into the parent document's body, completely bypassing Streamlit's layout engine.
    This ensures absolutely ZERO layout shift or blank space.
    """
    
    html_payload = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body>
        <script>
            // 1. Get the parent document (Streamlit main page)
            const doc = window.parent.document;
            
            // 2. Hide the Streamlit iframe container completely so it takes 0 layout space
            const iframe = window.frameElement;
            if (iframe) {
                // Streamlit wraps the iframe in a div (element-container)
                const wrapper = iframe.closest('[data-testid="element-container"]');
                if (wrapper) {
                    wrapper.style.display = 'none';
                    wrapper.style.position = 'absolute';
                    wrapper.style.width = '0px';
                    wrapper.style.height = '0px';
                }
                iframe.style.display = 'none';
            }

            // 3. Only inject if it doesn't already exist
            if (!doc.getElementById('hirepilot-ai-assistant-root')) {
                const root = doc.createElement('div');
                root.id = 'hirepilot-ai-assistant-root';
                
                // Set the HTML structure and CSS
                root.innerHTML = `
                <style>
                    /* Root Container */
                    #hirepilot-ai-assistant-root {
                        position: fixed;
                        bottom: 0;
                        right: 0;
                        width: 0;
                        height: 0;
                        z-index: 999999;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    }

                    /* Launcher Button */
                    #hp-ai-launcher {
                        position: fixed;
                        bottom: 24px;
                        right: 24px;
                        width: 64px;
                        height: 64px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #6366F1, #8B5CF6);
                        box-shadow: 0 12px 30px rgba(99, 102, 241, 0.35);
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        transition: transform 0.25s ease, box-shadow 0.25s ease;
                        z-index: 1000000;
                    }

                    #hp-ai-launcher:hover {
                        transform: scale(1.08);
                        box-shadow: 0 16px 40px rgba(99, 102, 241, 0.45);
                    }

                    #hp-ai-launcher:active {
                        transform: scale(0.96);
                    }

                    #hp-ai-launcher svg {
                        width: 30px;
                        height: 30px;
                        color: white;
                    }

                    /* Chat Panel */
                    #hp-ai-panel {
                        position: fixed;
                        bottom: 100px;
                        right: 24px;
                        width: 400px;
                        height: 88vh;
                        max-height: 800px;
                        background: rgba(255, 255, 255, 0.95);
                        backdrop-filter: blur(18px);
                        -webkit-backdrop-filter: blur(18px);
                        border-radius: 20px;
                        border: 1px solid rgba(226, 232, 240, 0.8);
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
                        z-index: 999999;
                        display: flex;
                        flex-direction: column;
                        overflow: hidden;
                        
                        /* Hidden by default */
                        opacity: 0;
                        transform: translateX(50px);
                        pointer-events: none;
                        transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    }

                    #hp-ai-panel.open {
                        opacity: 1;
                        transform: translateX(0);
                        pointer-events: all;
                    }

                    /* Header */
                    #hp-ai-header {
                        padding: 16px 20px;
                        background: linear-gradient(135deg, #6366F1, #8B5CF6);
                        color: white;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        border-top-left-radius: 20px;
                        border-top-right-radius: 20px;
                    }

                    #hp-ai-header h3 {
                        margin: 0;
                        font-size: 16px;
                        font-weight: 600;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }

                    .hp-ai-controls {
                        display: flex;
                        gap: 12px;
                    }

                    .hp-ai-controls button {
                        background: none;
                        border: none;
                        color: white;
                        cursor: pointer;
                        padding: 0;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        opacity: 0.8;
                        transition: opacity 0.2s;
                    }

                    .hp-ai-controls button:hover {
                        opacity: 1;
                    }

                    /* Messages Area */
                    #hp-ai-messages {
                        flex: 1;
                        padding: 20px;
                        overflow-y: auto;
                        display: flex;
                        flex-direction: column;
                        gap: 16px;
                    }

                    .hp-msg-row {
                        display: flex;
                        max-width: 85%;
                        gap: 10px;
                    }

                    .hp-msg-row.assistant {
                        align-self: flex-start;
                    }

                    .hp-msg-row.user {
                        align-self: flex-end;
                        flex-direction: row-reverse;
                    }

                    .hp-avatar {
                        width: 32px;
                        height: 32px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 14px;
                        flex-shrink: 0;
                    }

                    .hp-avatar.assistant {
                        background: linear-gradient(135deg, #6366F1, #8B5CF6);
                        color: white;
                    }

                    .hp-avatar.user {
                        background: #EEF4FF;
                        color: #3B82F6;
                        border: 1px solid #DBEAFE;
                    }

                    .hp-bubble {
                        padding: 12px 16px;
                        border-radius: 18px;
                        font-size: 14px;
                        line-height: 1.5;
                        color: #1E293B;
                        word-wrap: break-word;
                    }

                    .hp-bubble.assistant {
                        background: #FFFFFF;
                        border: 1px solid #E2E8F0;
                        border-top-left-radius: 4px;
                        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
                    }

                    .hp-bubble.user {
                        background: #EEF4FF;
                        border: 1px solid #DBEAFE;
                        border-top-right-radius: 4px;
                    }

                    /* Input Area */
                    #hp-ai-input-area {
                        padding: 16px;
                        border-top: 1px solid #E2E8F0;
                        background: #FAFAFA;
                        display: flex;
                        gap: 10px;
                        align-items: flex-end;
                        border-bottom-left-radius: 20px;
                        border-bottom-right-radius: 20px;
                    }

                    #hp-ai-textarea {
                        flex: 1;
                        min-height: 40px;
                        max-height: 120px;
                        padding: 10px 16px;
                        border-radius: 20px;
                        border: 1px solid #E2E8F0;
                        resize: none;
                        outline: none;
                        font-family: inherit;
                        font-size: 14px;
                        line-height: 1.4;
                        transition: border-color 0.2s;
                        background: white;
                    }

                    #hp-ai-textarea:focus {
                        border-color: #6366F1;
                    }

                    #hp-ai-send-btn {
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #6366F1, #8B5CF6);
                        border: none;
                        color: white;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        flex-shrink: 0;
                        transition: transform 0.2s;
                    }

                    #hp-ai-send-btn:hover {
                        transform: scale(1.05);
                    }
                    
                    #hp-ai-send-btn:disabled {
                        opacity: 0.5;
                        cursor: not-allowed;
                    }

                    /* Typing Indicator */
                    .hp-typing {
                        display: flex;
                        gap: 4px;
                        padding: 4px 0;
                    }
                    .hp-typing-dot {
                        width: 6px;
                        height: 6px;
                        border-radius: 50%;
                        background: #94A3B8;
                        animation: hp-bounce 1.4s infinite ease-in-out;
                    }
                    .hp-typing-dot:nth-child(1) { animation-delay: -0.32s; }
                    .hp-typing-dot:nth-child(2) { animation-delay: -0.16s; }
                    
                    @keyframes hp-bounce {
                        0%, 80%, 100% { transform: scale(0); }
                        40% { transform: scale(1); }
                    }

                </style>

                <!-- Floating Launcher -->
                <div id="hp-ai-launcher" title="AI Assistant">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bot">
                        <path d="M12 8V4H8"/>
                        <rect width="16" height="12" x="4" y="8" rx="2"/>
                        <path d="M2 14h2"/>
                        <path d="M20 14h2"/>
                        <path d="M15 13v2"/>
                        <path d="M9 13v2"/>
                    </svg>
                </div>

                <!-- Chat Panel -->
                <div id="hp-ai-panel">
                    <div id="hp-ai-header">
                        <h3>🤖 AI Assistant</h3>
                        <div class="hp-ai-controls">
                            <button id="hp-ai-min-btn" title="Minimize">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                            </button>
                            <button id="hp-ai-close-btn" title="Close">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                            </button>
                        </div>
                    </div>
                    
                    <div id="hp-ai-messages">
                        <div class="hp-msg-row assistant">
                            <div class="hp-avatar assistant">🤖</div>
                            <div class="hp-bubble assistant">Hi! I'm the HirePilot Assistant. How can I help you navigate the system today?</div>
                        </div>
                    </div>

                    <div id="hp-ai-input-area">
                        <textarea id="hp-ai-textarea" placeholder="Ask me anything about the system..." rows="1"></textarea>
                        <button id="hp-ai-send-btn">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                        </button>
                    </div>
                </div>
                `;

                doc.body.appendChild(root);

                // --- Logic ---
                let isOpen = false;
                let sessionId = "session_" + Math.random().toString(36).substring(2, 15);
                let chatHistory = [];
                
                const launcher = doc.getElementById('hp-ai-launcher');
                const panel = doc.getElementById('hp-ai-panel');
                const closeBtn = doc.getElementById('hp-ai-close-btn');
                const minBtn = doc.getElementById('hp-ai-min-btn');
                const textarea = doc.getElementById('hp-ai-textarea');
                const sendBtn = doc.getElementById('hp-ai-send-btn');
                const messagesDiv = doc.getElementById('hp-ai-messages');

                function togglePanel() {
                    isOpen = !isOpen;
                    if (isOpen) {
                        panel.classList.add('open');
                        textarea.focus();
                    } else {
                        panel.classList.remove('open');
                    }
                }

                launcher.addEventListener('click', togglePanel);
                closeBtn.addEventListener('click', togglePanel);
                minBtn.addEventListener('click', togglePanel);

                function addMessage(role, content) {
                    const row = doc.createElement('div');
                    row.className = `hp-msg-row ${role}`;
                    
                    const avatar = doc.createElement('div');
                    avatar.className = `hp-avatar ${role}`;
                    avatar.innerText = role === 'assistant' ? '🤖' : '👤';
                    
                    const bubble = doc.createElement('div');
                    bubble.className = `hp-bubble ${role}`;
                    bubble.innerText = content;
                    
                    row.appendChild(role === 'assistant' ? avatar : bubble);
                    row.appendChild(role === 'assistant' ? bubble : avatar);
                    
                    messagesDiv.appendChild(row);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }

                function addTypingIndicator() {
                    const row = doc.createElement('div');
                    row.className = 'hp-msg-row assistant hp-typing-row';
                    
                    const avatar = doc.createElement('div');
                    avatar.className = 'hp-avatar assistant';
                    avatar.innerText = '🤖';
                    
                    const bubble = doc.createElement('div');
                    bubble.className = 'hp-bubble assistant hp-typing';
                    bubble.innerHTML = '<div class="hp-typing-dot"></div><div class="hp-typing-dot"></div><div class="hp-typing-dot"></div>';
                    
                    row.appendChild(avatar);
                    row.appendChild(bubble);
                    
                    messagesDiv.appendChild(row);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    return row;
                }

                async function sendMessage() {
                    const text = textarea.value.trim();
                    if (!text) return;
                    
                    // Add User Message
                    addMessage('user', text);
                    chatHistory.push({role: "user", content: text});
                    textarea.value = '';
                    sendBtn.disabled = true;
                    textarea.style.height = '40px';
                    
                    const typingRow = addTypingIndicator();
                    
                    try {
                        const response = await fetch('http://localhost:8000/api/assistant/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                session_id: sessionId,
                                message: text,
                                history: chatHistory.slice(0, -1),
                                current_page: window.parent.location.pathname || "Dashboard"
                            })
                        });
                        
                        typingRow.remove();
                        
                        if (!response.ok) {
                            let errorText = await response.text();
                            try {
                                const errJson = JSON.parse(errorText);
                                if (errJson.detail) {
                                    errorText = errJson.detail;
                                }
                            } catch (e) {}
                            addMessage('assistant', `Backend Error (HTTP ${response.status}):\\n${errorText}`);
                            return;
                        }
                        
                        const data = await response.json();
                        const reply = data.response || "I couldn't generate a response. Please try again.";
                        addMessage('assistant', reply);
                        chatHistory.push({role: "assistant", content: reply});
                        
                    } catch (error) {
                        typingRow.remove();
                        addMessage('assistant', `Exception: ${error.message}\\nTraceback: ${error.stack || "N/A"}\\nMake sure FastAPI is running on port 8000.`);
                    }
                    
                    sendBtn.disabled = false;
                    textarea.focus();
                }

                sendBtn.addEventListener('click', sendMessage);
                
                textarea.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });
                
                textarea.addEventListener('input', () => {
                    textarea.style.height = '40px';
                    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
                });
            }
        </script>
    </body>
    </html>
    """
    
    st.components.v1.html(
        html_payload,
        height=0,
        width=0,
        scrolling=False,
    )