# User Management Scripts

This directory contains scripts to help manage users in the Agent47 system during development.

## User Management Scripts

### Basic User Management (`manage_users.py`)

The `manage_users.py` script allows you to:

### List all users
```bash
cd backend
python scripts/manage_users.py list
```

### Delete a user by email
```bash
cd backend
python scripts/manage_users.py delete-email john@example.com
```

### Delete a user by ID
```bash
cd backend
python scripts/manage_users.py delete-id 1
```

### Clear all users (DANGEROUS!)
```bash
cd backend
python scripts/manage_users.py clear-all
```

### Comprehensive User Data Cleanup (`delete_all_users.py`)

The `delete_all_users.py` script provides more comprehensive cleanup:

#### List all user-related data
```bash
cd backend
python scripts/delete_all_users.py list
```

#### Delete ALL user data (DANGEROUS!)
```bash
cd backend
python scripts/delete_all_users.py delete
```

This script will delete:
- All users
- User selected agents
- Team invites
- Inbox messages
- User analytics
- User platform tokens
- Platform audit logs
- Tasks

⚠️ **WARNING**: This action cannot be undone!

## Password Reset Testing

To test the password reset functionality:

1. **Start the backend server:**
   ```bash
   cd backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test the flow:**
   - Go to `http://localhost:3000/auth`
   - Click "Login" tab
   - Click "Forgot password?"
   - Enter your email address
   - Check the backend logs for the reset URL (if SMTP is not configured)
   - Use the reset URL to reset your password

## Email Configuration

The system is configured to send emails from `agent47assist@gmail.com`. To enable email sending:

1. **Set up Gmail App Password:**
   - Go to Google Account settings
   - Enable 2-factor authentication
   - Generate an App Password for "Mail"
   - Use this password in your environment variables

2. **Set environment variables:**
   ```bash
   export EMAIL_SMTP_PASSWORD="your-app-password"
   ```

3. **Or create a `.env` file in the backend directory:**
   ```
   EMAIL_SMTP_PASSWORD=your-app-password
   ```

## Troubleshooting

### "User already exists" error
If you get an error that a user already exists when trying to sign up:

1. **List users to see what's in the database:**
   ```bash
   python scripts/manage_users.py list
   ```

2. **Delete the existing user:**
   ```bash
   python scripts/manage_users.py delete-email your-email@example.com
   ```

3. **Try signing up again**

### Password reset not working
1. **Check backend logs** for any error messages
2. **Verify email configuration** if using SMTP
3. **Check the reset URL** in the logs if SMTP is not configured
4. **Ensure the token is not expired** (tokens expire in 1 hour)

### Database connection issues
1. **Ensure the backend server is running**
2. **Check your database configuration** in `backend/core/config.py`
3. **Verify Supabase connection** if using Supabase

## Security Notes

- The user management script is for **development purposes only**
- Never use these scripts in production
- Always backup your database before running destructive operations
- The `clear-all` command will delete ALL users permanently
