module.exports = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/__tests__'],
  setupFiles: ['<rootDir>/__tests__/setup.js', 'jest-canvas-mock'],
  testMatch: ['**/*.test.js'],
  moduleDirectories: ['node_modules', '<rootDir>/js'],
  transform: {},
};