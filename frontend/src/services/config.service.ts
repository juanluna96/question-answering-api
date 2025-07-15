import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

/**
 * Servicio de configuración para las peticiones HTTP
 * Centraliza la configuración de Axios y maneja la URL base desde variables de entorno
 */
export class ConfigService {
  private axiosInstance: AxiosInstance;
  private readonly baseURL: string;

  constructor() {
    // Obtener la URL base desde las variables de entorno
    this.baseURL = process.env.NEXT_PUBLIC_API_BACKEND_URL || 'http://localhost:8000';
    
    // Crear instancia de Axios con configuración base
    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 segundos de timeout
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Configurar interceptores
    this.setupInterceptors();
  }

  /**
   * Configurar interceptores para requests y responses
   */
  private setupInterceptors(): void {
    // Interceptor para requests
    this.axiosInstance.interceptors.request.use(
      (config) => {
        // Agregar timestamp a los requests para debugging
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url} at ${new Date().toISOString()}`);
        return config;
      },
      (error) => {
        console.error('[API Request Error]', error);
        return Promise.reject(error);
      }
    );

    // Interceptor para responses
    this.axiosInstance.interceptors.response.use(
      (response) => {
        console.log(`[API Response] ${response.status} ${response.config.url} at ${new Date().toISOString()}`);
        return response;
      },
      (error) => {
        console.error('[API Response Error]', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          url: error.config?.url,
          data: error.response?.data
        });
        return Promise.reject(error);
      }
    );
  }

  /**
   * Realizar petición GET
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.get<T>(url, config);
  }

  /**
   * Realizar petición POST
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.post<T>(url, data, config);
  }

  /**
   * Realizar petición PUT
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.put<T>(url, data, config);
  }

  /**
   * Realizar petición DELETE
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.delete<T>(url, config);
  }

  /**
   * Realizar petición PATCH
   */
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.axiosInstance.patch<T>(url, data, config);
  }

  /**
   * Obtener la URL base configurada
   */
  getBaseURL(): string {
    return this.baseURL;
  }

  /**
   * Obtener la instancia de Axios (para casos especiales)
   */
  getAxiosInstance(): AxiosInstance {
    return this.axiosInstance;
  }

  /**
   * Actualizar headers por defecto
   */
  setDefaultHeader(key: string, value: string): void {
    this.axiosInstance.defaults.headers.common[key] = value;
  }

  /**
   * Remover header por defecto
   */
  removeDefaultHeader(key: string): void {
    delete this.axiosInstance.defaults.headers.common[key];
  }
}

// Instancia singleton del servicio de configuración
export const configService = new ConfigService();

// Export por defecto
export default ConfigService;