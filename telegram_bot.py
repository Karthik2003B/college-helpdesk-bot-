# Telegram Bot Integration for College Helpdesk
# Install: pip install python-telegram-bot

import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import asyncio
import os
from datetime import datetime

# Import our chatbot class
from college_chatbot import CollegeChatbot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramCollegeBot:
    def __init__(self, token: str):
        self.token = token
        self.chatbot = CollegeChatbot()
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        """Set up bot command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("categories", self.categories))
        self.application.add_handler(CommandHandler("stats", self.stats))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🎓 **Welcome to College Helpdesk Bot!**

I'm here to help you with all your college-related questions!

📚 **What I can help with:**
• Admissions & Applications
• Academic Information
• Financial Aid & Scholarships
• Campus Life & Housing
• Technical Support
• Library Services

💬 **How to use:**
• Just type your question and I'll do my best to help
• Use /categories to see all available topics
• Use /help for more commands

🚀 **Quick Start:** Try asking "What are the admission requirements?"
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 Admission Requirements", callback_data='quick_admission')],
            [InlineKeyboardButton("💰 Financial Aid", callback_data='quick_financial')],
            [InlineKeyboardButton("🏠 Housing Options", callback_data='quick_housing')],
            [InlineKeyboardButton("📚 Library Hours", callback_data='quick_library')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 **Available Commands:**

/start - Welcome message and quick options
/help - Show this help message
/categories - List all FAQ categories
/stats - Show bot usage statistics

💡 **Tips:**
• Ask questions in natural language
• Be specific for better answers
• Try rephrasing if you don't get the right answer
• Contact help@college.edu for complex issues

🔄 **Examples:**
• "When is the application deadline?"
• "How do I register for classes?"
• "What meal plans are available?"
• "How to reset my password?"
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    async def categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available categories"""
        categories = self.chatbot.get_categories()
        
        keyboard = []
        for category in categories:
            keyboard.append([InlineKeyboardButton(f"📂 {category}", callback_data=f'category_{category}')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📁 **Select a category to explore:**", 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
        
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot statistics"""
        try:
            conn = sqlite3.connect(self.chatbot.db_path)
            cursor = conn.cursor()
            
            # Get statistics
            cursor.execute('SELECT COUNT(*) FROM chat_logs')
            total_conversations = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(confidence_score) FROM chat_logs WHERE confidence_score > 0')
            avg_confidence = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                SELECT user_query, COUNT(*) as count 
                FROM chat_logs 
                GROUP BY user_query 
                ORDER BY count DESC 
                LIMIT 3
            ''')
            common_queries = cursor.fetchall()
            
            conn.close()
            
            stats_text = f"""
📊 **Bot Statistics:**

💬 Total Conversations: {total_conversations}
🎯 Average Confidence: {avg_confidence:.2f}

🔥 **Most Asked Questions:**
"""
            for i, (query, count) in enumerate(common_queries, 1):
                stats_text += f"{i}. {query} ({count}x)\n"
                
            await update.message.reply_text(stats_text, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text("❌ Sorry, couldn't retrieve statistics.")
            
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Handle quick questions
        if data.startswith('quick_'):
            question_map = {
                'quick_admission': 'What are the admission requirements?',
                'quick_financial': 'What financial aid is available?',
                'quick_housing': 'What housing options are available?',
                'quick_library': 'What are library hours?'
            }
            
            question = question_map.get(data)
            if question:
                response, confidence, category = self.chatbot.find_best_answer(question)
                
                # Add confidence indicator
                confidence_emoji = "🎯" if confidence > 0.7 else "📍" if confidence > 0.4 else "❓"
                
                await query.edit_message_text(
                    f"{confidence_emoji} **{category}**\n\n{response}",
                    parse_mode='Markdown'
                )
                
                # Log the conversation
                self.chatbot.log_conversation(question, response, confidence)
                
        # Handle category browsing
        elif data.startswith('category_'):
            category = data.replace('category_', '')
            faqs = self.chatbot.get_faqs_by_category(category)
            
            if faqs:
                response_text = f"📂 **{category} FAQs:**\n\n"
                for i, faq in enumerate(faqs[:5], 1):  # Limit to first 5 FAQs
                    response_text += f"**Q{i}:** {faq['question']}\n"
                    # Truncate long answers for Telegram
                    answer = faq['answer']
                    if len(answer) > 200:
                        answer = answer[:197] + "..."
                    response_text += f"**A:** {answer}\n\n"
                
                if len(faqs) > 5:
                    response_text += f"... and {len(faqs) - 5} more questions in this category.\n"
                    
                response_text += "\n💬 **Ask me anything specific!**"
                
                await query.edit_message_text(response_text, parse_mode='Markdown')
            else:
                await query.edit_message_text(f"No FAQs found for {category}")
                
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages"""
        user_message = update.message.text
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logger.info(f"User {username} ({user_id}): {user_message}")
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        try:
            # Get response from chatbot
            response, confidence, category = self.chatbot.find_best_answer(user_message)
            
            # Add confidence and category info
            confidence_emoji = "🎯" if confidence > 0.7 else "📍" if confidence > 0.4 else "❓"
            
            # Format response for Telegram
            formatted_response = f"{confidence_emoji} **{category}**\n\n{response}"
            
            # Add quick action buttons for low confidence responses
            keyboard = None
            if confidence < 0.4:
                keyboard = [
                    [InlineKeyboardButton("📞 Contact Support", url="tel:+15551234567")],
                    [InlineKeyboardButton("🌐 Visit Website", url="https://college.edu/help")],
                    [InlineKeyboardButton("📂 Browse Categories", callback_data="browse_categories")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
            else:
                reply_markup = None
                
            await update.message.reply_text(
                formatted_response, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Log conversation with additional Telegram info
            extended_query = f"[TG:{username}] {user_message}"
            self.chatbot.log_conversation(extended_query, response, confidence)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "❌ Sorry, I encountered an error. Please try again or contact support at help@college.edu"
            )
            
    def run(self):
        """Run the Telegram bot"""
        logger.info("Starting Telegram College Helpdesk Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

# WhatsApp Integration (using Twilio)
class WhatsAppCollegeBot:
    def __init__(self, account_sid: str, auth_token: str, whatsapp_number: str):
        from twilio.rest import Client
        self.client = Client(account_sid, auth_token)
        self.whatsapp_number = whatsapp_number
        self.chatbot = CollegeChatbot()
        
    def send_message(self, to_number: str, message: str):
        """Send WhatsApp message"""
        try:
            message = self.client.messages.create(
                body=message,
                from_=f'whatsapp:{self.whatsapp_number}',
                to=f'whatsapp:{to_number}'
            )
            return message.sid
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return None
            
    def handle_webhook(self, request_data):
        """Handle incoming WhatsApp messages (for Flask webhook)"""
        from_number = request_data.get('From', '').replace('whatsapp:', '')
        message_body = request_data.get('Body', '')
        
        if message_body:
            # Get response from chatbot
            response, confidence, category = self.chatbot.find_best_answer(message_body)
            
            # Format response for WhatsApp
            confidence_emoji = "🎯" if confidence > 0.7 else "📍" if confidence > 0.4 else "❓"
            formatted_response = f"{confidence_emoji} *{category}*\n\n{response}"
            
            if confidence < 0.4:
                formatted_response += "\n\n📞 *Need more help?*\nCall: (555) 123-4567\nEmail: help@college.edu"
                
            # Send response
            self.send_message(from_number, formatted_response)
            
            # Log conversation
            self.chatbot.log_conversation(f"[WA:{from_number}] {message_body}", response, confidence)

# Configuration and main execution
if __name__ == "__main__":
    import sys
    
    # Configuration - Replace with your actual tokens
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN')
    
    # Telegram Bot Configuration
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'YOUR_TWILIO_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'YOUR_TWILIO_TOKEN')
    WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', '+1234567890')
    
    if len(sys.argv) > 1:
        platform = sys.argv[1].lower()
        
        if platform == 'telegram':
            if TELEGRAM_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN':
                print("❌ Please set your Telegram bot token in environment variable TELEGRAM_BOT_TOKEN")
                print("📝 Get token from @BotFather on Telegram")
                sys.exit(1)
                
            bot = TelegramCollegeBot(TELEGRAM_TOKEN)
            print("🤖 Starting Telegram Bot...")
            print("📱 Message your bot to start chatting!")
            bot.run()
            
        elif platform == 'whatsapp':
            if TWILIO_ACCOUNT_SID == 'YOUR_TWILIO_SID':
                print("❌ Please set your Twilio credentials in environment variables")
                print("📝 Get credentials from Twilio Console")
                sys.exit(1)
                
            print("📱 WhatsApp bot configured. Use with Flask webhook.")
            print("🌐 Example webhook endpoint: /whatsapp-webhook")
            
        else:
            print("❌ Invalid platform. Use 'telegram' or 'whatsapp'")
    else:
        print("🎓 College Helpdesk Bot - Platform Integration")
        print("\n📋 Available platforms:")
        print("  python telegram_bot.py telegram    # Start Telegram bot")
        print("  python telegram_bot.py whatsapp    # WhatsApp info")
        print("\n🔧 Setup Requirements:")
        print("  Telegram: pip install python-telegram-bot")
        print("  WhatsApp: pip install twilio flask")
        print("\n📝 Environment Variables:")
        print("  TELEGRAM_BOT_TOKEN=your_telegram_token")
        print("  TWILIO_ACCOUNT_SID=your_twilio_sid")
        print("  TWILIO_AUTH_TOKEN=your_twilio_token")
        print("  WHATSAPP_NUMBER=your_whatsapp_number")
