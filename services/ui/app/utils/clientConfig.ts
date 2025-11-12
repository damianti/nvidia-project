/**
 * Client-side configuration
 * Uses NEXT_PUBLIC_ prefixed environment variables for browser access
 */

function getEnv(key: string, defaultValue: string): string {
  const value = process.env[key]
  if (!value) {
    return defaultValue
  }
  return value
}

function validateUrl(url: string): void {
  try {
    new URL(url)
  } catch {
    throw new Error(`Invalid URL: ${url}`)
  }
}

export const clientConfig = {
  /**
   * API Gateway URL for client-side requests
   * Uses NEXT_PUBLIC_API_GATEWAY_URL or defaults to http://localhost:8080
   */
  apiGatewayUrl: getEnv('NEXT_PUBLIC_API_GATEWAY_URL', 'http://localhost:8080'),

  /**
   * Validate configuration on load
   */
  validate(): void {
    validateUrl(this.apiGatewayUrl)
  }
}

// Validate on import
clientConfig.validate()

