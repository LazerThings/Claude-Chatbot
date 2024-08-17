import os
import uuid
import json
from bottle import Bottle, run, request, template, response
import anthropic
from datetime import datetime
import markdown2

app = Bottle()

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# File to store conversations
CONVERSATIONS_FILE = 'conversations.json'

# Load conversations from file
def load_conversations():
    if os.path.exists(CONVERSATIONS_FILE):
        with open(CONVERSATIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save conversations to file
def save_conversations():
    with open(CONVERSATIONS_FILE, 'w') as f:
        json.dump(conversations, f, indent=2, default=str)

# Load existing conversations or initialize empty dict
conversations = load_conversations()

@app.route('/')
def home():
    return template('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Claude Chatbot</title>
            <link href="https://fonts.googleapis.com/css2?family=Overpass:wght@300;400;600&display=swap" rel="stylesheet">
            <style>
                :root {
                    --bg-primary: #f0f4f0;
                    --bg-secondary: #e0e8e0;
                    --text-primary: #333;
                    --text-secondary: #666;
                    --accent-color: #4a7c59;
                    --border-color: #c0c8c0;
                }

                @media (prefers-color-scheme: dark) {
                    :root {
                        --bg-primary: #2a3a2a;
                        --bg-secondary: #1a2a1a;
                        --text-primary: #e0e0e0;
                        --text-secondary: #b0b0b0;
                        --accent-color: #6a9c79;
                        --border-color: #4a5a4a;
                    }
                }

                body {
                    font-family: 'Overpass', sans-serif;
                    background-color: var(--bg-primary);
                    color: var(--text-primary);
                    display: flex;
                    height: 100vh;
                    margin: 0;
                    transition: background-color 0.3s ease, color 0.3s ease;
                }

                button, input, textarea {
                    font-family: 'Overpass', sans-serif;
                }

                #sidebar {
                    min-width: 350px;
                    width: 350px;
                    background-color: var(--bg-secondary);
                    padding: 20px;
                    overflow-y: auto;
                    border-right: 1px solid var(--border-color);
                }

                #main {
                    flex-grow: 1;
                    display: flex;
                    flex-direction: column;
                    padding: 20px;
                }

                #chat-history {
                    flex-grow: 1;
                    border: 1px solid var(--border-color);
                    padding: 10px;
                    overflow-y: scroll;
                    margin-bottom: 10px;
                    background-color: var(--bg-primary);
                }

                #user-input {
                    width: 100%;
                    padding: 10px;
                    margin-bottom: 10px;
                    border: 1px solid var(--border-color);
                    background-color: var(--bg-secondary);
                    color: var(--text-primary);
                    font-family: 'Overpass', sans-serif;
                    font-size: 16px;
                    resize: vertical;
                }

                #send-button, #new-conversation {
                    padding: 10px 20px;
                    margin-right: 10px;
                    background-color: var(--accent-color);
                    color: white;
                    border: none;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                    font-family: 'Overpass', sans-serif;
                    font-size: 16px;
                }

                #send-button:hover, #new-conversation:hover {
                    background-color: #5a8c69;
                }

                .conversation-item {
                    cursor: pointer;
                    padding: 10px;
                    margin-bottom: 5px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background-color: var(--bg-primary);
                    border: 1px solid var(--border-color);
                    transition: background-color 0.3s ease;
                }

                .conversation-item:hover {
                    background-color: var(--accent-color);
                    color: white;
                }

                .active {
                    background-color: var(--accent-color);
                    color: white;
                }

                .conversation-buttons {
                    display: flex;
                }

                .conversation-buttons button {
                    margin-left: 5px;
                    padding: 5px 10px;
                    background-color: var(--bg-secondary);
                    color: var(--text-primary);
                    border: 1px solid var(--border-color);
                    cursor: pointer;
                    transition: background-color 0.3s ease, color 0.3s ease;
                    font-family: 'Overpass', sans-serif;
                    font-size: 14px;
                }

                .conversation-buttons button:hover {
                    background-color: var(--accent-color);
                    color: white;
                }

                h1, h2 {
                    color: var(--accent-color);
                }

                #chat-history p {
                    margin-bottom: 10px;
                }
                #chat-history pre {
                    background-color: var(--bg-secondary);
                    padding: 10px;
                    border-radius: 4px;
                    overflow-x: auto;
                }
                #chat-history code {
                    font-family: monospace;
                    background-color: var(--bg-secondary);
                    padding: 2px 4px;
                    border-radius: 2px;
                }
            </style>
        </head>
        <body>
            <div id="sidebar">
                <h2>Conversations</h2>
                <div id="conversation-list"></div>
                <button id="new-conversation">New Conversation</button>
            </div>
            <div id="main">
                <h1>Claude</h1>
                <div id="chat-history"></div>
                <textarea id="user-input" placeholder="Type your message here..." rows="3"></textarea>
                <button id="send-button">Send</button>
            </div>

            <script>
            const chatHistory = document.getElementById('chat-history');
            const userInput = document.getElementById('user-input');
            const sendButton = document.getElementById('send-button');
            const newConversationButton = document.getElementById('new-conversation');
            const conversationList = document.getElementById('conversation-list');
            let conversationId = localStorage.getItem('conversationId');
            let conversations = [];

            sendButton.addEventListener('click', sendMessage);
            userInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            newConversationButton.addEventListener('click', startNewConversation);

            function sendMessage() {
                const message = userInput.value.trim();
                if (message) {
                    appendMessage('You', message);
                    fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            message: message,
                            conversation_id: conversationId
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            appendMessage('System', `Error: ${data.error}`);
                        } else {
                            appendMessage('Claude', data.reply, true);
                            conversationId = data.conversation_id;
                            localStorage.setItem('conversationId', conversationId);
                        }
                        updateConversationList();
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        appendMessage('System', `Error: ${error.message}`);
                    });
                    userInput.value = '';
                }
            }

            function appendMessage(sender, message, isMarkdown = false) {
                const messageElement = document.createElement('div');
                messageElement.innerHTML = `<strong>${sender}:</strong> `;
                if (isMarkdown) {
                    messageElement.innerHTML += message;
                } else {
                    messageElement.innerHTML += `<p>${message}</p>`;
                }
                chatHistory.appendChild(messageElement);
                chatHistory.scrollTop = chatHistory.scrollHeight;
            }

            function startNewConversation() {
                conversationId = null;
                localStorage.removeItem('conversationId');
                chatHistory.innerHTML = '';
                appendMessage('System', 'Started a new conversation.');
                updateConversationList();
            }

            function loadConversation(id) {
                conversationId = id;
                localStorage.setItem('conversationId', id);
                chatHistory.innerHTML = '';
                fetch(`/history/${id}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            appendMessage('System', `Error: ${data.error}`);
                        } else {
                            data.history.forEach(msg => appendMessage(msg.role === 'user' ? 'You' : 'Claude', msg.content, msg.role === 'assistant'));
                        }
                    })
                    .catch(error => {
                        console.error('Error loading history:', error);
                        appendMessage('System', `Error loading history: ${error.message}`);
                    });
                updateConversationList();
            }

            function updateConversationList() {
                fetch('/conversations')
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            console.error('Error fetching conversations:', data.error);
                        } else {
                            conversations = data.conversations;
                            renderConversationList();
                        }
                    })
                    .catch(error => console.error('Error updating conversation list:', error));
            }

            function renderConversationList() {
                conversationList.innerHTML = '';
                conversations.forEach(conv => {
                    const item = document.createElement('div');
                    item.className = `conversation-item${conv.id === conversationId ? ' active' : ''}`;
                    
                    const nameSpan = document.createElement('span');
                    nameSpan.textContent = conv.name || `Chat ${conv.id.slice(0, 8)}...`;
                    nameSpan.onclick = () => loadConversation(conv.id);
                    
                    const buttonContainer = document.createElement('div');
                    buttonContainer.className = 'conversation-buttons';

                    const renameButton = document.createElement('button');
                    renameButton.textContent = 'Rename';
                    renameButton.onclick = (e) => {
                        e.stopPropagation();
                        const newName = prompt('Enter new name for the conversation:', conv.name);
                        if (newName !== null) {
                            renameConversation(conv.id, newName);
                        }
                    };

                    const deleteButton = document.createElement('button');
                    deleteButton.textContent = 'Delete';
                    deleteButton.onclick = (e) => {
                        e.stopPropagation();
                        if (confirm('Are you sure you want to delete this conversation?')) {
                            deleteConversation(conv.id);
                        }
                    };
                    
                    buttonContainer.appendChild(renameButton);
                    buttonContainer.appendChild(deleteButton);
                    item.appendChild(nameSpan);
                    item.appendChild(buttonContainer);
                    conversationList.appendChild(item);
                });
            }

            function renameConversation(id, newName) {
                fetch('/rename', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id: id, name: newName})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateConversationList();
                    } else {
                        alert('Failed to rename conversation');
                    }
                })
                .catch(error => console.error('Error renaming conversation:', error));
            }

            function deleteConversation(id) {
                fetch(`/delete/${id}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (id === conversationId) {
                            startNewConversation();
                        } else {
                            updateConversationList();
                        }
                    } else {
                        alert('Failed to delete conversation');
                    }
                })
                .catch(error => console.error('Error deleting conversation:', error));
            }

            // Initial load
            updateConversationList();
            if (conversationId) {
                loadConversation(conversationId);
            } else {
                startNewConversation();
            }
        </script>
    </body>
    </html>
    ''')

def generate_chat_name(first_message):
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            messages=[
                {"role": "user", "content": f'Please provide a short, simple title for a chat about "{first_message}". Please only provide one title. Do not include quotes and/or other text around the title. Please provide just the title.'}
            ]
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"Error generating chat name: {e}")
        return None

@app.post('/chat')
def chat():
    data = request.json
    user_message = data['message']
    conversation_id = data.get('conversation_id')

    if not conversation_id or conversation_id not in conversations:
        conversation_id = str(uuid.uuid4())
        conversations[conversation_id] = {'messages': [], 'name': None, 'last_updated': datetime.now().isoformat()}

    conversations[conversation_id]['messages'].append({"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()})
    conversations[conversation_id]['last_updated'] = datetime.now().isoformat()
    
    try:
        api_messages = [{"role": msg["role"], "content": msg["content"]} 
                        for msg in conversations[conversation_id]['messages'] 
                        if msg['role'] in ['user', 'assistant']]
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=api_messages
        )
        reply = response.content[0].text
        # Convert markdown to HTML
        reply_html = markdown2.markdown(reply)
        conversations[conversation_id]['messages'].append({"role": "assistant", "content": reply, "timestamp": datetime.now().isoformat()})

        # Generate a name for the chat if it's a new conversation
        if len(conversations[conversation_id]['messages']) == 2 and not conversations[conversation_id]['name']:
            chat_name = generate_chat_name(user_message)
            if chat_name:
                conversations[conversation_id]['name'] = chat_name

        save_conversations()
        return {"reply": reply_html, "conversation_id": conversation_id}
    except Exception as e:
        return {"error": str(e), "conversation_id": conversation_id}

@app.get('/history/<conversation_id>')
def get_history(conversation_id):
    try:
        history = conversations[conversation_id]['messages']
        # Convert markdown to HTML for assistant messages
        for msg in history:
            if msg['role'] == 'assistant':
                msg['content'] = markdown2.markdown(msg['content'])
        return {"history": history}
    except KeyError:
        response.status = 404
        return {"error": f"Conversation with id {conversation_id} not found"}

@app.get('/conversations')
def get_conversations():
    sorted_conversations = sorted(conversations.items(), key=lambda x: x[1]['last_updated'], reverse=True)
    return {
        "conversations": [
            {"id": id, "name": data['name'], "messages": len(data['messages'])}
            for id, data in sorted_conversations
        ]
    }

@app.post('/rename')
def rename_conversation():
    data = request.json
    conversation_id = data['id']
    new_name = data['name']
    
    if conversation_id in conversations:
        conversations[conversation_id]['name'] = new_name
        save_conversations()
        return {"success": True}
    else:
        response.status = 404
        return {"success": False, "error": f"Conversation with id {conversation_id} not found"}

@app.delete('/delete/<conversation_id>')
def delete_conversation(conversation_id):
    if conversation_id in conversations:
        del conversations[conversation_id]
        save_conversations()
        return {"success": True}
    else:
        response.status = 404
        return {"success": False, "error": f"Conversation with id {conversation_id} not found"}

if __name__ == '__main__':
    run(app, host='localhost', port=6705, debug=True)