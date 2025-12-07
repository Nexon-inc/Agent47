# 🎨 Frontend Development Setup

This guide will help you set up the Agent47 frontend for local development.

## 📋 Prerequisites

Before you begin, ensure you have:

- **Node.js 18+** installed
- **npm** or **yarn** package manager
- **Git** for version control
- **Backend running** on http://localhost:8000

## 🚀 Quick Setup

### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

### Step 2: Install Dependencies

```bash
# Using npm (recommended)
npm install

# Or using yarn
yarn install
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env.local

# Edit configuration
nano .env.local
```

### Step 4: Start Development Server

```bash
# Using npm
npm run dev

# Or using yarn
yarn dev
```

### Step 5: Access the Application

Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Environment Configuration

### Required Environment Variables

Create a `.env.local` file in the frontend directory:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Authentication
NEXT_PUBLIC_JWT_SECRET=your-jwt-secret-key

# AI Services
NEXT_PUBLIC_CHUTES_API_URL=https://api.chutes.ai
NEXT_PUBLIC_GROK_API_URL=http://localhost:8001

# Analytics (Optional)
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=your-ga-id
NEXT_PUBLIC_MIXPANEL_TOKEN=your-mixpanel-token

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_CHAT=true
NEXT_PUBLIC_ENABLE_VOICE=true

# Development
NODE_ENV=development
NEXT_PUBLIC_DEBUG=true
```

### Optional Environment Variables

```bash
# Payment Processing
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY=pk_test_...

# Social Media Integration
NEXT_PUBLIC_TWITTER_API_KEY=your-twitter-key
NEXT_PUBLIC_FACEBOOK_APP_ID=your-facebook-id
NEXT_PUBLIC_LINKEDIN_CLIENT_ID=your-linkedin-id

# File Upload
NEXT_PUBLIC_MAX_FILE_SIZE=10485760  # 10MB
NEXT_PUBLIC_ALLOWED_FILE_TYPES=image/jpeg,image/png,image/gif,video/mp4

# Monitoring
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
NEXT_PUBLIC_LOG_LEVEL=info
```

## 📦 Package.json Overview

The frontend uses the following key dependencies:

### Core Framework
- **Next.js 15.2.4**: React framework with SSR/SSG
- **React 19**: Latest React with concurrent features
- **TypeScript 5**: Type-safe JavaScript

### UI Components
- **Radix UI**: Accessible component primitives
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Beautiful icons
- **Framer Motion**: Animation library

### State Management
- **Zustand**: Lightweight state management
- **React Hook Form**: Form handling
- **Zod**: Schema validation

### Charts & Visualization
- **Recharts**: Chart library for analytics

### Development Tools
- **Jest**: Testing framework
- **Testing Library**: React testing utilities
- **ESLint**: Code linting
- **Prettier**: Code formatting

## 🛠️ Development Scripts

### Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint

# Testing
npm run test         # Run tests
npm run test:watch   # Run tests in watch mode
npm run test:coverage # Run tests with coverage
npm run test:ci      # Run tests for CI/CD

# Code Quality
npm run lint:fix     # Fix linting issues
npm run type-check   # TypeScript type checking
npm run format       # Format code with Prettier
```

### Custom Scripts

You can add custom scripts to `package.json`:

```json
{
  "scripts": {
    "dev:backend": "cd ../backend && python main.py",
    "dev:full": "concurrently \"npm run dev:backend\" \"npm run dev\"",
    "build:analyze": "ANALYZE=true npm run build",
    "storybook": "storybook dev -p 6006",
    "test:e2e": "playwright test"
  }
}
```

## 🏗️ Project Structure

```
frontend/
├── app/                    # Next.js 13+ app directory
│   ├── dashboard/         # Dashboard pages
│   ├── auth/             # Authentication pages
│   ├── api/              # API routes
│   └── globals.css       # Global styles
├── components/            # Reusable components
│   ├── ui/               # Base UI components
│   ├── dashboard/        # Dashboard-specific components
│   └── forms/            # Form components
├── lib/                  # Utility libraries
│   ├── utils.ts          # Utility functions
│   ├── api-client.ts     # API client
│   └── stores/           # Zustand stores
├── hooks/                # Custom React hooks
├── types/                # TypeScript type definitions
├── styles/               # Additional styles
├── public/               # Static assets
├── tests/                # Test files
├── .env.local           # Environment variables
├── .env.example         # Environment template
├── package.json         # Dependencies and scripts
├── tailwind.config.js   # Tailwind configuration
├── tsconfig.json        # TypeScript configuration
└── next.config.js       # Next.js configuration
```

## 🎨 Styling & Theming

### Tailwind CSS Configuration

The project uses Tailwind CSS with custom configuration:

```javascript
// tailwind.config.js
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a',
        },
        // Custom colors for agents
        aria: '#8b5cf6',
        clara: '#06b6d4',
        eric: '#10b981',
        jackie: '#f59e0b',
        joe: '#ef4444',
        purity: '#ec4899',
        shakes: '#84cc16',
      },
    },
  },
  plugins: [],
}
```

### Component Styling

Use the `cn` utility for conditional classes:

```tsx
import { cn } from "@/lib/utils"

function Button({ variant, className, ...props }) {
  return (
    <button
      className={cn(
        "px-4 py-2 rounded-md font-medium",
        {
          "bg-primary-500 text-white": variant === "primary",
          "bg-gray-200 text-gray-900": variant === "secondary",
        },
        className
      )}
      {...props}
    />
  )
}
```

## 🔌 API Integration

### API Client Setup

The frontend uses a custom API client for backend communication:

```typescript
// lib/api-client.ts
import axios from 'axios'

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 10000,
})

// Add request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default apiClient
```

### Using the API Client

```typescript
// Example: Fetching user data
import apiClient from '@/lib/api-client'

async function fetchUserData() {
  try {
    const response = await apiClient.get('/api/user/profile')
    return response.data
  } catch (error) {
    console.error('Failed to fetch user data:', error)
    throw error
  }
}
```

## 🧪 Testing Setup

### Jest Configuration

```javascript
// jest.config.js
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testEnvironment: 'jest-environment-jsdom',
}

module.exports = createJestConfig(customJestConfig)
```

### Writing Tests

```typescript
// tests/components/Button.test.tsx
import { render, screen } from '@testing-library/react'
import { Button } from '@/components/ui/button'

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('applies variant styles', () => {
    render(<Button variant="primary">Primary</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-primary-500')
  })
})
```

## 🚀 Deployment

### Build for Production

```bash
# Build the application
npm run build

# Start production server
npm run start
```

### Environment Variables for Production

```bash
# Production environment
NEXT_PUBLIC_API_URL=https://api.agent47.app
NEXT_PUBLIC_WS_URL=wss://api.agent47.app
NODE_ENV=production
NEXT_PUBLIC_DEBUG=false
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Module Not Found Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### 2. TypeScript Errors

```bash
# Check TypeScript configuration
npx tsc --noEmit

# Update type definitions
npm install --save-dev @types/node @types/react @types/react-dom
```

#### 3. Build Errors

```bash
# Check for syntax errors
npm run lint

# Clear Next.js cache
rm -rf .next
npm run build
```

#### 4. API Connection Issues

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check environment variables
echo $NEXT_PUBLIC_API_URL
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug environment variable
NEXT_PUBLIC_DEBUG=true npm run dev
```

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Radix UI Documentation](https://www.radix-ui.com)
- [Zustand Documentation](https://github.com/pmndrs/zustand)

## 🤝 Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation
4. Submit pull requests

## 📞 Support

- **Documentation**: Check this guide and inline comments
- **Issues**: Report bugs on GitHub
- **Community**: Join our Discord server
- **Email**: Contact support@agent47.app

---

**Happy coding! 🎉**

*Build amazing AI-powered applications with Agent47.*
