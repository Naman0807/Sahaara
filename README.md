# Mental Wellness Chatbot

A Flask-based mental wellness chatbot application with crisis detection, journaling, micro-plans, and more.

## Features

- AI-powered conversations using Google Gemini
- Crisis detection and helpline escalation
- Multi-language support (English, Hindi, etc.)
- Mood tracking and wellness insights
- Journaling functionality
- Micro-plans for mental health
- Study timer with productivity tracking
- Badge system for achievements
- Myths and facts about mental health

## Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables (copy `.env.example` to `.env` and fill in your values)
6. Run the app: `python app.py`

## Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure your virtual environment is activated and all dependencies are installed
2. **Database Issues**: Check that the DATABASE_URL is correctly set and points to a writable location
3. **Static Files**: If static files aren't loading, check the static file mappings in the Web tab
4. **WSGI Errors**: Ensure your `wsgi.py` file is correctly configured

### Logs:

- Check the error log in the "Web" tab for deployment issues
- Use the PythonAnywhere console to test your app: `python wsgi.py`

## Environment Variables

Required:

- `SECRET_KEY`: Flask secret key for sessions
- `GEMINI_API_KEY`: Google Gemini API key for AI responses
- `DATABASE_URL`: Database connection string (SQLite for free tier)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

This project is licensed under the MIT License.
