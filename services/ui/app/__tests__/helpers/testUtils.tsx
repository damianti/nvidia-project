/**
 * Test utilities and helpers for React Testing Library.
 */
import React, { ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { AuthProvider } from "@/contexts/AuthContext";
import * as AuthContextModule from "@/contexts/AuthContext";

interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  authUser?: {
    id: number;
    username: string;
    email: string;
  } | null;
  authLoading?: boolean;
}

/**
 * Custom render function that includes providers.
 * Use this instead of render() from @testing-library/react for components that need AuthContext.
 */
export function renderWithProviders(
  ui: ReactElement,
  {
    authUser = {
      id: 1,
      username: "testuser",
      email: "test@example.com",
    },
    authLoading = false,
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  // Mock AuthContext before rendering
  jest.spyOn(AuthContextModule, "useAuth").mockReturnValue({
    user: authUser,
    loading: authLoading,
    login: jest.fn(),
    signup: jest.fn(),
    logout: jest.fn(),
  });

  return render(ui, {
    wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    ...renderOptions,
  });
}

// Re-export everything from @testing-library/react
export * from "@testing-library/react";
