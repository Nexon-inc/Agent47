const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './frontend',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/tests/frontend/jest.setup.js'],
  testEnvironment: 'jsdom',
  testPathIgnorePatterns: ['<rootDir>/.next/', '<rootDir>/node_modules/'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/frontend/$1',
    '^@/components/(.*)$': '<rootDir>/frontend/components/$1',
    '^@/lib/(.*)$': '<rootDir>/frontend/lib/$1',
    '^@/hooks/(.*)$': '<rootDir>/frontend/hooks/$1',
    '^@/app/(.*)$': '<rootDir>/frontend/app/$1',
  },
  collectCoverageFrom: [
    'frontend/**/*.{js,jsx,ts,tsx}',
    '!frontend/**/*.d.ts',
    '!frontend/**/*.stories.{js,jsx,ts,tsx}',
    '!frontend/**/node_modules/**',
    '!frontend/.next/**',
    '!frontend/out/**',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  testMatch: [
    '<rootDir>/tests/frontend/**/*.test.{js,jsx,ts,tsx}',
    '<rootDir>/tests/frontend/**/*.spec.{js,jsx,ts,tsx}',
  ],
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }],
  },
  transformIgnorePatterns: [
    '/node_modules/',
    '^.+\\.module\\.(css|sass|scss)$',
  ],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  testTimeout: 10000,
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
