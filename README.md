# Devy Career Advisor

An intelligent AI-powered career recommendation system that helps users discover their ideal tech career path through natural conversation. Devy evaluates users across six core technology roles and provides personalized recommendations with actionable next steps.

## 🚀 Features

- **Conversational AI Interface**: Natural chat-based interaction for gathering user information
- **Comprehensive Career Assessment**: Evaluates compatibility with 6 core tech roles
- **Personalized Recommendations**: Match scores and detailed reasoning for each career path
- **Actionable Guidance**: Specific next steps for pursuing recommended careers
- **Session Management**: Persistent conversations with automatic session handling
- **Professional UI**: Clean, responsive web interface optimized for career guidance

## 🎯 Supported Career Paths

1. **Frontend Developer** - Building user-facing web interfaces and experiences
2. **Backend Developer** - Creating server-side systems and APIs
3. **Mobile Developer** - Developing applications for smartphones and tablets
4. **Data Scientist** - Analyzing data to generate insights and support decisions
5. **Machine Learning Engineer** - Building and deploying ML models in production
6. **UI/UX Designer** - Designing intuitive and aesthetically pleasing user experiences

## 🏗️ System Architecture

### Core Components

```plaintext
├── app/
│   ├── main.py              # FastAPI application and route handlers
│   ├── config.py            # Application configuration and settings
│   ├── database.py          # Database connection and session management
│   ├── models.py            # SQLAlchemy ORM models for data persistence
│   ├── schemas.py           # Pydantic schemas for data validation
│   ├── services/            # Business logic and service layer
│   │   ├── ai_service.py    # GitHub AI integration and conversation processing
│   │   └── chat_service.py  # Chat flow management and session handling
│   ├── utils/               # Utility functions and helpers
│   │   ├── logging.py       # Centralized logging configuration
│   │   └── validation.py    # Data validation and sanitization
│   └── templates/           # Jinja2 HTML templates
│       └── index.html       # Main chat interface
├── static/                  # Frontend assets
│   ├── script.js           # JavaScript for chat interface
│   └── style.css           # Stylesheet for UI components
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
└── README.md               # This file
```

### Data Models

- **User**: Stores personal information and preferences collected during assessment
- **Session**: Manages conversation state and context across interactions
- **ChatMessage**: Individual messages in the conversation history
- **Assessment**: Complete career evaluation results with recommendations

### Service Layer

- **AIService**: Handles GitHub AI integration, prompt management, and response processing
- **ChatService**: Manages conversation flow, session state, and database operations

## 🛠️ Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database
- GitHub Token with AI access

### Local Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd devspace
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:

   ```env
   GITHUB_TOKEN=your_github_token_here
   DATABASE_URL=postgresql://username:password@localhost:5432/devy_db
   SESSION_SECRET_KEY=your_secure_secret_key_here
   AZURE_AI_ENDPOINT=https://models.github.ai/inference
   AZURE_AI_DEPLOYMENT_NAME=openai/gpt-4o
   ```

5. **Set up PostgreSQL database**

   ```sql
   CREATE DATABASE devy_db;
   CREATE USER devy_user WITH ENCRYPTED PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE devy_db TO devy_user;
   ```

6. **Run the application**

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Access the application**

   Open your browser and navigate to `http://localhost:8000`

### Docker Deployment

1. **Build the Docker image**

   ```bash
   docker build -t devy-career-advisor .
   ```

2. **Run with Docker Compose**

   Create a `docker-compose.yml` file:

   ```yaml
   version: '3.8'
   services:
     app:
       build: .
       ports:
         - \"8000:8000\"
       environment:
         - GITHUB_TOKEN=${GITHUB_TOKEN}
         - DATABASE_URL=postgresql://postgres:password@db:5432/devy_db
         - SESSION_SECRET_KEY=${SESSION_SECRET_KEY}
       depends_on:
         - db
     
     db:
       image: postgres:15
       environment:
         - POSTGRES_DB=devy_db
         - POSTGRES_PASSWORD=password
       volumes:
         - postgres_data:/var/lib/postgresql/data
   
   volumes:
     postgres_data:
   ```

3. **Start the services**

   ```bash
   docker-compose up -d
   ```

## 📖 Usage Examples

### Basic Conversation Flow

1. **User starts conversation**

   ```plaintext
   User: Hi there!
   Devy: Hello! I'm Devy, your AI career advisor. I'm here to help you discover 
         which tech career path might be the best fit for you. What's your name?
   ```

2. **Information gathering**

   ```plaintext
   User: My name is Alex
   Devy: Nice to meet you, Alex! Tell me a bit about your educational background. 
         Are you currently in school, a recent graduate, or looking to transition careers?
   ```

3. **Assessment completion**

   ```plaintext
   User: I think I have a good sense of what I like now.
   Devy: Perfect! I have enough information to create your personalized career 
         assessment. Let me prepare your results...
   ```

### API Integration

The application provides REST endpoints for programmatic access:

```python
import requests

# Send a chat message
response = requests.post(
    "http://localhost:8000/chat",
    data={"user_message": "Hello, I'm interested in tech careers"}
)

# Create a new session
response = requests.post("http://localhost:8000/new-session")
session_id = response.json()["session_id"]
```

### Assessment Result Structure

```json
{
  "user_summary": {
    "name": "Alex",
    "age": "22",
    "education_level": "Bachelor's in Computer Science",
    "technical_knowledge": "Programming fundamentals, some web development",
    "top_subjects": ["Mathematics", "Computer Science"],
    "interests_dreams": "Building user-friendly applications"
  },
  "career_recommendations": [
    {
      "career_name": "Frontend Developer",
      "match_score": 85,
      "reasoning": "Strong alignment with interest in user-facing applications...",
      "suggested_next_steps": [
        "Learn modern JavaScript frameworks like React or Vue",
        "Build portfolio projects showcasing UI/UX skills"
      ]
    }
  ],
  "overall_assessment_notes": "Based on your interests and background..."
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_TOKEN` | GitHub API token for AI access | - | Yes |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@host:port/database` | Yes |
| `APP_NAME` | Application display name | `Devy Career Advisor` | No |
| `SESSION_SECRET_KEY` | Secret key for session encryption | `your_secret_key_here` | Yes |
| `AZURE_AI_ENDPOINT` | GitHub AI inference endpoint | `https://models.github.ai/inference` | No |
| `AZURE_AI_DEPLOYMENT_NAME` | AI model name to use | `openai/gpt-4o` | No |

### Database Configuration

The application uses PostgreSQL with SQLAlchemy ORM. Connection pooling is configured for production use:

- Pool size: 10 connections
- Max overflow: 20 connections
- Connection validation: Enabled
- Connection recycling: Every hour

### Logging Configuration

Structured logging is configured with different levels for different components:

- Application logs: INFO level
- Database logs: WARNING level
- Third-party libraries: WARNING level

## 🧪 Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Structure

```plaintext
tests/
├── test_models.py          # Database model tests
├── test_services.py        # Service layer tests
├── test_api.py             # API endpoint tests
└── test_utils.py           # Utility function tests
```

### Manual Testing

1. **Test conversation flow**
   - Start new session
   - Engage in natural conversation
   - Verify assessment generation
   - Check data persistence

2. **Test error handling**
   - Invalid session IDs
   - Network connectivity issues
   - Malformed input data

## 🤝 Contributing

We welcome contributions to improve Devy! Please follow these guidelines:

### Development Workflow

1. **Fork the repository**

   ```bash
   git fork <repository-url>
   ```

2. **Create feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes following our standards**
   - Follow PEP8 style guidelines
   - Add comprehensive docstrings
   - Include type hints
   - Write unit tests for new functionality

4. **Run quality checks**

   ```bash
   # Format code
   black app/
   
   # Check style
   flake8 app/
   
   # Type checking
   mypy app/
   
   # Run tests
   pytest
   ```

5. **Submit pull request**
   - Clear description of changes
   - Reference any related issues
   - Include test results

### Code Style Guidelines

- **Python**: Follow PEP8 with 88-character line limit
- **Documentation**: Google-style docstrings for all functions and classes
- **Type Hints**: Required for all public functions and class methods
- **Error Handling**: Use specific exceptions with descriptive messages
- **Logging**: Use structured logging with appropriate levels

### Adding New Features

1. **AI Prompt Modifications**
   - Update system prompt in `ai_service.py`
   - Ensure backward compatibility
   - Test with various user inputs

2. **New Career Paths**
   - Update career list in validation utilities
   - Modify AI system prompt
   - Update frontend display logic

3. **Database Schema Changes**
   - Create migration scripts
   - Update model classes
   - Update schemas and validation

### Bug Reports

When reporting bugs, please include:

- **Environment details** (OS, Python version, dependencies)
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Error messages** or logs
- **Sample data** if applicable

### Feature Requests

For new features, please:

- **Describe the use case** and problem being solved
- **Provide examples** of expected behavior
- **Consider impact** on existing functionality
- **Suggest implementation approach** if applicable

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** for providing the underlying language model capabilities
- **GitHub** for AI inference infrastructure
- **FastAPI** for the excellent web framework
- **SQLAlchemy** for robust database ORM
- **Pydantic** for data validation and serialization

## 📞 Support

If you encounter issues or have questions:

1. **Check the documentation** in this README
2. **Search existing issues** in the repository
3. **Create a new issue** with detailed information
4. **Join our community discussions** for general questions
