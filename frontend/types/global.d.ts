// Global type declarations for test environment

declare global {
  interface Window {
    triggerTestError?: () => void;
    testErrorBoundary?: {
      triggerError: () => void;
      triggerAsyncError: () => void;
    };
  }
}

export {};