#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');

console.log('🧪 Running Frontend Test Suite...\n');

const testTypes = [
  { name: 'Unit Tests', pattern: 'tests/unit/**/*.test.*' },
  { name: 'Integration Tests', pattern: 'tests/integration/**/*.test.*' },
  { name: 'Component Tests', pattern: 'tests/components/**/*.test.*' }
];

const runTests = (testType, pattern) => {
  console.log(`\n📋 Running ${testType}...`);
  console.log('=' .repeat(50));
  
  try {
    execSync(`npx jest ${pattern} --verbose --coverage`, {
      stdio: 'inherit',
      cwd: path.resolve(__dirname, '..')
    });
    console.log(`\n✅ ${testType} completed successfully!`);
  } catch (error) {
    console.error(`\n❌ ${testType} failed!`);
    process.exit(1);
  }
};

const runAllTests = () => {
  console.log('\n🚀 Running All Tests...');
  console.log('=' .repeat(50));
  
  try {
    execSync('npx jest --verbose --coverage', {
      stdio: 'inherit',
      cwd: path.resolve(__dirname, '..')
    });
    console.log('\n✅ All tests completed successfully!');
  } catch (error) {
    console.error('\n❌ Some tests failed!');
    process.exit(1);
  }
};

const runSpecificTest = (testName) => {
  console.log(`\n🎯 Running specific test: ${testName}`);
  console.log('=' .repeat(50));
  
  try {
    execSync(`npx jest ${testName} --verbose`, {
      stdio: 'inherit',
      cwd: path.resolve(__dirname, '..')
    });
    console.log(`\n✅ Test ${testName} completed successfully!`);
  } catch (error) {
    console.error(`\n❌ Test ${testName} failed!`);
    process.exit(1);
  }
};

const showHelp = () => {
  console.log(`
🧪 Frontend Test Runner

Usage:
  node run-tests.js [command] [options]

Commands:
  all                    Run all tests
  unit                   Run unit tests only
  integration            Run integration tests only
  components             Run component tests only
  specific <test-name>   Run a specific test file
  help                   Show this help message

Examples:
  node run-tests.js all
  node run-tests.js unit
  node run-tests.js specific api-client.test.ts
  node run-tests.js specific auth-flow.test.ts

Options:
  --watch                Run tests in watch mode
  --coverage             Generate coverage report
  --verbose              Show detailed test output
`);
};

const main = () => {
  const args = process.argv.slice(2);
  const command = args[0];

  switch (command) {
    case 'all':
      runAllTests();
      break;
    case 'unit':
      runTests('Unit Tests', 'tests/unit/**/*.test.*');
      break;
    case 'integration':
      runTests('Integration Tests', 'tests/integration/**/*.test.*');
      break;
    case 'components':
      runTests('Component Tests', 'tests/components/**/*.test.*');
      break;
    case 'specific':
      if (args[1]) {
        runSpecificTest(args[1]);
      } else {
        console.error('❌ Please specify a test name');
        process.exit(1);
      }
      break;
    case 'help':
    case '--help':
    case '-h':
      showHelp();
      break;
    default:
      if (command) {
        console.error(`❌ Unknown command: ${command}`);
        showHelp();
        process.exit(1);
      } else {
        runAllTests();
      }
  }
};

main();
