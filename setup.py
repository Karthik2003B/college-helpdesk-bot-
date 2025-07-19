#!/usr/bin/env python3
"""
College Helpdesk Chatbot - Automated Setup Script
This script will help you set up the chatbot quickly and easily.
"""

import os
import sys
import subprocess
import platform

def print_header():
    print("=" * 60)
    print("🎓 COLLEGE HELPDESK CHATBOT - SETUP WIZARD")
    print("=" * 60)
    print("This script will help you set up your chatbot step by step!")
    print()

def check_python():
    """Check if Python is installed and version is compatible"""
    print("📍 Checking Python installation...")
    
    try:
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible!")
            return True
        else:
            print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.8+")
            print("📥 Please download Python from: https://python.org/downloads/")
            return False
    except Exception as e:
        print(f"❌ Python check failed: {e}")
        return False

def install_packages():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    
    packages = ['flask', 'python-telegram-bot', 'twilio']
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    print("✅ All packages installed successfully!")
    return True

def create_main_file():
    """Create the main college_chatbot.py file"""
    print("\n📝 Creating main chatbot file...")
    
    # Check if file already exists
    if os.path.exists('college_chatbot.py'):
        response = input("⚠️  college_chatbot.py already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("✅ Keeping existing file")
            return True
    
    # Main chatbot code (simplified version for auto-generation)
    chatbot_code = '''# College Helpdesk Chatbot - Auto-generated
# This is a simplified version. For the full version, copy from the provided artifact.

from flask import Flask, request, jsonify, render_template_string
import sqlite3
import difflib
import re
from datetime import datetime

app = Flask(__name__)

class SimpleChatbot:
    def __init__(self):
        self.init_database()
        self.faqs = [
            ("What are admission requirements?", "Admission requirements include: completed application, transcripts, entrance exam scores, and letters of recommendation."),
            ("When is tuition due?", "Tuition payment deadlines: Fall - August 15th, Spring - January 15th, Summer - May 15th."),
            ("How do I register for classes?", "Class registration is done online through the student portal. Meet with your advisor first."),
            ("What are library hours?", "Library hours: Mon-Thu 7am-11pm, Fri 7am-9pm, Sat 9am-9pm, Sun 10am-11pm."),
        ]
    
    def init_database(self):
        conn = sqlite3.connect('college_faq.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_query TEXT,
                bot_response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def find_answer(self, query):
        best_match = ""
        best_score = 0
        
        for question, answer in self.faqs:
            score = difflib.SequenceMatcher(None, query.lower(), question.lower()).ratio()
            if score > best_score:
                best_score = score
                best_match = answer
        
        if best_score < 0.3:
            best_match = "I'm sorry, I don't have information about that. Please contact the helpdesk at help@college.edu"
        
        return best_match, best_score

chatbot = SimpleChatbot()

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>College Helpdesk Bot</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: scroll; padding: 10px; margin: 20px 0; }
            .message { margin: 10px 0; padding: 10px; border-radius: 10px; }
            .user { background: #007bff; color: white; text-align: right; }
            .bot { background: #f1f1f1; }
            input[type="text"] { width: 70%; padding: 10px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>🎓 College Helpdesk Chatbot</h1>
        <div class="chat-container" id="chatContainer">
            <div class="message bot">Hello! I'm here to help with college questions. Try asking about admission requirements, tuition, or class registration!</div>
        </div>
        <div>
            <input type="text" id="messageInput" placeholder="Ask your question..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message) return;
                
                addMessage(message, 'user');
                input.value = '';
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: message })
                    });
                    const data = await response.json();
                    addMessage(data.response, 'bot');
                } catch (error) {
                    addMessage('Sorry, there was an error.', 'bot');
                }
            }
            
            function addMessage(message, sender) {
                const container = document.getElementById('chatContainer');
                const div = document.createElement('div');
                div.className = 'message ' + sender;
                div.textContent = message;
                container.appendChild(div);
                container.scrollTop = container.scrollHeight;
            }
        </script>
    </body>
    </html>
    """

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    response, confidence = chatbot.find_answer(user_message)
    
    # Log conversation
    conn = sqlite3.connect('college_faq.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_logs (user_query, bot_response) VALUES (?, ?)', 
                   (user_message, response))
    conn.commit()
    conn.close()
    
    return jsonify({'response': response, 'confidence': confidence})

if __name__ == '__main__':
    print("🎓 College Helpdesk Chatbot Starting...")
    print("📱 Web Interface: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
'''
    
    try:
        with open('college_chatbot.py', 'w') as f:
            f.write(chatbot_code)
        print("✅ college_chatbot.py created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create file: {e}")
        return False

def create_requirements_file():
    """Create requirements.txt file"""
    print("\n📄 Creating requirements.txt...")
    
    requirements = """flask==2.3.3
python-telegram-bot==20.7
twilio==8.10.0
"""
    
    try:
        with open('requirements.txt', 'w') as f:
            f.write(requirements)
        print("✅ requirements.txt created")
        return True
    except Exception as e:
        print(f"❌ Failed to create requirements.txt: {e}")
        return False

def run_chatbot():
    """Try to run the chatbot"""
    print("\n🚀 Starting the chatbot...")
    print("📱 The chatbot will be available at: http://localhost:5000")
    print("💡 Press Ctrl+C to stop the server")
    print()
    
    try:
        import college_chatbot
    except ImportError:
        print("❌ Could not import chatbot. Please check the setup.")
        return False
    except Exception as e:
        print(f"❌ Error running chatbot: {e}")
        return False

def main():
    """Main setup function"""
    print_header()
    
    # Check Python
    if not check_python():
        return
    
    print()
    print("🎯 SETUP STEPS:")
    print("1. Check Python ✅")
    print("2. Install packages")
    print("3. Create main file")
    print("4. Create requirements")
    print("5. Run chatbot")
    print()
    
    # Ask user to proceed
    response = input("Ready to continue? (y/n): ")
    if response.lower() != 'y':
        print("Setup cancelled.")
        return
    
    # Install packages
    if not install_packages():
        print("❌ Package installation failed. Please install manually:")
        print("pip install flask python-telegram-bot twilio")
        return
    
    # Create files
    if not create_main_file():
        return
    
    if not create_requirements_file():
        return
    
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("📂 Files created:")
    print("   ✅ college_chatbot.py")
    print("   ✅ requirements.txt")
    print("   ✅ college_faq.db (will be created when you run the bot)")
    print()
    print("🚀 TO RUN YOUR CHATBOT:")
    print("   python college_chatbot.py")
    print()
    print("🌐 THEN VISIT:")
    print("   http://localhost:5000")
    print()
    print("📝 NOTE: This is a simplified version.")
    print("   For the full-featured version, copy the complete code")
    print("   from the provided artifacts.")
    print()
    
    # Ask if they want to run now
    run_now = input("🎯 Run the chatbot now? (y/n): ")
    if run_now.lower() == 'y':
        print("\n" + "="*60)
        print("🚀 STARTING CHATBOT...")
        print("="*60)
        exec(open('college_chatbot.py').read())

if __name__ == "__main__":
    main()
