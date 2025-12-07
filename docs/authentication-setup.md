# Agent47 Authentication System Setup

This document explains how the authentication system works and how to set it up and run it.

## Overview

The authentication system consists of:

1. **Backend Authentication** (`backend/core/authentication/`)
   - JWT-based authentication with access and refresh tokens
   - Password hashing with bcrypt
   - User management with database integration
   - Admin authentication and user management

2. **Frontend Authentication** (`frontend/`)
   - React/Next.js authentication forms
   - Zustand state management
   - API client for backend communication
   - Route protection middleware

3. **Database Integration**
   - User model with comprehensive fields
   - Admin statistics and user management
   - Real-time user tracking

## Backend Setup

### Prerequisites

1. **Python 3.8+**
2. **PostgreSQL** - For user database
3. **Redis** - For caching and sessions
4. **ChromaDB** - For vector storage
5. **Kafka** - For event streaming

### Installation

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the backend directory:
   ```env
   # Database
   DB_POSTGRES_HOST=localhost
   DB_POSTGRES_PORT=5432
   DB_POSTGRES_USER=agent47
   DB_POSTGRES_PASSWORD=agent47_password
   DB_POSTGRES_DB=agent47_db
   
   # Redis
   REDIS_HOST=localhost
   REDIS_PORT=6379
   
   # Security
   SECURITY_SECRET_KEY=your-super-secret-key-change-in-production
   SECURITY_ALGORITHM=HS256
   SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES=30
   SECURITY_REFRESH_TOKEN_EXPIRE_DAYS=7
   
   # API
   BACKEND_CORS_ORIGINS=["http://localhost:3000"]
   ```

3. **Initialize the database:**
   ```bash
   # Create PostgreSQL database
   createdb agent47_db
   
   # Run database migrations (if any)
   # The system will auto-create tables on first run
   ```

4. **Start the backend server:**
   ```bash
   cd backend
   python start_server.py
   ```

The server will start on `http://localhost:8000`

## Frontend Setup

### Prerequisites

1. **Node.js 18+**
2. **pnpm** (recommended) or npm

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   pnpm install
   ```

2. **Set up environment variables:**
   Create a `.env.local` file in the frontend directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

3. **Start the development server:**
   ```bash
   pnpm dev
   ```

The frontend will start on `http://localhost:3000`

## API Endpoints

### Authentication Endpoints

- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/reset-password-request` - Request password reset
- `POST /api/v1/auth/change-password` - Change password (authenticated)
- `GET /api/v1/auth/me` - Get current user info (authenticated)
- `POST /api/v1/auth/logout` - Logout (authenticated)

### Admin Endpoints

- `GET /api/v1/admin/users` - Get all users (admin only)
- `GET /api/v1/admin/stats` - Get admin statistics (admin only)

## User Registration Flow

1. **Frontend Form** - User fills out registration form with:
   - Email, username, password
   - Personal info (name, country, etc.)
   - Business info (optional)

2. **Backend Validation** - Server validates:
   - Email uniqueness
   - Username uniqueness
   - Password strength
   - Required fields

3. **User Creation** - Server creates user with:
   - Hashed password
   - Default tier (FREE)
   - Preferences stored as JSON

4. **Token Generation** - Server returns:
   - Access token (30 minutes)
   - Refresh token (7 days)
   - User information

5. **Frontend Storage** - Client stores:
   - Tokens in localStorage
   - User info in Zustand store

## Authentication Flow

1. **Login Request** - User submits email/password
2. **Backend Validation** - Server verifies credentials
3. **Token Generation** - Server creates new tokens
4. **Frontend Storage** - Client stores tokens
5. **Route Protection** - Middleware checks authentication

## Admin Features

### User Management
- View all registered users
- Track user statistics
- Monitor user activity
- User tier management

### Statistics Dashboard
- Total users count
- Active users count
- New users (30 days)
- Verification rates
- Tier distribution

## Security Features

1. **Password Security**
   - bcrypt hashing
   - Password strength validation
   - Minimum requirements enforcement

2. **Token Security**
   - JWT tokens with expiration
   - Refresh token rotation
   - Secure token storage

3. **Route Protection**
   - Middleware-based authentication
   - Admin-only route protection
   - Automatic redirects

4. **Data Validation**
   - Input sanitization
   - Email validation
   - SQL injection prevention

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    tier VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    preferences JSONB,
    api_usage JSONB DEFAULT '{}',
    billing_info JSONB
);
```

## Testing the System

1. **Start both servers:**
   ```bash
   # Backend
   cd backend && python start_server.py
   
   # Frontend
   cd frontend && pnpm dev
   ```

2. **Test registration:**
   - Go to `http://localhost:3000/auth`
   - Fill out the signup form
   - Check database for new user

3. **Test login:**
   - Use registered credentials
   - Verify token storage
   - Check dashboard access

4. **Test admin features:**
   - Login with enterprise tier user
   - Access `/admin` page
   - View user statistics

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check PostgreSQL is running
   - Verify connection credentials
   - Ensure database exists

2. **CORS Errors**
   - Check `BACKEND_CORS_ORIGINS` setting
   - Verify frontend URL is included

3. **Token Issues**
   - Check token expiration
   - Verify token format
   - Clear localStorage and retry

4. **Admin Access Denied**
   - Verify user tier is 'enterprise'
   - Check admin permissions
   - Review user role settings

### Logs

- **Backend logs:** `backend/logs/agent47.log`
- **Frontend logs:** Browser console
- **Database logs:** PostgreSQL logs

## Production Deployment

1. **Security Considerations**
   - Change default secret keys
   - Use HTTPS
   - Set up proper CORS
   - Configure rate limiting

2. **Database Setup**
   - Use production PostgreSQL
   - Set up backups
   - Configure connection pooling

3. **Environment Variables**
   - Use production values
   - Secure sensitive data
   - Use environment-specific configs

4. **Monitoring**
   - Set up logging
   - Monitor performance
   - Track user metrics

## Next Steps

After authentication is working:

1. **Connect Agent APIs** - Integrate individual agent endpoints
2. **Add Real-time Features** - WebSocket connections
3. **Implement File Upload** - S3 integration
4. **Add Payment Processing** - Stripe integration
5. **Enhance Admin Features** - More detailed analytics
