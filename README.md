# Student Management System Backend

Flask backend for the student management system.

## Features

- RESTful API
- JWT Authentication
- Role-based access control
- Student score management
- Score analysis

## Tech Stack

- Python
- Flask
- SQLAlchemy
- JWT
- MySQL
- Redis

## Project Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Initialize database
python run.py
```

## Environment Variables

Copy `.env.example` to `.env` and adjust the values:

```
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=mysql+pymysql://username:password@localhost/dbname
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

## API Documentation

### Authentication
- POST /api/auth/register - Register new user
- POST /api/auth/login - User login
- POST /api/auth/refresh - Refresh access token

### Student
- GET /api/student/scores - Get student scores
- GET /api/student/major-ranking - Get major ranking
- GET /api/student/score-distribution - Get score distribution
- GET /api/student/school-ranking - Get school ranking

## Project Structure

```
app/
├── __init__.py
├── config.py
├── models/
├── routes/
└── utils/
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License 