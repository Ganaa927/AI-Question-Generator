# AI Question Generator

An intelligent question generation system powered by Google's Gemini AI, designed for creating language learning exercises and educational content.

## 🌟 Features

- **Smart Question Generation**: Uses Google Gemini AI to create contextual questions
- **Multiple Deployment Options**: 
  - Local development with Flask
  - Google Colab integration
- **Language Learning Focus**: Specialized for translation exercises and language practice
- **JSON Structure Matching**: Maintains consistent question formats
- **Real-time Generation**: Fast question creation with detailed error handling

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai-question-generator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your Gemini API key
   # GEMINI_API_KEY=your_actual_api_key_here
   ```

4. **Run the application**
   ```bash
   python local_backend.py
   ```

5. **Open your browser**
   - Navigate to `http://localhost:5000`
   - The application will be ready to use!

### Google Colab Setup

1. **Upload files to Colab**
   - Upload `colab_ai_backend.py` and `ai_question_generator.html`

2. **Install dependencies**
   ```python
   !pip install flask-ngrok google-generativeai --quiet
   ```

3. **Set your API key**
   ```python
   import os
   os.environ['GEMINI_API_KEY'] = 'your_api_key_here'
   ```

4. **Run the backend**
   ```python
   exec(open('colab_ai_backend.py').read())
   ```

## 📖 Usage

1. **Upload JSON Data**: Provide a sample JSON structure for your questions
2. **Set Parameters**: 
   - Choose target language
   - Specify topic/subject
   - Set number of questions (1-20)
3. **Generate**: Click generate to create new questions matching your format
4. **Download**: Export generated questions as JSON

## 🛠 Technical Details

### Architecture

- **Backend**: Flask web server with Google Gemini AI integration
- **Frontend**: Single-page HTML application with modern UI
- **AI Model**: Google Gemini 2.5 Pro for question generation

### API Endpoints

- `GET /` - Serve the main application
- `POST /generate-fast` - Fast question generation
- `POST /generate` - Standard question generation
- `GET /health` - Health check and status

### Configuration Options

The application supports various configuration options through environment variables:

- `GEMINI_API_KEY` - Your Google Gemini API key (required)

## 🔧 Development

### Project Structure

```
project/
├── local_backend.py          # Flask backend for local development
├── colab_ai_backend.py       # Backend optimized for Google Colab
├── ai_question_generator.html # Frontend interface
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
└── README.md               # This file
```

### Key Features

- **Error Handling**: Comprehensive error logging and user feedback
- **JSON Repair**: Automatic fixing of common JSON formatting issues
- **Flexible Input**: Supports various JSON structures and formats
- **Development-Friendly**: Detailed logging and debug information

## 🚨 Important Notes

### Security

- **Never commit API keys** to version control
- **Use environment variables** for sensitive configuration
- **Review logs** before sharing - they may contain sensitive information

### API Limits

- Gemini API has rate limits and usage quotas
- Monitor your API usage in the Google Cloud Console
- Consider implementing rate limiting for production use

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the logs in `app.log` (local development)
- Verify your Gemini API key is correctly set
- Ensure all dependencies are installed

---

**⚠️ Remember**: Always keep your API keys secure and never commit them to version control! 