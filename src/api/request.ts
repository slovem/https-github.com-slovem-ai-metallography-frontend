import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

class Request {
  private instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL: 'http://localhost:3001/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  private setupInterceptors(): void {
    // 请求拦截器 - 添加 Token
    this.instance.interceptors.request.use(
      (config) => {
        const authStore = useAuthStore()
        const token = authStore.token || localStorage.getItem('token')
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        } else {
          console.warn('⚠️ 没有找到 Token')
        }
        
        console.log('📤 请求:', config.method?.toUpperCase(), config.url, 'Token:', !!token)
        return config
      },
      (error) => Promise.reject(error)
    )

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response) => {
        const { data } = response
        if (data.code === 0) {
          return data.data
        }
        if (data.code !== 0 && data.code !== 200) {
          message.error(data.message || '请求失败')
          return Promise.reject(response)
        }
        return data
      },
      (error) => {
        if (error.response) {
          const { status, data } = error.response
          if (status === 401) {
            const authStore = useAuthStore()
            authStore.logout()
            message.error('登录已过期，请重新登录')
            router.push('/auth/login')
          } else if (status === 403) {
            message.error('没有权限执行此操作')
          } else if (data?.message) {
            message.error(data.message)
          } else {
            message.error('请求失败，请稍后重试')
          }
        } else if (error.code === 'ECONNABORTED') {
          message.error('请求超时，请检查网络连接')
        } else {
          message.error('网络错误，请检查网络连接')
        }
        return Promise.reject(error)
      }
    )
  }

  public get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.get(url, config)
  }

  public post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.post(url, data, config)
  }

  public put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.put(url, data, config)
  }

  public delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.delete(url, config)
  }

  public upload<T = any>(url: string, formData: FormData, onProgress?: (percent: number) => void): Promise<T> {
    return this.instance.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      }
    })
  }
}

export const request = new Request()
export default request