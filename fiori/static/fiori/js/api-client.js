/**
 * Cliente API para Fiori Launchpad
 * Maneja las peticiones al backend con JWT
 */

class FioriAPIClient {
    constructor() {
        this.baseURL = '/api';
        this.authURL = '/api/auth';
    }
    
    /**
     * Obtiene el access token del localStorage
     */
    getAccessToken() {
        return localStorage.getItem('access_token');
    }
    
    /**
     * Obtiene el refresh token del localStorage
     */
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    }
    
    /**
     * Guarda los tokens en localStorage
     */
    setTokens(accessToken, refreshToken) {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    }
    
    /**
     * Limpia los tokens del localStorage
     */
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    }
    
    /**
     * Refresca el access token usando el refresh token
     */
    async refreshAccessToken() {
        try {
            const refreshToken = this.getRefreshToken();
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }
            
            const response = await fetch(`${this.authURL}/token/refresh/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: refreshToken })
            });
            
            if (!response.ok) {
                throw new Error('Failed to refresh token');
            }
            
            const data = await response.json();
            this.setTokens(data.access, data.refresh || refreshToken);
            
            return data.access;
        } catch (error) {
            console.error('Error refreshing token:', error);
            this.clearTokens();
            window.location.href = '/fiori/login/';
            throw error;
        }
    }
    
    /**
     * Realiza una petición GET
     */
    async get(endpoint, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'GET'
        });
    }
    
    /**
     * Realiza una petición POST
     */
    async post(endpoint, data, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    /**
     * Realiza una petición PUT
     */
    async put(endpoint, data, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    
    /**
     * Realiza una petición PATCH
     */
    async patch(endpoint, data, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }
    
    /**
     * Realiza una petición DELETE
     */
    async delete(endpoint, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'DELETE'
        });
    }
    
    /**
     * Realiza una petición HTTP con manejo automático de autenticación
     */
    async request(endpoint, options = {}) {
        // Asegurar que el endpoint comienza con /
        if (!endpoint.startsWith('/')) {
            endpoint = '/' + endpoint;
        }
        
        // Si el endpoint ya incluye /api, no agregarlo de nuevo
        const url = endpoint.startsWith('/api') ? endpoint : `${this.baseURL}${endpoint}`;
        
        // Headers por defecto
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        // Agregar token si existe
        const token = this.getAccessToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        try {
            let response = await fetch(url, {
                ...options,
                headers
            });
            
            // Si recibimos 401, intentar refrescar el token
            if (response.status === 401 && this.getRefreshToken()) {
                console.log('Token expired, refreshing...');
                await this.refreshAccessToken();
                
                // Reintentar la petición con el nuevo token
                headers['Authorization'] = `Bearer ${this.getAccessToken()}`;
                response = await fetch(url, {
                    ...options,
                    headers
                });
            }
            
            // Si aún es 401, redirigir a login
            if (response.status === 401) {
                this.clearTokens();
                window.location.href = '/fiori/login/';
                throw new Error('Authentication required');
            }
            
            // Parsear respuesta
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || data.error || 'Request failed');
                }
                
                return data;
            }
            
            if (!response.ok) {
                throw new Error(`Request failed with status ${response.status}`);
            }
            
            return response;
            
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }
    
    /**
     * Login
     */
    async login(run, password) {
        try {
            const response = await fetch(`${this.authURL}/token/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ run, password })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }
            
            const data = await response.json();
            
            // Guardar tokens y usuario
            this.setTokens(data.access, data.refresh);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }
    
    /**
     * Logout
     */
    async logout() {
        try {
            // Llamar al endpoint de logout si existe
            await this.post('/usuarios/logout/');
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Siempre limpiar tokens locales
            this.clearTokens();
        }
    }
    
    /**
     * Obtiene información del usuario actual
     */
    getCurrentUser() {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            try {
                return JSON.parse(userStr);
            } catch (e) {
                return null;
            }
        }
        return null;
    }
    
    /**
     * Verifica si el usuario está autenticado
     */
    isAuthenticated() {
        return !!this.getAccessToken();
    }
}

// Crear instancia global
const FioriAPI = new FioriAPIClient();

// Exportar para uso en módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FioriAPI;
}