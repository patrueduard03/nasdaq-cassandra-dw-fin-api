// Financial Data Warehouse Web Interface
// Main JavaScript file for handling UI interactions and API calls

class FinancialDataApp {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.currentChart = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialData();
        this.setDefaultTab();
    }

    // Event Binding
    bindEvents() {
        // Tab navigation
        document.getElementById('assets-tab').addEventListener('click', () => this.showSection('assets'));
        document.getElementById('datasources-tab').addEventListener('click', () => this.showSection('datasources'));
        document.getElementById('timeseries-tab').addEventListener('click', () => this.showSection('timeseries'));
        document.getElementById('ingest-tab').addEventListener('click', () => this.showSection('ingest'));

        // Form submissions
        document.getElementById('create-asset-form').addEventListener('submit', (e) => this.handleCreateAsset(e));
        document.getElementById('create-datasource-form').addEventListener('submit', (e) => this.handleCreateDataSource(e));
        document.getElementById('ingest-form').addEventListener('submit', (e) => this.handleDataIngestion(e));

        // Time series data loading
        document.getElementById('load-timeseries').addEventListener('click', () => this.loadTimeSeriesData());
        document.getElementById('update-chart').addEventListener('click', () => this.updateChart());
    }

    // UI Navigation
    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.add('d-none');
        });

        // Remove active class from all tabs
        document.querySelectorAll('.list-group-item').forEach(tab => {
            tab.classList.remove('active');
        });

        // Show selected section
        document.getElementById(`${sectionName}-content`).classList.remove('d-none');
        document.getElementById(`${sectionName}-tab`).classList.add('active');

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    setDefaultTab() {
        this.showSection('assets');
    }

    // Data Loading
    async loadInitialData() {
        await this.loadAssets();
        await this.loadDataSources();
    }

    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'assets':
                await this.loadAssets();
                break;
            case 'datasources':
                await this.loadDataSources();
                break;
            case 'timeseries':
                await this.populateTimeSeriesSelects();
                break;
            case 'ingest':
                await this.populateIngestionSelects();
                break;
        }
    }

    // API Methods
    async apiCall(endpoint, method = 'GET', data = null) {
        try {
            const config = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };

            if (data) {
                config.body = JSON.stringify(data);
            }

            const response = await fetch(`${this.baseURL}${endpoint}`, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showToast('Error', error.message, 'error');
            throw error;
        }
    }

    // Assets Management
    async loadAssets() {
        try {
            const assets = await this.apiCall('/assets');
            this.populateAssetsTable(assets);
        } catch (error) {
            console.error('Failed to load assets:', error);
        }
    }

    populateAssetsTable(assets) {
        const tbody = document.querySelector('#assets-table tbody');
        tbody.innerHTML = '';

        assets.forEach(asset => {
            const row = document.createElement('tr');
            const symbol = asset.attributes?.symbol || 'N/A';
            
            row.innerHTML = `
                <td>${asset.id}</td>
                <td><strong>${asset.name}</strong></td>
                <td>${asset.description}</td>
                <td><span class="badge bg-info">${symbol}</span></td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="app.deleteAsset(${asset.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async handleCreateAsset(e) {
        e.preventDefault();
        
        const assetData = {
            name: document.getElementById('asset-name').value,
            description: document.getElementById('asset-description').value,
            attributes: {
                symbol: document.getElementById('asset-symbol').value,
                type: document.getElementById('asset-type').value,
                exchange: document.getElementById('asset-exchange').value || 'NASDAQ'
            }
        };

        try {
            await this.apiCall('/assets', 'POST', assetData);
            this.showToast('Success', 'Asset created successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('createAssetModal')).hide();
            document.getElementById('create-asset-form').reset();
            await this.loadAssets();
        } catch (error) {
            console.error('Failed to create asset:', error);
        }
    }

    async deleteAsset(assetId) {
        if (!confirm('Are you sure you want to delete this asset?')) {
            return;
        }

        try {
            await this.apiCall(`/assets/${assetId}`, 'DELETE');
            this.showToast('Success', 'Asset deleted successfully!', 'success');
            await this.loadAssets();
        } catch (error) {
            console.error('Failed to delete asset:', error);
        }
    }

    // Data Sources Management
    async loadDataSources() {
        try {
            const dataSources = await this.apiCall('/data-sources');
            this.populateDataSourcesTable(dataSources);
        } catch (error) {
            console.error('Failed to load data sources:', error);
        }
    }

    populateDataSourcesTable(dataSources) {
        const tbody = document.querySelector('#datasources-table tbody');
        tbody.innerHTML = '';

        dataSources.forEach(ds => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${ds.id}</td>
                <td><strong>${ds.name}</strong></td>
                <td><span class="badge bg-primary">${ds.provider}</span></td>
                <td>${ds.description}</td>
                <td>
                    <small class="text-muted">Created: ${new Date(ds.system_date).toLocaleDateString()}</small>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async handleCreateDataSource(e) {
        e.preventDefault();
        
        const dataSourceData = {
            name: document.getElementById('datasource-name').value,
            provider: document.getElementById('datasource-provider').value,
            description: document.getElementById('datasource-description').value,
            attributes: {}
        };

        try {
            await this.apiCall('/data-sources', 'POST', dataSourceData);
            this.showToast('Success', 'Data source created successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('createDataSourceModal')).hide();
            document.getElementById('create-datasource-form').reset();
            await this.loadDataSources();
        } catch (error) {
            console.error('Failed to create data source:', error);
        }
    }

    // Time Series Management
    async populateTimeSeriesSelects() {
        try {
            const [assets, dataSources] = await Promise.all([
                this.apiCall('/assets'),
                this.apiCall('/data-sources')
            ]);

            this.populateSelect('timeseries-asset', assets, 'id', 'name');
            this.populateSelect('timeseries-datasource', dataSources, 'id', 'name');
        } catch (error) {
            console.error('Failed to populate time series selects:', error);
        }
    }

    async loadTimeSeriesData() {
        const assetId = document.getElementById('timeseries-asset').value;
        const dataSourceId = document.getElementById('timeseries-datasource').value;
        const startDate = document.getElementById('timeseries-start-date').value;
        const endDate = document.getElementById('timeseries-end-date').value;

        if (!assetId || !dataSourceId) {
            this.showToast('Warning', 'Please select both asset and data source', 'warning');
            return;
        }

        try {
            let endpoint = `/time-series/${assetId}/${dataSourceId}`;
            if (startDate && endDate) {
                endpoint += `?start_date=${startDate}&end_date=${endDate}`;
            }

            const data = await this.apiCall(endpoint);
            this.timeSeriesData = data; // Store data for metric updates
            this.renderTimeSeriesChart(data);
            
            // Show metrics selection after data is loaded
            document.getElementById('metrics-selection').style.display = 'block';
        } catch (error) {
            console.error('Failed to load time series data:', error);
        }
    }

    renderTimeSeriesChart(data) {
        const canvas = document.getElementById('timeseriesChart');
        const placeholder = document.getElementById('timeseries-placeholder');
        
        if (data.length === 0) {
            canvas.style.display = 'none';
            placeholder.style.display = 'block';
            placeholder.innerHTML = `
                <i class="fas fa-exclamation-circle fa-3x mb-3 text-warning"></i>
                <p>No data found for the selected criteria</p>
            `;
            return;
        }

        canvas.style.display = 'block';
        placeholder.style.display = 'none';

        // Destroy existing chart
        if (this.currentChart) {
            this.currentChart.destroy();
        }

        // Get selected metrics
        const selectedMetrics = this.getSelectedMetrics();
        
        // Prepare chart data
        const labels = data.map(d => d.business_date).reverse();
        const datasets = [];
        
        // Define colors for different metrics
        const colors = {
            'close': '#0d6efd',
            'open': '#198754',
            'high': '#dc3545',
            'low': '#fd7e14',
            'adj_close': '#6f42c1',
            'adj_open': '#20c997',
            'adj_high': '#e91e63',
            'adj_low': '#795548',
            'volume': '#6c757d',
            'adj_volume': '#607d8b',
            'split_ratio': '#ff9800'
        };

        // Create datasets for selected metrics
        selectedMetrics.forEach((metric, index) => {
            const isVolumeMetric = metric === 'volume' || metric === 'adj_volume';
            const metricData = data.map(d => d.values_double?.[metric] || 0).reverse();
            const baseColor = colors[metric] || `hsl(${index * 60}, 70%, 50%)`;
            
            datasets.push({
                label: this.formatMetricName(metric),
                data: metricData,
                borderColor: baseColor,
                backgroundColor: baseColor + '20',
                tension: 0.1,
                yAxisID: isVolumeMetric ? 'y1' : 'y'
            });
        });

        const ctx = canvas.getContext('2d');
        this.currentChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Time Series Data - ${selectedMetrics.map(m => this.formatMetricName(m)).join(', ')}`
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Price ($)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: selectedMetrics.some(m => m === 'volume' || m === 'adj_volume'),
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Volume'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });
    }

    getSelectedMetrics() {
        const checkboxes = document.querySelectorAll('.metric-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    formatMetricName(metric) {
        return metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    updateChart() {
        if (this.timeSeriesData && this.timeSeriesData.length > 0) {
            const selectedMetrics = this.getSelectedMetrics();
            if (selectedMetrics.length === 0) {
                this.showToast('Warning', 'Please select at least one metric to display', 'warning');
                return;
            }
            this.renderTimeSeriesChart(this.timeSeriesData);
        }
    }

    // Data Ingestion
    async populateIngestionSelects() {
        try {
            const [assets, dataSources] = await Promise.all([
                this.apiCall('/assets'),
                this.apiCall('/data-sources')
            ]);

            // Filter for Nasdaq data sources only
            const nasdaqDataSources = dataSources.filter(ds => ds.provider === 'Nasdaq');

            this.populateSelect('ingest-asset', assets, 'id', 'name');
            this.populateSelect('ingest-datasource', nasdaqDataSources, 'id', 'name');
        } catch (error) {
            console.error('Failed to populate ingestion selects:', error);
        }
    }

    async handleDataIngestion(e) {
        e.preventDefault();
        
        const ingestionData = {
            asset_id: parseInt(document.getElementById('ingest-asset').value),
            data_source_id: parseInt(document.getElementById('ingest-datasource').value),
            start_date: document.getElementById('ingest-start-date').value,
            end_date: document.getElementById('ingest-end-date').value
        };

        const progressDiv = document.getElementById('ingestion-progress');
        const submitBtn = document.querySelector('#ingest-form button[type="submit"]');
        
        try {
            // Show progress
            progressDiv.style.display = 'block';
            submitBtn.disabled = true;
            
            await this.apiCall('/ingest/nasdaq', 'POST', ingestionData);
            
            this.showToast('Success', 'Data ingestion completed successfully!', 'success');
            document.getElementById('ingest-form').reset();
        } catch (error) {
            console.error('Failed to ingest data:', error);
        } finally {
            // Hide progress
            progressDiv.style.display = 'none';
            submitBtn.disabled = false;
        }
    }

    // Utility Methods
    populateSelect(selectId, options, valueField, textField) {
        const select = document.getElementById(selectId);
        
        // Clear existing options except the first one
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }

        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option[valueField];
            optionElement.textContent = option[textField];
            select.appendChild(optionElement);
        });
    }

    showToast(title, message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        const toastId = 'toast-' + Date.now();
        
        const toastHTML = `
            <div class="toast toast-${type}" role="alert" id="${toastId}" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="fas fa-${this.getToastIcon(type)} me-2"></i>
                    <strong class="me-auto">${title}</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
        toast.show();
        
        // Remove toast from DOM after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    getToastIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            default: return 'info-circle';
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new FinancialDataApp();
});

// Make deleteAsset function globally available for onclick handlers
window.deleteAsset = (assetId) => {
    if (window.app) {
        window.app.deleteAsset(assetId);
    }
};
