/**
 * Controlador de la App Fiori de Madres
 */

export class FioriMadresApp {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 20;
        this.totalPages = 1;
        this.filters = {};
        this.madres = [];
    }
    
    async init() {
        console.log('Inicializando Fiori Madres App...');
        await this.loadNacionalidades();
        await this.loadMadres();
    }
    
    async loadNacionalidades() {
        try {
            const response = await fetch('/api/catalogs/nacionalidades/', {
                headers: {
                    'Authorization': `Bearer ${this.getAccessToken()}`
                }
            });
            
            if (!response.ok) throw new Error('Error al cargar nacionalidades');
            
            const data = await response.json();
            const select = document.getElementById('filter-nacionalidad');
            
            if (select) {
                data.forEach(nac => {
                    const option = document.createElement('ui5-option');
                    option.value = nac.id_nacionalidad;
                    option.textContent = nac.nombre;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error cargando nacionalidades:', error);
        }
    }
    
    async loadMadres() {
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) loadingIndicator.active = true;
        
        try {
            // Construir URL con filtros y paginación
            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.pageSize,
                ...this.filters
            });
            
            const response = await fetch(`/api/maternity/madres/?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAccessToken()}`
                }
            });
            
            if (!response.ok) throw new Error('Error al cargar madres');
            
            const data = await response.json();
            this.madres = data.results;
            this.totalPages = Math.ceil(data.count / this.pageSize);
            
            this.renderTable();
            this.updatePagination();
        } catch (error) {
            console.error('Error cargando madres:', error);
            this.showError('No se pudieron cargar las madres');
        } finally {
            if (loadingIndicator) loadingIndicator.active = false;
        }
    }
    
    renderTable() {
        const table = document.getElementById('madres-table');
        if (!table) return;
        
        // Limpiar filas existentes
        table.querySelectorAll('ui5-table-row').forEach(row => row.remove());
        
        // Agregar filas
        this.madres.forEach(madre => {
            const row = document.createElement('ui5-table-row');
            row.innerHTML = `
                <ui5-table-cell>${madre.run}</ui5-table-cell>
                <ui5-table-cell>${madre.nombre_completo || `${madre.nombre} ${madre.apellido_paterno} ${madre.apellido_materno}`}</ui5-table-cell>
                <ui5-table-cell>${madre.edad || 'N/A'}</ui5-table-cell>
                <ui5-table-cell>${madre.nacionalidad_nombre || 'N/A'}</ui5-table-cell>
                <ui5-table-cell>${new Date(madre.fecha_registro).toLocaleDateString()}</ui5-table-cell>
                <ui5-table-cell>
                    <ui5-button icon="display" design="Transparent" 
                                data-id="${madre.id_madre}" 
                                class="view-btn">
                    </ui5-button>
                    <ui5-button icon="edit" design="Transparent" 
                                data-id="${madre.id_madre}" 
                                class="edit-btn">
                    </ui5-button>
                </ui5-table-cell>
            `;
            
            table.appendChild(row);
        });
        
        // Agregar event listeners a botones
        table.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.target.closest('ui5-button').dataset.id;
                window.location.href = `/fiori/madres/${id}/`;
            });
        });
        
        table.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.target.closest('ui5-button').dataset.id;
                window.location.href = `/fiori/madres/${id}/edit/`;
            });
        });
    }
    
    updatePagination() {
        const pageInfo = document.getElementById('page-info');
        const prevBtn = document.getElementById('prev-page-btn');
        const nextBtn = document.getElementById('next-page-btn');
        
        if (pageInfo) {
            pageInfo.textContent = `Página ${this.currentPage} de ${this.totalPages}`;
        }
        
        if (prevBtn) {
            prevBtn.disabled = this.currentPage <= 1;
        }
        
        if (nextBtn) {
            nextBtn.disabled = this.currentPage >= this.totalPages;
        }
    }
    
    applyFilters() {
        const filterRun = document.getElementById('filter-run')?.value;
        const filterNombre = document.getElementById('filter-nombre')?.value;
        const filterNacionalidad = document.getElementById('filter-nacionalidad')?.value;
        
        this.filters = {};
        if (filterRun) this.filters.run = filterRun;
        if (filterNombre) this.filters.nombre = filterNombre;
        if (filterNacionalidad) this.filters.fk_nacionalidad = filterNacionalidad;
        
        this.currentPage = 1;
        this.loadMadres();
    }
    
    clearFilters() {
        document.getElementById('filter-run').value = '';
        document.getElementById('filter-nombre').value = '';
        document.getElementById('filter-nacionalidad').value = '';
        
        this.filters = {};
        this.currentPage = 1;
        this.loadMadres();
    }
    
    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadMadres();
        }
    }
    
    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.loadMadres();
        }
    }
    
    exportToExcel() {
        // Implementar exportación a Excel
        window.open(`/api/maternity/madres/export/?${new URLSearchParams(this.filters)}`, '_blank');
    }
    
    getAccessToken() {
        return localStorage.getItem('access_token');
    }
    
    showError(message) {
        console.error(message);
        // Implementar toast de error con UI5
    }
}