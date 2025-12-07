/**
 * @jest-environment jsdom
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'

// Mock authentication components
const LoginForm = ({ onLogin }: { onLogin: (email: string, password: string) => void }) => {
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onLogin(email, password)
  }

  return (
    <form data-testid="login-form" onSubmit={handleSubmit}>
      <input
        data-testid="email-input"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
      />
      <input
        data-testid="password-input"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <button data-testid="login-button" type="submit">
        Login
      </button>
    </form>
  )
}

const Dashboard = ({ user }: { user: { email: string; name: string } }) => (
  <div data-testid="dashboard">
    <h1>Welcome, {user.name}!</h1>
    <p>Email: {user.email}</p>
  </div>
)

const AuthFlow = () => {
  const [user, setUser] = React.useState<{ email: string; name: string } | null>(null)

  const handleLogin = (email: string, password: string) => {
    // Mock successful login
    if (email === 'test@example.com' && password === 'password') {
      setUser({ email, name: 'Test User' })
    }
  }

  if (user) {
    return <Dashboard user={user} />
  }

  return <LoginForm onLogin={handleLogin} />
}

describe('Authentication Flow', () => {
  it('renders login form initially', () => {
    render(<AuthFlow />)
    
    expect(screen.getByTestId('login-form')).toBeInTheDocument()
    expect(screen.getByTestId('email-input')).toBeInTheDocument()
    expect(screen.getByTestId('password-input')).toBeInTheDocument()
    expect(screen.getByTestId('login-button')).toBeInTheDocument()
  })

  it('handles successful login', async () => {
    render(<AuthFlow />)
    
    const emailInput = screen.getByTestId('email-input')
    const passwordInput = screen.getByTestId('password-input')
    const loginButton = screen.getByTestId('login-button')

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password' } })
    fireEvent.click(loginButton)

      await waitFor(() => {
      expect(screen.getByTestId('dashboard')).toBeInTheDocument()
      expect(screen.getByText('Welcome, Test User!')).toBeInTheDocument()
      expect(screen.getByText('Email: test@example.com')).toBeInTheDocument()
    })
  })

  it('handles failed login', async () => {
    render(<AuthFlow />)
    
    const emailInput = screen.getByTestId('email-input')
    const passwordInput = screen.getByTestId('password-input')
    const loginButton = screen.getByTestId('login-button')

    fireEvent.change(emailInput, { target: { value: 'wrong@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
    fireEvent.click(loginButton)

      await waitFor(() => {
      expect(screen.getByTestId('login-form')).toBeInTheDocument()
      expect(screen.queryByTestId('dashboard')).not.toBeInTheDocument()
    })
  })
})
