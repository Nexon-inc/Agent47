import React from 'react';
import { render, screen } from '@testing-library/react';
import { AuthProvider } from '@/components/auth-provider';
import { useAuthStore } from '@/lib/stores/auth-store';

// Mock the auth store
jest.mock('@/lib/stores/auth-store');

// Mock Supabase
jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(() => ({
    auth: {
      signUp: jest.fn(),
      signInWithPassword: jest.fn(),
      signOut: jest.fn(),
      getSession: jest.fn(),
      onAuthStateChange: jest.fn()
    }
  }))
}));

describe('AuthProvider Component', () => {
  const mockAuthStore = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
    session: null,
    signup: jest.fn(),
    login: jest.fn(),
    logout: jest.fn(),
    resetPassword: jest.fn(),
    refreshUser: jest.fn(),
    clearError: jest.fn(),
    initialize: jest.fn(),
    initializeSupabase: jest.fn(),
    handleAuthStateChange: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuthStore as jest.Mock).mockReturnValue(mockAuthStore);
  });

  it('should render children without crashing', () => {
    render(
      <AuthProvider>
        <div data-testid="test-child">Test Content</div>
      </AuthProvider>
    );

    expect(screen.getByTestId('test-child')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should initialize auth state on mount', () => {
    render(
      <AuthProvider>
        <div>Test Content</div>
      </AuthProvider>
    );

    expect(mockAuthStore.initialize).toHaveBeenCalled();
  });

  it('should initialize Supabase on mount', () => {
    render(
      <AuthProvider>
        <div>Test Content</div>
      </AuthProvider>
    );

    expect(mockAuthStore.initializeSupabase).toHaveBeenCalled();
  });

  it('should handle multiple children', () => {
    render(
      <AuthProvider>
        <div data-testid="child-1">Child 1</div>
        <div data-testid="child-2">Child 2</div>
        <span data-testid="child-3">Child 3</span>
      </AuthProvider>
    );

    expect(screen.getByTestId('child-1')).toBeInTheDocument();
    expect(screen.getByTestId('child-2')).toBeInTheDocument();
    expect(screen.getByTestId('child-3')).toBeInTheDocument();
  });

  it('should handle empty children', () => {
    render(<AuthProvider>{null}</AuthProvider>);

    expect(mockAuthStore.initialize).toHaveBeenCalled();
    expect(mockAuthStore.initializeSupabase).toHaveBeenCalled();
  });

  it('should handle fragment children', () => {
    render(
      <AuthProvider>
        <>
          <div data-testid="fragment-child-1">Fragment Child 1</div>
          <div data-testid="fragment-child-2">Fragment Child 2</div>
        </>
      </AuthProvider>
    );

    expect(screen.getByTestId('fragment-child-1')).toBeInTheDocument();
    expect(screen.getByTestId('fragment-child-2')).toBeInTheDocument();
  });

  it('should handle complex nested children', () => {
    render(
      <AuthProvider>
        <div data-testid="parent">
          <header data-testid="header">Header</header>
          <main data-testid="main">
            <section data-testid="section">Section</section>
          </main>
          <footer data-testid="footer">Footer</footer>
        </div>
      </AuthProvider>
    );

    expect(screen.getByTestId('parent')).toBeInTheDocument();
    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByTestId('main')).toBeInTheDocument();
    expect(screen.getByTestId('section')).toBeInTheDocument();
    expect(screen.getByTestId('footer')).toBeInTheDocument();
  });
});
