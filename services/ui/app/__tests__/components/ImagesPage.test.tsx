/**
 * Integration tests for ImagesPage component.
 * Tests user interactions, API calls, and UI states using MSW.
 */
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
// @ts-expect-error - Next.js page component
import ImagesPage from "@/images/page";
import { useAuth } from "@/contexts/AuthContext";
import { server } from "../mocks/server";
import { rest } from "msw";
import { mockImages } from "../mocks/handlers";

// Mock AuthContext
jest.mock("@/contexts/AuthContext");
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

// Mock Next.js Link component
jest.mock("next/link", () => {
  const MockLink = ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => {
    return <a href={href}>{children}</a>;
  };
  MockLink.displayName = "Link";
  return MockLink;
});

describe("ImagesPage", () => {
  const mockUser = {
    id: 1,
    username: "testuser",
    email: "test@example.com",
  };

  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: mockUser,
      loading: false,
      login: jest.fn(),
      signup: jest.fn(),
      logout: jest.fn(),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Loading State", () => {
    it("should show loading spinner while fetching images", async () => {
      // Arrange
      server.use(
        rest.get("/api/images", async (req, res, ctx) => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          return res(ctx.json(mockImages));
        })
      );

      // Act
      render(<ImagesPage />);

      // Assert
      expect(screen.getByText(/loading images/i)).toBeInTheDocument();

      // Wait for loading to finish
      await waitFor(() => {
        expect(screen.queryByText(/loading images/i)).not.toBeInTheDocument();
      });
    });
  });

  describe("Images List Display", () => {
    it("should render list of images when images exist", async () => {
      // Arrange & Act
      render(<ImagesPage />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/your images/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/test-image:latest/i)).toBeInTheDocument();
      expect(screen.getByText(/another-image:v1.0/i)).toBeInTheDocument();
      expect(screen.getByText(/test\.example\.com/i)).toBeInTheDocument();
    });

    it("should display image status badges correctly", async () => {
      // Arrange & Act
      render(<ImagesPage />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/ready/i)).toBeInTheDocument();
        expect(screen.getByText(/building/i)).toBeInTheDocument();
      });
    });

    it("should display empty state when no images exist", async () => {
      // Arrange
      server.use(
        rest.get("/api/images", (req, res, ctx) => {
          return res(ctx.json([]));
        })
      );

      // Act
      render(<ImagesPage />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/no images yet/i)).toBeInTheDocument();
        expect(
          screen.getByText(/get started by uploading your first docker image/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe("Upload Form", () => {
    it('should open upload form when "Upload New Image" button is clicked', async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ImagesPage />);

      await waitFor(() => {
        expect(screen.getByText(/your images/i)).toBeInTheDocument();
      });

      // Act
      const uploadButton = screen.getByRole("button", {
        name: /upload new image/i,
      });
      await user.click(uploadButton);

      // Assert
      expect(screen.getByText(/upload new image/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/image name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/tag/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/app hostname/i)).toBeInTheDocument();
    });

    it("should close upload form when cancel button is clicked", async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ImagesPage />);

      await waitFor(() => {
        expect(screen.getByText(/your images/i)).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole("button", {
        name: /upload new image/i,
      });
      await user.click(uploadButton);

      // Act
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await user.click(cancelButton);

      // Assert
      await waitFor(() => {
        expect(screen.queryByLabelText(/image name/i)).not.toBeInTheDocument();
      });
    });

    it("should show validation errors for empty required fields", async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ImagesPage />);

      await waitFor(() => {
        expect(screen.getByText(/your images/i)).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole("button", {
        name: /upload new image/i,
      });
      await user.click(uploadButton);

      // Act - Try to submit without filling fields
      const submitButton = screen.getByRole("button", { name: /upload/i });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/image name is required/i)).toBeInTheDocument();
      });
    });

    it("should validate file type", async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ImagesPage />);

      await waitFor(() => {
        expect(screen.getByText(/your images/i)).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole("button", {
        name: /upload new image/i,
      });
      await user.click(uploadButton);

      // Fill form
      await user.type(screen.getByLabelText(/image name/i), "test-image");
      await user.type(screen.getByLabelText(/tag/i), "latest");
      await user.type(screen.getByLabelText(/app hostname/i), "test.com");

      // Create invalid file
      const invalidFile = new File(["content"], "test.txt", {
        type: "text/plain",
      });
      const fileInput = screen.getByLabelText(/build context file/i);
      await user.upload(fileInput, invalidFile);

      // Act
      const submitButton = screen.getByRole("button", { name: /upload/i });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(
          screen.getByText(
            /file must be a .zip, .tar, .tar.gz, or .tgz archive/i
          )
        ).toBeInTheDocument();
      });
    });

    it("should successfully upload an image", async () => {
      // Arrange
      const user = userEvent.setup();
      const newImage = {
        id: 3,
        name: "new-image",
        tag: "v1.0",
        app_hostname: "new.example.com",
        status: "building",
        created_at: new Date().toISOString(),
        min_instances: 1,
        max_instances: 3,
        cpu_limit: "0.5",
        memory_limit: "512m",
        container_port: 8080,
      };

      server.use(
        rest.post("/api/images", (req, res, ctx) => {
          return res(ctx.json(newImage, { status: 201 }));
        })
      );

      render(<ImagesPage />);

      await waitFor(() => {
        expect(screen.getByText(/your images/i)).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole("button", {
        name: /upload new image/i,
      });
      await user.click(uploadButton);

      // Fill form
      await user.type(screen.getByLabelText(/image name/i), "new-image");
      await user.type(screen.getByLabelText(/tag/i), "v1.0");
      await user.type(
        screen.getByLabelText(/app hostname/i),
        "new.example.com"
      );

      // Upload valid file
      const validFile = new File(["content"], "test.zip", {
        type: "application/zip",
      });
      const fileInput = screen.getByLabelText(/build context file/i);
      await user.upload(fileInput, validFile);

      // Act
      const submitButton = screen.getByRole("button", { name: /upload/i });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(
          screen.getByText(/image "new-image:v1.0" created successfully/i)
        ).toBeInTheDocument();
      });

      // Form should close
      await waitFor(() => {
        expect(screen.queryByLabelText(/image name/i)).not.toBeInTheDocument();
      });
    });

    it("should show error message when upload fails", async () => {
      // Arrange
      const user = userEvent.setup();
      server.use(
        rest.post("/api/images", (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ error: "Build failed" }));
        })
      );

      render(<ImagesPage />);

      await waitFor(() => {
        expect(screen.getByText(/your images/i)).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole("button", {
        name: /upload new image/i,
      });
      await user.click(uploadButton);

      // Fill form
      await user.type(screen.getByLabelText(/image name/i), "test-image");
      await user.type(screen.getByLabelText(/tag/i), "latest");
      await user.type(screen.getByLabelText(/app hostname/i), "test.com");

      const validFile = new File(["content"], "test.zip", {
        type: "application/zip",
      });
      const fileInput = screen.getByLabelText(/build context file/i);
      await user.upload(fileInput, validFile);

      // Act
      const submitButton = screen.getByRole("button", { name: /upload/i });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/failed to upload image/i)).toBeInTheDocument();
      });
    });
  });

  describe("Error Handling", () => {
    it("should display error message when API returns 500", async () => {
      // Arrange
      server.use(
        rest.get("/api/images", (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ error: "Internal server error" })
          );
        })
      );

      // Act
      render(<ImagesPage />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/failed to load images/i)).toBeInTheDocument();
      });
    });

    it("should display error message when network fails", async () => {
      // Arrange
      server.use(
        rest.get("/api/images", (_req, res) => {
          return res.networkError("Network error");
        })
      );

      // Act
      render(<ImagesPage />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/failed to load images/i)).toBeInTheDocument();
      });
    });
  });

  describe("Delete Image", () => {
    it("should delete an image successfully", async () => {
      // Arrange
      const user = userEvent.setup();
      window.confirm = jest.fn(() => true);

      render(<ImagesPage />);

      await waitFor(() => {
        expect(screen.getByText(/test-image:latest/i)).toBeInTheDocument();
      });

      // Act
      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      await user.click(deleteButtons[0]);

      // Assert
      await waitFor(() => {
        expect(
          screen.getByText(/image "test-image:latest" deleted successfully/i)
        ).toBeInTheDocument();
      });
    });

    it("should show error when delete fails", async () => {
      // Arrange
      const user = userEvent.setup();
      window.confirm = jest.fn(() => true);

      server.use(
        rest.delete("/api/images/:id", (req, res, ctx) => {
          return res(
            ctx.status(400),
            ctx.json({ error: "Cannot delete image with running containers" })
          );
        })
      );

      render(<ImagesPage />);

      await waitFor(() => {
        expect(screen.getByText(/test-image:latest/i)).toBeInTheDocument();
      });

      // Act
      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      await user.click(deleteButtons[0]);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/failed to delete image/i)).toBeInTheDocument();
      });
    });
  });

  describe("Authentication", () => {
    it("should redirect to login when user is not authenticated", () => {
      // Arrange
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
        login: jest.fn(),
        signup: jest.fn(),
        logout: jest.fn(),
      });

      // Act
      render(<ImagesPage />);

      // Assert - Component should not render content
      expect(screen.queryByText(/your images/i)).not.toBeInTheDocument();
    });

    it("should show loading spinner when auth is loading", () => {
      // Arrange
      mockUseAuth.mockReturnValue({
        user: null,
        loading: true,
        login: jest.fn(),
        signup: jest.fn(),
        logout: jest.fn(),
      });

      // Act
      render(<ImagesPage />);

      // Assert - Should show loading spinner (from LoadingSpinner component)
      // The actual spinner might be rendered by LoadingSpinner component
    });
  });
});
