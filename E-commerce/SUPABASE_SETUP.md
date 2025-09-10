# Supabase Setup Guide for Django E-commerce Project

## 1. Environment Configuration

Create a `.env` file in your project root with these values:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# Supabase Database Configuration
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-database-password
SUPABASE_DB_HOST=db.your-project-ref.supabase.co
SUPABASE_DB_PORT=5432

# Optional: Supabase API Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

## 2. Get Your Supabase Credentials

1. Go to your Supabase project dashboard
2. Navigate to Settings > Database
3. Copy the connection details:
   - Host: `db.your-project-ref.supabase.co`
   - Database name: `postgres`
   - Username: `postgres`
   - Password: Your database password

## 3. Run Migrations

Once your .env file is configured, run:

```bash
# Activate virtual environment
env\Scripts\Activate.ps1

# Make migrations
python manage.py makemigrations

# Apply migrations to Supabase
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

## 4. Test Your Connection

```bash
# Test database connection
python manage.py dbshell
```

## 5. Current Project Status

✅ PostgreSQL adapter (psycopg2-binary) - INSTALLED
✅ Supabase Python client - INSTALLED  
✅ Django settings configured for Supabase
✅ User signup endpoint implemented
✅ URL routing configured

## 6. What's Working

Your user signup endpoint is ready to work with Supabase:
- POST `/signup/` with JSON: `{"username": "test", "email": "test@email.com", "password": "password123"}`
- Validates unique username and email
- Stores hashed passwords
- Returns user data on success

## 7. Next Steps

1. Configure your `.env` file with real Supabase credentials
2. Run migrations to create tables in Supabase
3. Test the signup endpoint
4. Check your Supabase dashboard to see the data

## 8. Troubleshooting

If you get connection errors:
- Check your Supabase project is not paused
- Verify your database password
- Ensure your IP is whitelisted in Supabase (or disable IP restrictions)
- Check that your project reference is correct in the host URL
