/**
 * Test utilities: render wrapper with providers.
 *
 * Creates a fresh QueryClient per test with retry disabled
 * to prevent flaky tests from retrying failed queries.
 *
 * Usage:
 *   import { renderWithProviders } from "@/testing/test-utils";
 *   renderWithProviders(<MyComponent />);
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";

function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

function createWrapper(): ({ children }: { children: ReactNode }) => ReactElement {
  const queryClient = createTestQueryClient();
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

export function renderWithProviders(ui: ReactElement, options?: Omit<RenderOptions, "wrapper">) {
  return render(ui, { wrapper: createWrapper(), ...options });
}

export { createTestQueryClient, createWrapper };
