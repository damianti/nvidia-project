// Types for image operations
export interface Image {
  id: number
  name: string
  tag: string
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
  min_instances: number
  max_instances: number
  cpu_limit: string
  memory_limit: string
}

export interface UpdateImageRequest extends Partial<CreateImageRequest> {}

// Image service class
class ImageService {
  private baseUrl = '/api/images'

  // Get all images
  async getImages(): Promise<Image[]> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to fetch images')
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
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to fetch image')
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
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(imageData),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to create image')
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
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(imageData),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to update image')
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
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to delete image')
      }
    } catch (error) {
      console.error('Error deleting image:', error)
      throw error
    }
  }
}

// Export singleton instance
export const imageService = new ImageService() 