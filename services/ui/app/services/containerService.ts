import { Image } from './imageService'

export interface ImageWithContainers extends Image {
    containers: Container[]
}
export interface Container {
    id: number
    container_id: string
    name: string
    port: number
    status: string
    cpu_usage: string
    memory_usage: string
    created_at: string
    image_id: number
    image: Image
}


class ContainerService {

    private baseUrl = '/api/containers'

    private getHeaders(): HeadersInit {
        return {
          'Content-Type': 'application/json',
        }
      }

    async getContainers(): Promise<Container[]> {
        try{
            const response = await fetch(this.baseUrl, {
                method: 'GET',
                headers: this.getHeaders(),
                credentials: 'include',
            })

            if (!response.ok){
                if (response.status === 401){
                    throw new Error('Authentication required')
                }
                const error = await response.json()
                throw new Error(error.detail || error.error || 'failed to fetch containers')
            }
            return await response.json()
        }
        catch (error){
            console.error('Error fetching containers: ', error)
            throw error
        }
    }
    async getImagesWithContainers(): Promise<ImageWithContainers[]> {
        try {
            const response = await fetch('/api/images/with-containers', {
                method: 'GET',
                headers: this.getHeaders(),
                credentials: 'include',
            })
            if (!response.ok){
                if (response.status == 401) {
                    throw new Error ('Authentication required')
                }
                const error = await response.json()
                throw new Error (error.detail || error.error || 'Failed to fetch images with containers')
            }
            return await response.json()
        }
        catch (error){
            throw error
        }
    }

    async createContainer(imageId: number, containerName?: string, count: number = 1): Promise<Container[]> {
        try {
            const response = await fetch (`/api/containers/${imageId}`, {
                method: 'POST',
                headers: this.getHeaders(),
                credentials: 'include',
                body: JSON.stringify({
                    name: containerName || `container-${Date.now()}`,
                    image_id: imageId,
                    count: count
                })
            })
            if (!response.ok){
                if (response.status == 401){
                    throw new Error ('Authentication required');
                }
                let errorMessage = 'Failed to create container'
                try {
                    const error = await response.json();
                    errorMessage = error.detail || error.error || errorMessage
                } catch {
                    // If response is not JSON, use status text
                    errorMessage = `HTTP ${response.status}: ${response.statusText || errorMessage}`
                }
                throw new Error(errorMessage)
            }
            return response.json()
        }
        catch (error){
            throw error;
        }
    }

    async startContainer(containerId: number): Promise<Container>{
        try {
            const response = await fetch (`${this.baseUrl}/${containerId}/start`, {
                method: 'POST',
                headers: this.getHeaders(),
                credentials: 'include',
            })
            if (!response.ok){
                
                if (response.status == 401){
                    throw new Error ('Authentication required');
                }
                const error = await response.json();
                throw new Error (error.detail || error.error || 'Failed to start container');
            } 
            return response.json()
        }
        catch (error){
            throw error;
        }
    }
    async stopContainer (containerId: number): Promise<Container> {
        try {
            const response = await fetch (`${this.baseUrl}/${containerId}/stop`,{
                method: 'POST',
                headers: this.getHeaders(),
                credentials: 'include',
            })
            if (!response.ok){
                if (response.status == 401){
                    throw new Error ('Authentication required');
                }
                const error = await response.json();
                throw new Error (error.detail || error.error || 'Failed to stop container')
            }
            return response.json()
        }
        catch (error){
            throw error
        }
    }
    async deleteContainer (containerId: number): Promise< {message:string} > {
        try {
            const response = await fetch (`${this.baseUrl}/${containerId}`,{
                method: 'DELETE',
                headers: this.getHeaders(),
                credentials: 'include',
            })
            if (!response.ok){
                if (response.status == 401){
                    throw new Error ('Authentication required');
                }
                const error = await response.json();
                throw new Error (error.detail || error.error || 'Failed to delete container')
            }
            return response.json()
        }
        catch (error){
            throw error
        }
    }

}

export const containerService = new ContainerService()