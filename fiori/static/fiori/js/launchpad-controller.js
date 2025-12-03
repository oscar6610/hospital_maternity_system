/**
 * Controlador del Fiori Launchpad
 * Gestiona la carga y personalización de aplicaciones
 */

export class FioriLaunchpad {
    constructor() {
        this.apps = [];
        this.userConfig = {};
        this.preferences = {};
        this.viewMode = 'grid';
    }
    
    async init() {
        try {
            await this.loadApps();
            await this.loadUserConfig();
            await this.loadPreferences();
            this.render();
        } catch (error) {
            console.error('Error al inicializar Launchpad:', error);
            this.showError('No se pudo cargar el Launchpad');
        }
    }
    
    async loadApps() {
        try {
            const response = await fetch('/api/fiori/apps/', {
                headers: {
                    'Authorization': `Bearer ${this.getAccessToken()}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Error al cargar aplicaciones');
            
            const data = await response.json();
            this.apps = data.results || data;
        } catch (error) {
            console.error('Error al cargar apps:', error);
            throw error;
        }
    }
    
    async loadUserConfig() {
        try {
            const response = await fetch('/api/fiori/user-apps/', {
                headers: {
                    'Authorization': `Bearer ${this.getAccessToken()}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Error al cargar configuración');
            
            const data = await response.json();
            this.userConfig = data.reduce((acc, config) => {
                acc[config.app.id_app] = config;
                return acc;
            }, {});
        } catch (error) {
            console.error('Error al cargar config:', error);
            this.userConfig = {};
        }
    }
    
    async loadPreferences() {
        try {
            const response = await fetch('/api/fiori/preferences/', {
                headers: {
                    'Authorization': `Bearer ${this.getAccessToken()}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                this.preferences = await response.json();
            }
        } catch (error) {
            console.error('Error al cargar preferencias:', error);
            this.preferences = {
                group_by_category: true,
                compact_mode: false,
                show_recent_apps: true,
                recent_apps_count: 5
            };
        }
    }
    
    render() {
        this.renderRecentApps();
        if (this.preferences.group_by_category) {
            this.renderAppsByCategory();
        } else {
            this.renderAllApps();
        }
        this.renderFavoriteApps();
    }
    
    renderRecentApps() {
        if (!this.preferences.show_recent_apps) {
            document.getElementById('recent-apps-section').style.display = 'none';
            return;
        }
        
        const container = document.getElementById('recent-apps-tiles');
        container.innerHTML = '';
        
        // Filtrar y ordenar apps recientes
        const recentApps = this.apps
            .filter(app => {
                const config = this.userConfig[app.id_app];
                return config && config.last_accessed;
            })
            .sort((a, b) => {
                const configA = this.userConfig[a.id_app];
                const configB = this.userConfig[b.id_app];
                return new Date(configB.last_accessed) - new Date(configA.last_accessed);
            })
            .slice(0, this.preferences.recent_apps_count);
        
        recentApps.forEach(app => {
            container.appendChild(this.createTile(app));
        });
    }
    
    renderAppsByCategory() {
        const container = document.getElementById('apps-by-category');
        container.innerHTML = '';
        
        // Agrupar apps por categoría
        const categories = {};
        this.apps.forEach(app => {
            const config = this.userConfig[app.id_app];
            if (!config || !config.is_visible) return;
            
            const categoryName = app.category?.name || 'Sin categoría';
            if (!categories[categoryName]) {
                categories[categoryName] = [];
            }
            categories[categoryName].push(app);
        });
        
        // Renderizar cada categoría
        Object.entries(categories).forEach(([categoryName, apps]) => {
            const section = document.createElement('div');
            section.className = 'flp-section';
            
            const title = document.createElement('ui5-title');
            title.level = 'H4';
            title.className = 'section-title';
            title.innerHTML = `
                <ui5-icon name="${apps[0].category?.icon || 'folder'}" style="margin-right: 10px;"></ui5-icon>
                ${categoryName}
            `;
            
            const tilesContainer = document.createElement('div');
            tilesContainer.className = 'flp-tiles-container';
            
            // Ordenar apps por custom_order
            apps.sort((a, b) => {
                const orderA = this.userConfig[a.id_app]?.custom_order || a.default_order;
                const orderB = this.userConfig[b.id_app]?.custom_order || b.default_order;
                return orderA - orderB;
            });
            
            apps.forEach(app => {
                tilesContainer.appendChild(this.createTile(app));
            });
            
            section.appendChild(title);
            section.appendChild(tilesContainer);
            container.appendChild(section);
        });
    }
    
    renderAllApps() {
        const container = document.getElementById('apps-by-category');
        container.innerHTML = '';
        
        const section = document.createElement('div');
        section.className = 'flp-section';
        
        const title = document.createElement('ui5-title');
        title.level = 'H4';
        title.className = 'section-title';
        title.textContent = 'Todas las Aplicaciones';
        
        const tilesContainer = document.createElement('div');
        tilesContainer.className = 'flp-tiles-container';
        
        const visibleApps = this.apps.filter(app => {
            const config = this.userConfig[app.id_app];
            return !config || config.is_visible;
        });
        
        visibleApps.forEach(app => {
            tilesContainer.appendChild(this.createTile(app));
        });
        
        section.appendChild(title);
        section.appendChild(tilesContainer);
        container.appendChild(section);
    }
    
    renderFavoriteApps() {
        const container = document.getElementById('favorite-apps-tiles');
        container.innerHTML = '';
        
        const favoriteApps = this.apps.filter(app => {
            const config = this.userConfig[app.id_app];
            return config && config.is_favorite;
        });
        
        if (favoriteApps.length === 0) {
            document.getElementById('favorite-apps-section').style.display = 'none';
            return;
        }
        
        favoriteApps.forEach(app => {
            container.appendChild(this.createTile(app, true));
        });
    }
    
    createTile(app, showFavorite = false) {
        const tile = document.createElement('ui5-card');
        tile.className = 'flp-tile';
        tile.setAttribute('accessible-name', app.title);
        
        const config = this.userConfig[app.id_app];
        const isFavorite = config?.is_favorite || false;
        
        tile.innerHTML = `
            <div class="tile-header" style="background-color: var(--sap${app.background_color || 'Accent6'});">
                <ui5-icon name="${app.icon}" style="font-size: 2.5rem; color: white;"></ui5-icon>
            </div>
            <div class="tile-content">
                <ui5-title level="H5">${app.title}</ui5-title>
                <ui5-label class="tile-subtitle">${app.subtitle || ''}</ui5-label>
                ${config?.access_count ? `
                    <div class="tile-info">
                        <ui5-badge color-scheme="8">${config.access_count} accesos</ui5-badge>
                    </div>
                ` : ''}
            </div>
            <div class="tile-actions">
                <ui5-button 
                    icon="${isFavorite ? 'favorite' : 'unfavorite'}" 
                    design="Transparent"
                    class="favorite-btn"
                    data-app-id="${app.id_app}"
                    title="${isFavorite ? 'Quitar de favoritos' : 'Agregar a favoritos'}">
                </ui5-button>
            </div>
        `;
        
        // Event: Click en tile para navegar
        tile.addEventListener('click', (e) => {
            if (!e.target.closest('.favorite-btn')) {
                this.navigateToApp(app);
            }
        });
        
        // Event: Toggle favorito
        const favBtn = tile.querySelector('.favorite-btn');
        favBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            await this.toggleFavorite(app.id_app);
        });
        
        return tile;
    }
    
    async navigateToApp(app) {
        try {
            // Registrar acceso
            await fetch(`/api/fiori/apps/${app.id_app}/access/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAccessToken()}`,
                    'Content-Type': 'application/json'
                }
            });
            
            // Navegar
            window.location.href = app.url_path;
        } catch (error) {
            console.error('Error al navegar:', error);
        }
    }
    
    async toggleFavorite(appId) {
        try {
            const config = this.userConfig[appId] || {};
            const newFavoriteState = !config.is_favorite;
            
            const response = await fetch(`/api/fiori/user-apps/${appId}/`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${this.getAccessToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_favorite: newFavoriteState })
            });
            
            if (!response.ok) throw new Error('Error al actualizar favorito');
            
            // Actualizar estado local
            if (!this.userConfig[appId]) {
                this.userConfig[appId] = {};
            }
            this.userConfig[appId].is_favorite = newFavoriteState;
            
            // Re-renderizar
            this.render();
            
            this.showSuccess(`App ${newFavoriteState ? 'agregada a' : 'removida de'} favoritas`);
        } catch (error) {
            console.error('Error al toggle favorito:', error);
            this.showError('No se pudo actualizar favorito');
        }
    }
    
    openPersonalizeDialog() {
        const dialog = document.getElementById('personalize-dialog');
        const list = document.getElementById('apps-selector-list');
        list.innerHTML = '';
        
        this.apps.forEach(app => {
            const config = this.userConfig[app.id_app];
            const isVisible = !config || config.is_visible;
            
            const item = document.createElement('ui5-li');
            item.setAttribute('data-app-id', app.id_app);
            if (isVisible) {
                item.setAttribute('selected', '');
            }
            item.innerHTML = `
                <ui5-icon name="${app.icon}" slot="icon"></ui5-icon>
                ${app.title}
            `;
            list.appendChild(item);
        });
        
        // Cargar preferencias actuales
        document.getElementById('group-by-category-switch').checked = this.preferences.group_by_category;
        document.getElementById('compact-mode-switch').checked = this.preferences.compact_mode;
        
        dialog.show();
    }
    
    async savePersonalization() {
        try {
            // Guardar visibilidad de apps
            const list = document.getElementById('apps-selector-list');
            const selectedItems = list.querySelectorAll('ui5-li[selected]');
            const visibleAppIds = Array.from(selectedItems).map(item => item.getAttribute('data-app-id'));
            
            const updates = this.apps.map(app => ({
                app_id: app.id_app,
                is_visible: visibleAppIds.includes(String(app.id_app))
            }));
            
            await fetch('/api/fiori/user-apps/bulk-update/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAccessToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ apps: updates })
            });
            
            // Guardar preferencias
            const preferences = {
                group_by_category: document.getElementById('group-by-category-switch').checked,
                compact_mode: document.getElementById('compact-mode-switch').checked
            };
            
            await fetch('/api/fiori/preferences/', {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${this.getAccessToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(preferences)
            });
            
            // Recargar y re-renderizar
            await this.loadUserConfig();
            await this.loadPreferences();
            this.render();
            
            document.getElementById('personalize-dialog').close();
            this.showSuccess('Personalización guardada correctamente');
        } catch (error) {
            console.error('Error al guardar personalización:', error);
            this.showError('No se pudo guardar la personalización');
        }
    }
    
    setViewMode(mode) {
        this.viewMode = mode;
        document.body.setAttribute('data-view-mode', mode);
        // Implementar cambio de vista si es necesario
    }
    
    getAccessToken() {
        return localStorage.getItem('access_token');
    }
    
    showSuccess(message) {
        // Implementar toast de éxito
        console.log('✓', message);
    }
    
    showError(message) {
        // Implementar toast de error
        console.error('✗', message);
    }
}