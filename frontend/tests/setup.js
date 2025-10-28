/**
 * Test setup configuration for frontend tests
 */

// Setup for DOM testing
import '@testing-library/jest-dom';

// Mock fetch globally if needed
global.fetch = jest.fn();

// Setup cleanup after each test
afterEach(() => {
    jest.clearAllMocks();
});
