# College Helpdesk AI Chatbot
# A comprehensive chatbot system for answering college FAQs

import sqlite3
import re
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import difflib
from typing import List, Dict, Tuple
import json

app = Flask(__name__)

class CollegeChatbot:
    def __init__(self, db_path='college_faq.db'):
        self.db_path = db_path
        self.init_database()
        self.load_faqs()
        
    def init_database(self):
        """Initialize the FAQ database with sample data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category VARCHAR(100),
                question TEXT,
                answer TEXT,
                keywords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_query TEXT,
                bot_response TEXT,
                confidence_score REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert sample FAQs
        sample_faqs = [
            # Admissions
            ("Admissions", "What are the admission requirements?", 
             "Admission requirements include: 1) Completed application form 2) Academic transcripts 3) Entrance exam scores 4) Letters of recommendation 5) Statement of purpose. Minimum GPA requirement is 3.0.", 
             "admission, requirements, apply, application, GPA, transcripts"),
            
            ("Admissions", "When is the application deadline?", 
             "Application deadlines are: Fall semester - March 15th, Spring semester - October 15th, Summer semester - February 15th. Late applications may be considered on a case-by-case basis.", 
             "deadline, application, fall, spring, summer, dates"),
            
            ("Admissions", "What is the application fee?", 
             "The application fee is $75 for domestic students and $100 for international students. Fee waivers are available for students with financial need.", 
             "application fee, cost, payment, waiver, international"),
            
            # Academic
            ("Academic", "How do I register for classes?", 
             "Class registration is done online through the student portal. Registration opens based on your class standing: Seniors - Day 1, Juniors - Day 2, Sophomores - Day 3, Freshmen - Day 4. You'll need to meet with your academic advisor before registration.", 
             "register, classes, courses, enrollment, student portal, advisor"),
            
            ("Academic", "What is the grading system?", 
             "Our grading system: A (90-100%), B (80-89%), C (70-79%), D (60-69%), F (below 60%). Grade points: A=4.0, B=3.0, C=2.0, D=1.0, F=0.0. Minimum GPA to remain in good standing is 2.0.", 
             "grades, grading, GPA, points, academic standing"),
            
            ("Academic", "How do I change my major?", 
             "To change your major: 1) Meet with your current advisor 2) Meet with advisor in new department 3) Complete major change form 4) Submit to Registrar's office. Some majors have specific requirements or deadlines.", 
             "change major, switch major, academic advisor, registrar"),
            
            # Financial
            ("Financial", "What financial aid is available?", 
             "Financial aid options include: Federal grants and loans, state grants, institutional scholarships, work-study programs. Complete FAFSA by priority deadline March 1st for best consideration.", 
             "financial aid, scholarships, grants, loans, FAFSA, work study"),
            
            ("Financial", "When is tuition due?", 
             "Tuition payment deadlines: Fall semester - August 15th, Spring semester - January 15th, Summer semester - May 15th. Payment plans are available through the Bursar's office.", 
             "tuition, payment, due date, bursar, payment plan"),
            
            ("Financial", "How do I apply for scholarships?", 
             "Scholarship applications are available on the Financial Aid portal. General application deadline is February 1st. Submit transcripts, essays, and letters of recommendation as required.", 
             "scholarships, apply, financial aid, deadline, application"),
            
            # Campus Life
            ("Campus Life", "What dining options are available?", 
             "Dining options include: Main cafeteria (all-you-can-eat), food court with various vendors, coffee shops, and convenience stores. Meal plans are required for on-campus residents.", 
             "dining, food, cafeteria, meal plans, restaurants, campus"),
            
            ("Campus Life", "How do I join clubs and organizations?", 
             "Join clubs at the Activities Fair during orientation week, or visit the Student Life office. Over 100+ student organizations available including academic, cultural, recreational, and service groups.", 
             "clubs, organizations, activities, student life, extracurricular"),
            
            ("Campus Life", "What housing options are available?", 
             "Housing options: Traditional dorms, suite-style residences, apartments for upperclassmen. All freshmen required to live on campus. Housing applications due by May 1st.", 
             "housing, dorms, residence, apartments, campus living"),
            
            # Technical Support
            ("Technical", "How do I access the student portal?", 
             "Access the student portal at portal.college.edu using your student ID and password. For password resets, visit IT Help Desk in Library Room 101 or call ext. 4357.", 
             "student portal, login, password, IT support, help desk"),
            
            ("Technical", "How do I connect to campus WiFi?", 
             "Connect to 'CollegeWiFi' network using your student credentials. For guest access, use 'CollegeGuest' with no password. For technical issues, contact IT at help@college.edu.", 
             "WiFi, internet, network, connection, IT support"),
            
            # Library
            ("Library", "What are library hours?", 
             "Library hours: Monday-Thursday 7am-11pm, Friday 7am-9pm, Saturday 9am-9pm, Sunday 10am-11pm. Extended hours during finals week. Check website for holiday schedules.", 
             "library, hours, schedule, finals, holiday"),
            
            ("Library", "How do I reserve study rooms?", 
             "Reserve study rooms online through the library website or at the front desk. Rooms can be booked up to 7 days in advance for up to 4 hours per day.", 
             "study rooms, reserve, booking, library, group study")
        ]
        
        cursor.execute('SELECT COUNT(*) FROM faqs')
        if cursor.fetchone()[0] == 0:  # Only insert if table is empty
            cursor.executemany('''
                INSERT INTO faqs (category, question, answer, keywords)
                VALUES (?, ?, ?, ?)
            ''', sample_faqs)
        
        conn.commit()
        conn.close()
        
    def load_faqs(self):
        """Load FAQs from database into memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, category, question, answer, keywords FROM faqs')
        self.faqs = cursor.fetchall()
        conn.close()
        
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text
        
    def calculate_similarity(self, user_query: str, faq_text: str, keywords: str) -> float:
        """Calculate similarity score between user query and FAQ"""
        user_query = self.preprocess_text(user_query)
        faq_text = self.preprocess_text(faq_text)
        keywords = self.preprocess_text(keywords)
        
        # Calculate similarity with question text
        question_similarity = difflib.SequenceMatcher(None, user_query, faq_text).ratio()
        
        # Calculate keyword match score
        user_words = set(user_query.split())
        keyword_words = set(keywords.split())
        keyword_matches = len(user_words.intersection(keyword_words))
        keyword_score = keyword_matches / max(len(user_words), 1)
        
        # Weighted combination
        final_score = (question_similarity * 0.6) + (keyword_score * 0.4)
        return final_score
        
    def find_best_answer(self, user_query: str) -> Tuple[str, float, str]:
        """Find the best matching FAQ answer"""
        if not user_query.strip():
            return "Please ask me a question about the college!", 0.0, "General"
            
        best_score = 0.0
        best_answer = "I'm sorry, I don't have information about that. Please contact the college helpdesk at help@college.edu or call (555) 123-4567 for assistance."
        best_category = "General"
        
        for faq_id, category, question, answer, keywords in self.faqs:
            score = self.calculate_similarity(user_query, question, keywords)
            if score > best_score:
                best_score = score
                best_answer = answer
                best_category = category
                
        # If confidence is too low, provide general help
        if best_score < 0.3:
            best_answer = f"I couldn't find a specific answer to your question. Here are some ways to get help:\n\n" \
                         f"📞 Call: (555) 123-4567\n" \
                         f"📧 Email: help@college.edu\n" \
                         f"🏢 Visit: Student Services Center\n" \
                         f"🌐 Website: www.college.edu/help\n\n" \
                         f"You can also try rephrasing your question or ask about: admissions, academics, financial aid, campus life, or technical support."
            best_category = "General"
                
        return best_answer, best_score, best_category
        
    def log_conversation(self, user_query: str, bot_response: str, confidence_score: float):
        """Log conversation to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_logs (user_query, bot_response, confidence_score)
            VALUES (?, ?, ?)
        ''', (user_query, bot_response, confidence_score))
        conn.commit()
        conn.close()
        
    def get_categories(self) -> List[str]:
        """Get all available categories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM faqs ORDER BY category')
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories
        
    def get_faqs_by_category(self, category: str) -> List[Dict]:
        """Get FAQs for a specific category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT question, answer FROM faqs WHERE category = ?', (category,))
        faqs = [{"question": row[0], "answer": row[1]} for row in cursor.fetchall()]
        conn.close()
        return faqs

# Initialize chatbot
chatbot = CollegeChatbot()

# HTML Template for web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>College Helpdesk Chatbot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .chat-container { 
            background: white; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%; 
            max-width: 800px; 
            height: 600px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 20px; 
            text-align: center;
            border-radius: 20px 20px 0 0;
        }
        .chat-header h1 { font-size: 24px; margin-bottom: 5px; }
        .chat-header p { opacity: 0.9; font-size: 14px; }
        .chat-messages { 
            flex: 1; 
            padding: 20px; 
            overflow-y: auto; 
            background: #f8f9fa;
        }
        .message { 
            margin-bottom: 15px; 
            display: flex; 
            align-items: flex-start;
        }
        .message.user { justify-content: flex-end; }
        .message-content { 
            max-width: 70%; 
            padding: 12px 16px; 
            border-radius: 18px; 
            line-height: 1.4;
            word-wrap: break-word;
        }
        .message.user .message-content { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            border-bottom-right-radius: 4px;
        }
        .message.bot .message-content { 
            background: white; 
            border: 1px solid #e9ecef;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .chat-input { 
            padding: 20px; 
            background: white;
            border-top: 1px solid #e9ecef;
        }
        .input-group { 
            display: flex; 
            gap: 10px; 
        }
        .input-group input { 
            flex: 1; 
            padding: 12px 16px; 
            border: 2px solid #e9ecef; 
            border-radius: 25px; 
            outline: none;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        .input-group input:focus { 
            border-color: #667eea; 
        }
        .input-group button { 
            padding: 12px 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            border: none; 
            border-radius: 25px; 
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .input-group button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .categories { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 8px; 
            margin-top: 10px;
        }
        .category-btn { 
            padding: 6px 12px; 
            background: #f1f3f4; 
            border: 1px solid #e1e3e4; 
            border-radius: 15px; 
            cursor: pointer; 
            font-size: 12px;
            transition: all 0.3s ease;
        }
        .category-btn:hover { 
            background: #667eea; 
            color: white; 
            border-color: #667eea;
        }
        .typing-indicator {
            display: none;
            padding: 10px 16px;
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 18px;
            margin-bottom: 15px;
            max-width: 70%;
        }
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        .dot {
            width: 6px;
            height: 6px;
            background: #999;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🎓 College Helpdesk</h1>
            <p>Ask me anything about admissions, academics, campus life, and more!</p>
        </div>
        <div class="chat-messages" id="chatMessages">
            <div class="message bot">
                <div class="message-content">
                    👋 Hello! I'm your college helpdesk assistant. I can help you with questions about:
                    <br><br>
                    📚 <strong>Academics</strong> - Registration, grades, majors<br>
                    🎯 <strong>Admissions</strong> - Requirements, deadlines, applications<br>
                    💰 <strong>Financial Aid</strong> - Scholarships, tuition, payment<br>
                    🏫 <strong>Campus Life</strong> - Housing, dining, clubs<br>
                    💻 <strong>Technical Support</strong> - Portal access, WiFi<br>
                    📖 <strong>Library</strong> - Hours, study rooms<br>
                    <br>
                    What can I help you with today?
                </div>
            </div>
        </div>
        <div class="typing-indicator" id="typingIndicator">
            <div class="typing-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        </div>
        <div class="chat-input">
            <div class="input-group">
                <input type="text" id="messageInput" placeholder="Ask your question..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Send</button>
            </div>
            <div class="categories">
                <span class="category-btn" onclick="sendQuickQuery('admission requirements')">Admission Requirements</span>
                <span class="category-btn" onclick="sendQuickQuery('tuition payment')">Tuition Payment</span>
                <span class="category-btn" onclick="sendQuickQuery('class registration')">Class Registration</span>
                <span class="category-btn" onclick="sendQuickQuery('housing options')">Housing</span>
                <span class="category-btn" onclick="sendQuickQuery('library hours')">Library Hours</span>
            </div>
        </div>
    </div>

    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        function sendQuickQuery(query) {
            document.getElementById('messageInput').value = query;
            sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            showTypingIndicator();
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                hideTypingIndicator();
                addMessage(data.response, 'bot');
            } catch (error) {
                hideTypingIndicator();
                addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }
        }

        function addMessage(message, sender) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.innerHTML = message.replace(/\\n/g, '<br>');
            
            messageDiv.appendChild(contentDiv);
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function showTypingIndicator() {
            document.getElementById('typingIndicator').style.display = 'block';
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function hideTypingIndicator() {
            document.getElementById('typingIndicator').style.display = 'none';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    """Main chat interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        # Get response from chatbot
        response, confidence, category = chatbot.find_best_answer(user_message)
        
        # Log conversation
        chatbot.log_conversation(user_message, response, confidence)
        
        return jsonify({
            'response': response,
            'confidence': confidence,
            'category': category
        })
    except Exception as e:
        return jsonify({
            'response': 'Sorry, I encountered an error. Please try again.',
            'confidence': 0.0,
            'category': 'Error'
        }), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all FAQ categories"""
    categories = chatbot.get_categories()
    return jsonify({'categories': categories})

@app.route('/api/faqs/<category>', methods=['GET'])
def get_faqs_by_category(category):
    """Get FAQs for a specific category"""
    faqs = chatbot.get_faqs_by_category(category)
    return jsonify({'faqs': faqs})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get chatbot usage statistics"""
    conn = sqlite3.connect(chatbot.db_path)
    cursor = conn.cursor()
    
    # Total conversations
    cursor.execute('SELECT COUNT(*) FROM chat_logs')
    total_conversations = cursor.fetchone()[0]
    
    # Average confidence score
    cursor.execute('SELECT AVG(confidence_score) FROM chat_logs')
    avg_confidence = cursor.fetchone()[0] or 0
    
    # Most common queries
    cursor.execute('''
        SELECT user_query, COUNT(*) as count 
        FROM chat_logs 
        GROUP BY user_query 
        ORDER BY count DESC 
        LIMIT 5
    ''')
    common_queries = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'total_conversations': total_conversations,
        'average_confidence': round(avg_confidence, 3),
        'common_queries': [{'query': q[0], 'count': q[1]} for q in common_queries]
    })

if __name__ == '__main__':
    print("🎓 College Helpdesk Chatbot Starting...")
    print("📱 Web Interface: http://localhost:5000")
    print("🔌 API Endpoint: http://localhost:5000/chat")
    print("📊 Statistics: http://localhost:5000/api/stats")
    print("📚 Categories: http://localhost:5000/api/categories")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
