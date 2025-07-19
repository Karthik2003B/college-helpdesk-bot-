# College Helpdesk Bot

A smart chatbot system designed to help students with college-related queries and information. This bot provides instant responses to frequently asked questions about admissions, academics, campus facilities, and more.

## Features

- 🤖 **AI-Powered Responses**: Intelligent chatbot that understands and responds to student queries
- 📚 **FAQ Database**: Comprehensive database of college-related questions and answers
- 💬 **Telegram Integration**: Easy-to-use Telegram bot interface
- 🔍 **Smart Search**: Quickly finds relevant information from the knowledge base
- 📱 **Mobile Friendly**: Works seamlessly on mobile devices through Telegram

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Bot Platform**: Telegram Bot API
- **AI/NLP**: Natural Language Processing for query understanding

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/college-helpdesk-bot.git
   cd college-helpdesk-bot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv chatbot_env
   source chatbot_env/bin/activate  # On Windows: chatbot_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file and add your Telegram Bot Token:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

5. **Initialize the database**
   The SQLite database (`college_faq.db`) should be automatically created when you run the bot.

## Usage

### Running the Flask Web Interface
```bash
flask run
```
The web interface will be available at `http://localhost:5000`

### Running the Telegram Bot
```bash
python telegram_bot.py
```

### Using the Chatbot
1. Start a conversation with your Telegram bot
2. Ask questions about:
   - Admissions and enrollment
   - Course information
   - Campus facilities
   - Academic policies
   - Student services
   - And much more!

## Project Structure

```
college-helpdesk-bot/
├── college_chatbot.py      # Main chatbot logic
├── telegram_bot.py         # Telegram bot implementation
├── college_faq.db         # SQLite database with FAQs
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation
```

## Configuration

### Telegram Bot Setup
1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Get your bot token
4. Add the token to your `.env` file

### Database Customization
You can modify the `college_faq.db` database to add your college-specific information:
- Update FAQ entries
- Add new categories
- Customize responses

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development

### Adding New FAQs
To add new questions and answers to the bot:
1. Open the SQLite database
2. Insert new entries into the FAQ table
3. Restart the bot to load new data

### Improving NLP
The bot's natural language understanding can be enhanced by:
- Adding more training data
- Implementing better text preprocessing
- Using advanced NLP models

## Troubleshooting

### Common Issues

**Port 5000 already in use**
```bash
# Find and kill the process using port 5000
lsof -i :5000
kill -9 <PID>

# Or run on a different port
flask run --port 3001
```

**Bot not responding**
- Check your internet connection
- Verify the Telegram bot token
- Ensure the bot script is running

**Database errors**
- Check if `college_faq.db` exists
- Verify database permissions
- Restart the application

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or support, please contact:
- Email: your.email@college.edu
- GitHub: [@your-username](https://github.com/your-username)

## Acknowledgments

- Thanks to the Telegram Bot API for providing an excellent platform
- Flask community for the web framework
- Contributors who helped improve this project

---

**Note**: This is a development version. For production deployment, please use a proper WSGI server instead of Flask's development server.
