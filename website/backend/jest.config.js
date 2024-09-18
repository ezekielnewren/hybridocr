module.exports = {
  preset: 'ts-jest', // Use ts-jest to transform TypeScript files
  testEnvironment: 'node', // Use the Node.js environment for testing
  transform: {
    '^.+\\.ts$': 'ts-jest', // Use ts-jest for all .ts files
  },
  moduleFileExtensions: ['ts', 'js'], // Include .ts and .js file extensions
  roots: ['<rootDir>/tests'], // Specify the test directory
};
