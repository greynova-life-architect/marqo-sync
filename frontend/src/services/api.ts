import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 5000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      console.error('API request timeout:', error.config?.url)
    } else if (error.response) {
      console.error('API error response:', error.response.status, error.response.data)
    } else if (error.request) {
      console.error('API request failed - no response:', error.request)
    } else {
      console.error('API error:', error.message)
    }
    return Promise.reject(error)
  }
)

export interface StatusResponse {
  status: string
  indexers: Record<string, any>
  watchers: Record<string, any>
}

export interface ConfigResponse {
  marqo_url: string
  max_file_size_bytes: number
  store_large_files_metadata_only: boolean
  indexers: any[]
}

export interface IndexResponse {
  indexes: Array<{
    name: string
    type: string
    document_count: number
    size: number
    settings?: any
    error?: string
  }>
}

export interface PathValidationResponse {
  valid: boolean
  exists: boolean
  is_directory: boolean
  readable: boolean
  error?: string
}

export const apiService = {
  getStatus: () => api.get<StatusResponse>('/status'),
  getConfig: () => api.get<ConfigResponse>('/config'),
  updateConfig: (data: any) => api.post('/config', data),
  getIndexes: () => api.get<IndexResponse>('/indexes'),
  getIndexers: () => api.get('/indexers'),
  getWatchers: () => api.get('/watchers'),
  validatePath: (path: string) => api.post<PathValidationResponse>('/validate-path', { path }),
  testConnection: (url: string) => api.post('/test-connection', { url }),
  getIndexStats: (indexName: string) => api.get(`/index-stats/${indexName}`),
  getProfiles: (params?: any) => api.get('/profiles', { params }),
  createProfile: (data: any) => api.post('/profiles', data),
  getProfile: (id: string) => api.get(`/profiles/${id}`),
  updateProfile: (id: string, data: any) => api.put(`/profiles/${id}`, data),
  createAgent: (data: any) => api.post('/agents', data),
  getConversations: (params?: any) => api.get('/conversations', { params }),
  createConversation: (data: any) => api.post('/conversations', data),
  getConversation: (id: string) => api.get(`/conversations/${id}`),
  addMessage: (id: string, data: any) => api.post(`/conversations/${id}/messages`, data),
  getMemories: (params?: any) => api.get('/memories', { params }),
  storeMemory: (data: any) => api.post('/memories', data),
  getCategories: (params?: any) => api.get('/categories', { params }),
  getCategoryTree: (params?: any) => api.get('/categories/tree', { params }),
}

