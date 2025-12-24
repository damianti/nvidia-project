# UI Service

Next.js web dashboard for managing images, containers, authentication, and billing.

## Overview

The UI service provides a modern web interface for:
- User authentication (login/signup)
- Image management (upload, view, delete)
- Container management (create, start, stop, delete)
- Billing visualization (costs and usage)
- Real-time updates and status monitoring

## Features

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Modern styling
- **Authentication**: JWT-based with HttpOnly cookies
- **API Integration**: Communicates with API Gateway

## Pages

- `/login` - User authentication
- `/signup` - User registration
- `/dashboard` - Main dashboard
- `/images` - Image management
- `/containers` - Container management
- `/billing` - Billing and cost tracking

## Development

```bash
npm install
npm run dev
```

## Configuration

- Port: `3000`
- API Gateway: `http://localhost:8080`
- Environment: Development and production builds

## Dependencies

- API Gateway: For all backend API calls
- Next.js: React framework
- TypeScript: Type safety

## Testing

This project uses a comprehensive testing setup with Jest, React Testing Library, and MSW (Mock Service Worker) for API mocking.

### Test Structure

```
app/
  __tests__/
    components/        # Component integration tests
    services/          # Service unit tests
    mocks/             # MSW handlers and server setup
    helpers/           # Test utilities
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage report
npm run test:coverage

# Run tests in CI mode (no watch, with coverage)
npm run test:ci
```

### Writing Tests

#### Service Tests (Unit Tests)

Service tests mock HTTP requests using MSW. Example:

```typescript
import { imageService } from '@/services/imageService'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'

describe('ImageService', () => {
  it('should fetch images successfully', async () => {
    const images = await imageService.getImages()
    expect(images).toHaveLength(2)
  })

  it('should handle errors', async () => {
    server.use(
      http.get('/api/images', () => {
        return HttpResponse.json(
          { error: 'Server error' },
          { status: 500 }
        )
      })
    )
    await expect(imageService.getImages()).rejects.toThrow()
  })
})
```

#### Component Tests (Integration Tests)

Component tests use React Testing Library and MSW to test user interactions:

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ImagesPage from '@/images/page'
import { server } from '../mocks/server'

describe('ImagesPage', () => {
  it('should render images list', async () => {
    render(<ImagesPage />)
    await waitFor(() => {
      expect(screen.getByText(/your images/i)).toBeInTheDocument()
    })
  })

  it('should handle form submission', async () => {
    const user = userEvent.setup()
    render(<ImagesPage />)
    
    const uploadButton = screen.getByRole('button', { name: /upload/i })
    await user.click(uploadButton)
    
    // Fill form and submit...
  })
})
```

### Mocking Strategy

- **MSW (Mock Service Worker)**: Used for mocking HTTP requests at the network level
- **Handlers**: Defined in `app/__tests__/mocks/handlers.ts`
- **Server**: Configured in `app/__tests__/mocks/server.ts`
- **Setup**: MSW is initialized in `jest.setup.js`

### Test Best Practices

1. **Use role-based queries**: Prefer `getByRole`, `getByLabelText` over `getByTestId`
2. **Test user behavior**: Focus on what users see and do, not implementation details
3. **Wait for async updates**: Use `waitFor` and `findBy*` queries for async content
4. **Mock at boundaries**: Mock HTTP calls, not internal functions
5. **Keep tests isolated**: Each test should be independent and not rely on others

### Adding New Tests

1. **For a new service**: Create `app/__tests__/services/[serviceName].test.ts`
2. **For a new component**: Create `app/__tests__/components/[ComponentName].test.tsx`
3. **For new API endpoints**: Add handlers to `app/__tests__/mocks/handlers.ts`

### Coverage Goals

- **Minimum coverage**: 80% for branches, functions, lines, and statements
- **Focus areas**: Services, components, and critical user flows
- **Excluded**: Layout files, page files (tested via E2E if needed)

### Troubleshooting

- **Tests failing with "Cannot find module"**: Ensure path aliases in `tsconfig.json` match `jest.config.js`
- **MSW not intercepting requests**: Check that `server.listen()` is called in `jest.setup.js`
- **Async tests timing out**: Use `waitFor` or increase timeout for slow operations
