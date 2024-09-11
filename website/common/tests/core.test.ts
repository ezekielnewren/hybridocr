import { greet } from '../src/core';

test('test greeter', () => {
  expect(greet("alice")).toBe("Hello, alice!");
});
