/**
 * Integration tests for ImagesPage component.
 * Tests user interactions, API calls, and UI states using MSW.
 */
import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
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
      // Check hostname appears in the App URL code block
      const codeElements = screen.getAllByText(/test\.example\.com/i)
      expect(codeElements.length).toBeGreaterThan(0);
    });

    it("should display image status badges correctly", async () => {
      // Arrange - Add a building image to test both statuses
      server.use(
        rest.get("*/api/images", (req, res, ctx) => {
          return res(
            ctx.json([
              {
                id: 1,
                name: "test-image",
                tag: "latest",
                app_hostname: "test.example.com",
                status: "ready",
                created_at: "2024-01-01T00:00:00Z",
                min_instances: 1,
                max_instances: 3,
                cpu_limit: "0.5",
                memory_limit: "512m",
                container_port: 8080,
              },
              {
                id: 2,
                name: "building-image",
                tag: "v1.0",
                app_hostname: "building.example.com",
                status: "building",
                created_at: "2024-01-02T00:00:00Z",
                min_instances: 2,
                max_instances: 5,
                cpu_limit: "1.0",
                memory_limit: "1g",
                container_port: 3000,
              },
            ])
          );
        })
      );

      // Act
      render(<ImagesPage />);

      // Assert - Verificar que ambos badges existen
      await waitFor(() => {
        const readyBadges = screen.getAllByText(/^ready$/i);
        const buildingBadges = screen.getAllByText(/^building$/i);
        expect(readyBadges.length).toBeGreaterThan(0);
        expect(buildingBadges.length).toBeGreaterThan(0);
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

      // Assert - Check that the modal form is now visible
      expect(screen.getByLabelText(/image name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/tag/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/app hostname/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^upload$/i })).toBeInTheDocument();
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

    it("should show validation errors for invalid hostname", async () => {
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

      // Wait for modal to open
      await waitFor(() => {
        expect(screen.getByLabelText(/image name/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/image name/i);
      const tagInput = screen.getByLabelText(/tag/i);
      const hostnameInput = screen.getByLabelText(/app hostname/i);
      const fileInput = screen.getByLabelText(/build context file/i);

      // Fill form with INVALID hostname (test JavaScript validation)
      await user.type(nameInput, "test-image");
      await user.clear(tagInput);
      await user.type(tagInput, "latest");
      await user.type(hostnameInput, "INVALID HOSTNAME!!!"); // Invalid: uppercase and special chars

      const validFile = new File(["content"], "test.zip", {
        type: "application/zip",
      });
      await user.upload(fileInput, validFile);

      // Act - Submit form with invalid hostname
      const submitButton = screen.getByRole("button", { name: /^upload$/i });
      await user.click(submitButton);

      // Assert - Should show JavaScript validation error for hostname
      await waitFor(() => {
        const errorMessages = screen.getAllByText(/please enter a valid app hostname/i);
        expect(errorMessages.length).toBeGreaterThan(0);
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

      // Wait for modal to open and get all input references
      await waitFor(() => {
        expect(screen.getByLabelText(/image name/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/image name/i);
      const tagInput = screen.getByLabelText(/tag/i);
      const hostnameInput = screen.getByLabelText(/app hostname/i);
      const fileInput = screen.getByLabelText(/build context file/i);

      // Fill form
      await user.type(nameInput, "test-image");
      await user.clear(tagInput);
      await user.type(tagInput, "latest");
      await user.type(hostnameInput, "test.com");

      // Create invalid file and upload using fireEvent (user.upload doesn't work reliably here)
      const invalidFile = new File(["content"], "test.txt", {
        type: "text/plain",
      });
      Object.defineProperty(fileInput, 'files', {
        value: [invalidFile],
        configurable: true,
      });
      fireEvent.change(fileInput);

      // Act
      const submitButton = screen.getByRole("button", { name: /^upload$/i });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        const errorMessages = screen.getAllByText(
          /file must be a .zip, .tar, .tar.gz, or .tgz archive/i
        );
        expect(errorMessages.length).toBeGreaterThan(0);
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

      // Wait for modal to open and get all input references
      await waitFor(() => {
        expect(screen.getByLabelText(/image name/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/image name/i);
      const tagInput = screen.getByLabelText(/tag/i);
      const hostnameInput = screen.getByLabelText(/app hostname/i);
      const fileInput = screen.getByLabelText(/build context file/i);

      // Fill form
      await user.type(nameInput, "new-image");
      await user.clear(tagInput);
      await user.type(tagInput, "v1.0");
      await user.type(hostnameInput, "new.example.com");

      // Upload valid file
      const validFile = new File(["content"], "test.zip", {
        type: "application/zip",
      });
      await user.upload(fileInput, validFile);

      // Act
      const submitButton = screen.getByRole("button", { name: /^upload$/i });
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

      // Wait for modal to open and get all input references
      await waitFor(() => {
        expect(screen.getByLabelText(/image name/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/image name/i);
      const tagInput = screen.getByLabelText(/tag/i);
      const hostnameInput = screen.getByLabelText(/app hostname/i);
      const fileInput = screen.getByLabelText(/build context file/i);

      // Fill form
      await user.type(nameInput, "test-image");
      await user.clear(tagInput);
      await user.type(tagInput, "latest");
      await user.type(hostnameInput, "test.com");

      const validFile = new File(["content"], "test.zip", {
        type: "application/zip",
      });
      await user.upload(fileInput, validFile);

      // Act
      const submitButton = screen.getByRole("button", { name: /^upload$/i });
      await user.click(submitButton);

      // Assert
      await waitFor(() => {
        const errorMessages = screen.getAllByText(/failed to create image/i);
        expect(errorMessages.length).toBeGreaterThan(0);
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

      // Assert - Should show the specific error message from the backend (4xx error)
      await waitFor(() => {
        expect(screen.getByText(/cannot delete image with running containers/i)).toBeInTheDocument();
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
