// Types for image operations
export interface Image {
  id: number
  name: string
  tag: string
  app_hostname: string
  status: string
  created_at: string
  min_instances: number
  max_instances: number
  cpu_limit: string
  memory_limit: string
  container_port?: number
  build_logs_?: string
  source_path?: string
}

export interface CreateImageRequest {
  name: string
  tag: string
  app_hostname: string
  container_port?: number
  min_instances: number
  max_instances: number
  cpu_limit: string
  memory_limit: string
  user_id: number
  file: File
}

export interface UpdateImageRequest extends Partial<CreateImageRequest> {}

// Image service class
class ImageService {
  private baseUrl = '/api/images'

  // Helper para obtener headers
  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
    }
  }

  // Helper para manejar errores de respuesta
  private async handleErrorResponse(response: Response, defaultMessage: string): Promise<never> {
    // Errores específicos que siempre se manejan igual
    if (response.status === 401) {
      throw new Error('Authentication required')
    }

    // Para 4xx (errores del cliente): usar mensaje del backend
    if (response.status >= 400 && response.status < 500) {
      try {
        const error = await response.json()
        throw new Error(error.detail || error.error || defaultMessage)
      } catch (e) {
        if (e instanceof Error && e.message !== defaultMessage) throw e
        throw new Error(defaultMessage)
      }
    }

    // Para 5xx (errores del servidor): mensaje genérico + log detallado
    if (response.status >= 500) {
      try {
        const error = await response.json()
        console.error(`Server error (${response.status}):`, error)
      } catch {
        console.error(`Server error: ${response.status} ${response.statusText}`)
      }
      throw new Error(defaultMessage)
    }

    throw new Error(defaultMessage)
  }

  // Get all images
  async getImages(): Promise<Image[]> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include', // Include cookies
      })

      if (!response.ok) {
        await this.handleErrorResponse(response, 'Failed to fetch images')
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
        headers: this.getHeaders(),
        credentials: 'include',
      })

      if (!response.ok) {
        await this.handleErrorResponse(response, 'Failed to fetch image')
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching image:', error)
      throw error
    }
  }

  async getBuildLogs(id: number): Promise<string>{
    try {
      const response = await fetch (`${this.baseUrl}/${id}/build-logs`,{
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      })
      
      if (!response.ok){
        await this.handleErrorResponse(response, 'Failed to fetch build logs')
      }

      const data = await response.json()
      return data.build_logs || ''
    } catch (error){
      console.error('Error fetching build logs:', error)
      throw error
    }
  }

  // Create new image
  async createImage(imageData: CreateImageRequest): Promise<Image> {
    try {
      const formData = new FormData()

      formData.append('name', imageData.name)
      formData.append('tag', imageData.tag)
      formData.append('app_hostname', imageData.app_hostname)
      formData.append('container_port', String(imageData.container_port))
      formData.append('min_instances', String(imageData.min_instances))
      formData.append('max_instances', String(imageData.max_instances))
      formData.append('cpu_limit', imageData.cpu_limit)
      formData.append('memory_limit', imageData.memory_limit)
      formData.append('file', imageData.file)

      const response = await fetch(this.baseUrl, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })

      if (!response.ok) {
        await this.handleErrorResponse(response, 'Failed to create image')
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
        headers: this.getHeaders(),
        credentials: 'include',
        body: JSON.stringify(imageData),
      })

      if (!response.ok) {
        await this.handleErrorResponse(response, 'Failed to update image')
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
        headers: this.getHeaders(),
        credentials: 'include',
      })

      if (!response.ok) {
        await this.handleErrorResponse(response, 'Failed to delete image')
      }
    } catch (error) {
      console.error('Error deleting image:', error)
      throw error
    }
  }
}

// Export singleton instance
export const imageService = new ImageService() 