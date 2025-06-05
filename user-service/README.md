# User Service

The User Service handles user registration, authentication, and profile management. This service contains multiple intentional vulnerabilities for educational purposes.

## Endpoints

### Public Endpoints
- `POST /register` - User registration
- `POST /login` - User authentication

### User Management
- `GET /users/{id}` - Get user profile (VULNERABLE: No auth required)
- `PUT /users/{id}` - Update user profile (VULNERABLE: Can escalate privileges)
- `GET /users` - List all users (VULNERABLE: No auth required)

### Admin Endpoints
- `GET /admin/users` - Admin user listing (VULNERABLE: No admin check)

## Vulnerabilities

### API1: Broken Object Level Authorization (BOLA)
- Any user can access any other user's profile
- No authentication required for user data access

### API2: Broken Authentication
- MD5 password hashing (easily crackable)
- No rate limiting on login attempts
- Weak JWT secret key
- Long token expiration (30 days)

### API3: Broken Object Property Level Authorization
- Users can update their `is_admin` field
- No field-level access control

### API8: Security Misconfiguration
- SQL injection vulnerabilities in registration
- Verbose error messages expose database structure
- Debug mode enabled

## Database Schema

\`\`\`sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(64) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
\`\`\`

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `RABBITMQ_URL` - RabbitMQ connection string

## Security Issues to Test

1. **SQL Injection in Registration**:
\`\`\`bash
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test'\'''; DROP TABLE users; --", "email": "test@test.com", "password": "password"}'
\`\`\`

2. **Privilege Escalation**:
\`\`\`bash
curl -X PUT http://localhost:5001/users/2 \
  -H "Content-Type: application/json" \
  -d '{"is_admin": true}'
\`\`\`

3. **BOLA - Access any user**:
\`\`\`bash
curl http://localhost:5001/users/1
\`\`\`

## Default Admin Account

- Username: `admin`
- Password: `admin123`
- Email: `admin@example.com`
