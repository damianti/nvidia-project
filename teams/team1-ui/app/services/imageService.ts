// Types for image operations
export interface Image {
  id: number
  name: string
  tag: string
  website_url: string
  status: string
  created_at: string
  min_instances: number
  max_instances: number
  cpu_limit: string
  memory_limit: string
}

export interface CreateImageRequest {
  name: string
  tag: string
  website_url: string
  min_instances: number
  max_instances: number
  cpu_limit: string
  memory_limit: string
  user_id: number
}

export interface UpdateImageRequest extends Partial<CreateImageRequest> {}

// Image service class
class ImageService {
  private baseUrl = 'http://localhost:3003/api/images'

  // Helper para obtener headers con token
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('auth-token')
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    }
  }

  // Get all images
  async getImages(): Promise<Image[]> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required')
        }
        const error = await response.json()
        throw new Error(error.detail || error.error || 'Failed to fetch images')
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching images:', error)
      throw error
    }
  }

  // Get single image
  async getImage(id: number): Promise<Image> {
    try {
      const response = await fetch(`${this.baseUrl}/${id}`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required')
        }
        const error = await response.json()
        throw new Error(error.detail || error.error || 'Failed to fetch image')
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching image:', error)
      throw error
    }
  }

  // Create new image
  async createImage(imageData: CreateImageRequest): Promise<Image> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(imageData),
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required')
        }
        const error = await response.json()
        throw new Error(error.detail || error.error || 'Failed to create image')
      }

      return await response.json()
    } catch (error) {
      console.error('Error creating image:', error)
      throw error
    }
  }

  // Update image
  async updateImage(id: number, imageData: UpdateImageRequest): Promise<Image> {
    try {
      const response = await fetch(`${this.baseUrl}/${id}`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(imageData),
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required')
        }
        const error = await response.json()
        throw new Error(error.detail || error.error || 'Failed to update image')
      }

      return await response.json()
    } catch (error) {
      console.error('Error updating image:', error)
      throw error
    }
  }

  // Delete image
  async deleteImage(id: number): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/${id}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required')
        }
        const error = await response.json()
        throw new Error(error.detail || error.error || 'Failed to delete image')
      }
    } catch (error) {
      console.error('Error deleting image:', error)
      throw error
    }
  }
}

// Export singleton instance
export const imageService = new ImageService() 