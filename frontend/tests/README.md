# Frontend Test Suite

This directory contains comprehensive tests for the Agent47 frontend application, including unit tests, integration tests, and component tests.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual functions and modules
│   ├── api-client.test.ts   # API client functionality tests
│   └── auth-store.test.ts   # Authentication store tests
├── integration/             # Integration tests for complete workflows
│   └── auth-flow.test.ts    # Authentication flow tests
├── components/              # Component tests for UI components
│   └── auth-provider.test.tsx # Auth provider component tests
├── __mocks__/               # Mock implementations for external dependencies
│   └── supabase.ts          # Supabase client mock
├── setup.ts                 # Test setup and global configurations
├── run-tests.js             # Test runner script
└── README.md                # This file
```

## Test Categories

### Unit Tests
- **API Client Tests** (`api-client.test.ts`): Tests for the API client functionality including:
  - Authentication methods (signup, login, logout)
  - Token management
  - HTTP request handling
  - User management
  - Password management
  - Supabase integration

- **Auth Store Tests** (`auth-store.test.ts`): Tests for the authentication store including:
  - State management
  - Authentication actions
  - Error handling
  - Supabase session management

### Integration Tests
- **Auth Flow Tests** (`auth-flow.test.ts`): Tests for complete authentication workflows including:
  - Signup flow
  - Login flow
  - Logout flow
  - Password reset flow
  - Session management
  - Error handling

### Component Tests
- **Auth Provider Tests** (`auth-provider.test.tsx`): Tests for the authentication provider component including:
  - Component rendering
  - Initialization
  - Children handling
  - Error boundaries

## Running Tests

### Using the Test Runner Script

```bash
# Run all tests
node tests/run-tests.js all

# Run specific test categories
node tests/run-tests.js unit
node tests/run-tests.js integration
node tests/run-tests.js components

# Run a specific test file
node tests/run-tests.js specific api-client.test.ts
node tests/run-tests.js specific auth-flow.test.ts

# Show help
node tests/run-tests.js help
```

### Using Jest Directly

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npx jest api-client.test.ts

# Run tests matching a pattern
npx jest --testPathPattern=unit
npx jest --testPathPattern=integration
npx jest --testPathPattern=components
```

### Using Package Scripts

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run tests in CI mode
npm run test:ci

# Run unit tests only
npm run test:unit

# Run integration tests only
npm run test:integration

# Run component tests only
npm run test:components
```

## Test Configuration

### Jest Configuration
The Jest configuration is defined in `jest.config.js` and includes:
- Test environment setup (jsdom)
- Module path mapping
- Coverage thresholds
- Test file patterns
- Transform configurations

### Test Setup
The test setup is configured in `tests/setup.ts` and includes:
- Environment variable mocking
- DOM API mocking
- Console method mocking
- Global test utilities

### Mocks
External dependencies are mocked in the `__mocks__` directory:
- **Supabase Client**: Mocked in `supabase.ts` for testing without actual Supabase connection

## Writing Tests

### Unit Test Example

```typescript
import { apiClient } from '@/lib/api-client';

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should handle successful login', async () => {
    const mockTokens = {
      access_token: 'token',
      refresh_token: 'refresh',
      user: { id: 1, email: 'test@example.com' }
    };

    (apiClient.login as jest.Mock).mockResolvedValue(mockTokens);

    const result = await apiClient.login({
      email: 'test@example.com',
      password: 'password123'
    });

    expect(result).toEqual(mockTokens);
  });
});
```

### Integration Test Example

```typescript
import { useAuthStore } from '@/lib/stores/auth-store';

describe('Auth Flow Integration', () => {
  it('should complete signup flow successfully', async () => {
    const mockAuthStore = {
      signup: jest.fn().mockResolvedValue(true)
    };

    (useAuthStore as jest.Mock).mockReturnValue(mockAuthStore);

    const result = await mockAuthStore.signup(signupData);
    expect(result).toBe(true);
  });
});
```

### Component Test Example

```typescript
import { render, screen } from '@testing-library/react';
import { AuthProvider } from '@/components/auth-provider';

describe('AuthProvider Component', () => {
  it('should render children without crashing', () => {
    render(
      <AuthProvider>
        <div data-testid="test-child">Test Content</div>
      </AuthProvider>
    );

    expect(screen.getByTestId('test-child')).toBeInTheDocument();
  });
});
```

## Coverage Requirements

The test suite has the following coverage thresholds:
- **Branches**: 80%
- **Functions**: 80%
- **Lines**: 80%
- **Statements**: 80%

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Mock External Dependencies**: Use mocks for external services and APIs
3. **Test Both Success and Error Cases**: Ensure error handling is properly tested
4. **Use Descriptive Test Names**: Test names should clearly describe what is being tested
5. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification phases
6. **Mock Cleanup**: Always clear mocks between tests to avoid test interference

## Troubleshooting

### Common Issues

1. **Module Resolution Errors**: Ensure the Jest configuration includes proper module path mapping
2. **Mock Not Working**: Check that mocks are properly configured and imported
3. **Async Test Failures**: Ensure proper async/await handling and test timeouts
4. **Coverage Threshold Failures**: Review uncovered code and add appropriate tests

### Debug Mode

Run tests in debug mode for more detailed output:

```bash
DEBUG=* npm test
```

### Verbose Output

Get detailed test output:

```bash
npm test -- --verbose
```

## Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Add appropriate mocks for external dependencies
3. Ensure tests cover both success and error scenarios
4. Update this README if adding new test categories or patterns
5. Maintain the coverage thresholds

## Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
