// Financial Data Warehouse Web Interface
// Main JavaScript file for handling UI interactions and API calls

class FinancialDataApp {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.currentChart = null;
        this.currentChart2 = null; // Secondary chart instance
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
        
        // Second chart controls
        document.getElementById('update-chart-2').addEventListener('click', () => this.updateChart2());
        document.getElementById('show-second-chart').addEventListener('click', () => this.showSecondChart());
        document.getElementById('hide-second-chart').addEventListener('click', () => this.hideSecondChart());
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
                    <button class="btn btn-sm btn-outline-info me-1" onclick="app.viewAsset(${asset.id})" title="View Details">
                        <i class="fas fa-info-circle"></i> Details
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="app.deleteAsset(${asset.id})" title="Delete Asset">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async handleCreateAsset(e) {
        e.preventDefault();
        
        // Collect additional attributes from dynamic form
        const additionalAttributes = this.collectAssetAttributes();
        
        // Combine default attributes with additional ones
        const allAttributes = {
            symbol: document.getElementById('asset-symbol').value,
            type: document.getElementById('asset-type').value,
            exchange: document.getElementById('asset-exchange').value || 'NASDAQ',
            ...additionalAttributes
        };
        
        const assetData = {
            name: document.getElementById('asset-name').value,
            description: document.getElementById('asset-description').value,
            attributes: allAttributes
        };

        try {
            await this.apiCall('/assets', 'POST', assetData);
            this.showToast('Success', 'Asset created successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('createAssetModal')).hide();
            document.getElementById('create-asset-form').reset();
            this.resetAssetAttributesPairs();
            await this.loadAssets();
        } catch (error) {
            console.error('Failed to create asset:', error);
            if (error.response && error.response.status === 409) {
                // Asset with same symbol already exists - show specific error
                this.showToast('Duplicate Asset', 
                    `An asset with symbol "${assetData.attributes.symbol}" already exists or has been previously deleted and resurrected. Please use a different symbol or check your existing assets.`, 
                    'warning'
                );
            } else {
                this.showToast('Error', 'Failed to create asset. Please try again.', 'error');
            }
        }
    }

    // View asset details
    async viewAsset(assetId) {
        try {
            const asset = await this.apiCall(`/assets/${assetId}`);
            
            // Format attributes for display
            const attributesHtml = asset.attributes && Object.keys(asset.attributes).length > 0
                ? Object.entries(asset.attributes)
                    .map(([key, value]) => `<li><strong>${key}:</strong> ${value}</li>`)
                    .join('')
                : '<li class="text-muted">No attributes defined</li>';
            
            // Show details in a toast
            const detailsHtml = `
                <div class="mb-2"><strong>ID:</strong> ${asset.id}</div>
                <div class="mb-2"><strong>Name:</strong> ${asset.name}</div>
                <div class="mb-2"><strong>Description:</strong> ${asset.description}</div>
                <div class="mb-2"><strong>Status:</strong> <span class="badge ${asset.is_deleted ? 'bg-danger' : 'bg-success'}">${asset.is_deleted ? 'Deleted' : 'Active'}</span></div>
                <div class="mb-2"><strong>Created:</strong> ${new Date(asset.system_date).toLocaleString()}</div>
                <div class="mb-2"><strong>Valid From:</strong> ${new Date(asset.valid_from).toLocaleString()}</div>
                ${asset.valid_to ? `<div class="mb-2"><strong>Valid To:</strong> ${new Date(asset.valid_to).toLocaleString()}</div>` : ''}
                <div class="mb-2"><strong>Attributes:</strong></div>
                <ul class="mb-0 ps-3">${attributesHtml}</ul>
            `;
            
            this.showToast('Asset Details', detailsHtml, 'info', 8000);
        } catch (error) {
            console.error('Failed to load asset details:', error);
            this.showToast('Error', 'Failed to load asset details', 'error');
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

    async deleteDataSource(dataSourceId) {
        if (!confirm('Are you sure you want to delete this data source?')) {
            return;
        }

        try {
            await this.apiCall(`/data-sources/${dataSourceId}`, 'DELETE');
            this.showToast('Success', 'Data source deleted successfully!', 'success');
            await this.loadDataSources();
        } catch (error) {
            console.error('Failed to delete data source:', error);
            this.showToast('Error', 'Failed to delete data source. Please try again.', 'error');
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
            // Format attributes for display
            const attributesDisplay = ds.attributes && Object.keys(ds.attributes).length > 0 
                ? Object.entries(ds.attributes)
                    .map(([key, value]) => `<span class="badge bg-secondary me-1">${key}: ${value}</span>`)
                    .join('')
                : '<span class="text-muted">None</span>';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${ds.id}</td>
                <td><strong>${ds.name}</strong></td>
                <td><span class="badge bg-primary">${ds.provider}</span></td>
                <td>${ds.description || 'N/A'}</td>
                <td>${attributesDisplay}</td>
                <td>
                    <button class="btn btn-sm btn-outline-info me-1" onclick="viewDataSource(${ds.id})" title="View Details">
                        <i class="fas fa-info-circle"></i> Details
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteDataSource(${ds.id})" title="Delete Data Source">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async handleCreateDataSource(e) {
        e.preventDefault();
        
        // Collect attributes from dynamic form
        const attributes = this.collectAttributes();
        
        const dataSourceData = {
            name: document.getElementById('datasource-name').value,
            provider: document.getElementById('datasource-provider').value,
            description: document.getElementById('datasource-description').value || null,
            attributes: attributes
        };

        try {
            await this.apiCall('/data-sources', 'POST', dataSourceData);
            this.showToast('Success', 'Data source created successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('createDataSourceModal')).hide();
            document.getElementById('create-datasource-form').reset();
            this.resetAttributesPairs();
            await this.loadDataSources();
        } catch (error) {
            console.error('Failed to create data source:', error);
            if (error.response && error.response.status === 422) {
                this.showToast('Validation Error', 'Please check your input data and try again.', 'error');
            } else {
                this.showToast('Error', 'Failed to create data source. Please try again.', 'error');
            }
        }
    }

    // Add new attribute pair
    addAttribute() {
        const container = document.getElementById('attributesContainer');
        const newAttribute = document.createElement('div');
        newAttribute.className = 'attribute-pair mb-2';
        newAttribute.innerHTML = `
            <div class="row align-items-center">
                <div class="col-5">
                    <input type="text" class="form-control attribute-key" placeholder="Key (e.g., version)">
                </div>
                <div class="col-5">
                    <input type="text" class="form-control attribute-value" placeholder="Value">
                </div>
                <div class="col-2">
                    <button type="button" class="btn btn-outline-danger btn-sm" onclick="app.removeAttribute(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        container.appendChild(newAttribute);
    }

    // Remove attribute pair
    removeAttribute(button) {
        const container = document.getElementById('attributesContainer');
        const attributePair = button.closest('.attribute-pair');
        
        // Don't remove if it's the last one
        if (container.children.length > 1) {
            attributePair.remove();
        } else {
            // Clear the inputs instead
            attributePair.querySelector('.attribute-key').value = '';
            attributePair.querySelector('.attribute-value').value = '';
        }
    }

    // Collect attributes from form
    collectAttributes() {
        const attributes = {};
        const attributePairs = document.querySelectorAll('.attribute-pair');
        
        attributePairs.forEach(pair => {
            const key = pair.querySelector('.attribute-key').value.trim();
            const value = pair.querySelector('.attribute-value').value.trim();
            
            if (key && value) {
                attributes[key] = value;
            }
        });
        
        return attributes;
    }

    // Reset attributes to single empty pair
    resetAttributesPairs() {
        const container = document.getElementById('attributesContainer');
        container.innerHTML = `
            <div class="attribute-pair mb-2">
                <div class="row align-items-center">
                    <div class="col-5">
                        <input type="text" class="form-control attribute-key" placeholder="Key (e.g., version)">
                    </div>
                    <div class="col-5">
                        <input type="text" class="form-control attribute-value" placeholder="Value">
                    </div>
                    <div class="col-2">
                        <button type="button" class="btn btn-outline-danger btn-sm" onclick="app.removeAttribute(this)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Asset Attribute Management Functions
    addAssetAttribute() {
        const container = document.getElementById('assetAttributesContainer');
        const newAttribute = document.createElement('div');
        newAttribute.className = 'asset-attribute-pair mb-2';
        newAttribute.innerHTML = `
            <div class="row align-items-center">
                <div class="col-5">
                    <input type="text" class="form-control asset-attribute-key" placeholder="Key (e.g., sector, market_cap)">
                </div>
                <div class="col-5">
                    <input type="text" class="form-control asset-attribute-value" placeholder="Value">
                </div>
                <div class="col-2">
                    <button type="button" class="btn btn-outline-danger btn-sm" onclick="app.removeAssetAttribute(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        container.appendChild(newAttribute);
    }

    // Remove asset attribute pair
    removeAssetAttribute(button) {
        const container = document.getElementById('assetAttributesContainer');
        const attributePair = button.closest('.asset-attribute-pair');
        
        // Don't remove if it's the last one
        if (container.children.length > 1) {
            attributePair.remove();
        } else {
            // Clear the inputs instead
            attributePair.querySelector('.asset-attribute-key').value = '';
            attributePair.querySelector('.asset-attribute-value').value = '';
        }
    }

    // Collect asset attributes from form
    collectAssetAttributes() {
        const attributes = {};
        const attributePairs = document.querySelectorAll('.asset-attribute-pair');
        
        attributePairs.forEach(pair => {
            const key = pair.querySelector('.asset-attribute-key').value.trim();
            const value = pair.querySelector('.asset-attribute-value').value.trim();
            
            if (key && value) {
                attributes[key] = value;
            }
        });
        
        return attributes;
    }

    // Reset asset attributes to single empty pair
    resetAssetAttributesPairs() {
        const container = document.getElementById('assetAttributesContainer');
        container.innerHTML = `
            <div class="asset-attribute-pair mb-2">
                <div class="row align-items-center">
                    <div class="col-5">
                        <input type="text" class="form-control asset-attribute-key" placeholder="Key (e.g., sector, market_cap)">
                    </div>
                    <div class="col-5">
                        <input type="text" class="form-control asset-attribute-value" placeholder="Value">
                    </div>
                    <div class="col-2">
                        <button type="button" class="btn btn-outline-danger btn-sm" onclick="app.removeAssetAttribute(this)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
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
        
        // Define colors for different metrics with better visibility
        const colors = {
            'close': '#0d6efd',      // Blue
            'open': '#198754',       // Green
            'high': '#dc3545',       // Red
            'low': '#fd7e14',        // Orange
            'adj_close': '#6f42c1',  // Purple
            'adj_open': '#20c997',   // Teal
            'adj_high': '#e91e63',   // Pink
            'adj_low': '#795548',    // Brown
            'volume': '#6c757d',     // Gray
            'adj_volume': '#607d8b', // Blue Gray
            'split_ratio': '#ff9800' // Amber
        };

        // Enhanced color palette for additional metrics
        const fallbackColors = [
            '#FF6B35', '#F7931E', '#FFD23F', '#06FFA5', '#3BCEAC',
            '#0EAD69', '#68EDC6', '#8CD867', '#C0CA33', '#FBC02D',
            '#FF7043', '#8E24AA', '#5E35B1', '#3949AB', '#1E88E5'
        ];

        // Create datasets for selected metrics
        selectedMetrics.forEach((metric, index) => {
            const isVolumeMetric = metric === 'volume' || metric === 'adj_volume';
            const metricData = data.map(d => d.values_double?.[metric] || 0).reverse();
            const baseColor = colors[metric] || fallbackColors[index % fallbackColors.length];
            
            datasets.push({
                label: this.formatMetricName(metric),
                data: metricData,
                borderColor: baseColor,
                backgroundColor: 'transparent',
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 0,
                pointHoverRadius: 5,
                pointBackgroundColor: baseColor,
                pointBorderColor: baseColor,
                pointHoverBackgroundColor: baseColor,
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2,
                yAxisID: isVolumeMetric ? 'y1' : 'y',
                fill: false
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
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    title: {
                        display: true,
                        text: `Time Series Data - ${selectedMetrics.map(m => this.formatMetricName(m)).join(', ')}`
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            generateLabels: function(chart) {
                                // Ensure all datasets are shown in legend with their colors
                                return chart.data.datasets.map((dataset, index) => {
                                    return {
                                        text: dataset.label,
                                        fillStyle: dataset.borderColor,
                                        strokeStyle: dataset.borderColor,
                                        lineWidth: 2,
                                        hidden: !chart.isDatasetVisible(index),
                                        datasetIndex: index
                                    };
                                });
                            },
                            usePointStyle: false,
                            padding: 10
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1,
                        displayColors: true,
                        filter: function(tooltipItem) {
                            // Always show all datasets
                            return true;
                        },
                        callbacks: {
                            title: function(tooltipItems) {
                                return tooltipItems[0].label;
                            },
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                const isVolume = context.dataset.yAxisID === 'y1';
                                if (isVolume) {
                                    return `${label}: ${value.toLocaleString()}`;
                                } else {
                                    return `${label}: $${value.toFixed(2)}`;
                                }
                            }
                        }
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
                        }
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
        
        // Show the secondary chart button when primary chart is rendered successfully
        document.getElementById('show-second-chart-btn').style.display = 'block';
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

    // Secondary Chart Methods
    updateChart2() {
        if (this.timeSeriesData && this.timeSeriesData.length > 0) {
            const selectedMetrics = this.getSelectedMetrics2();
            if (selectedMetrics.length === 0) {
                this.showToast('Warning', 'Please select at least one metric for the secondary chart', 'warning');
                return;
            }
            this.renderTimeSeriesChart2(this.timeSeriesData);
            
            // Show the "Show Second Chart" button after first update
            document.getElementById('show-second-chart-btn').style.display = 'block';
        } else {
            this.showToast('Warning', 'Please load time series data first', 'warning');
        }
    }

    showSecondChart() {
        document.getElementById('second-chart-section').style.display = 'block';
        document.getElementById('show-second-chart-btn').style.display = 'none';
        
        // If no metrics are selected for the secondary chart, default to volume metrics
        const selectedMetrics2 = this.getSelectedMetrics2();
        if (selectedMetrics2.length === 0) {
            // Auto-select volume if it exists in the data
            const volumeCheckbox = document.getElementById('metric-volume-2');
            if (volumeCheckbox) {
                volumeCheckbox.checked = true;
            }
        }
    }

    hideSecondChart() {
        document.getElementById('second-chart-section').style.display = 'none';
        document.getElementById('show-second-chart-btn').style.display = 'block';
    }

    getSelectedMetrics2() {
        const checkboxes = document.querySelectorAll('.metric-checkbox-2:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    renderTimeSeriesChart2(data) {
        const canvas = document.getElementById('timeseriesChart2');
        const placeholder = document.getElementById('timeseries-placeholder-2');
        
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

        // Destroy existing secondary chart
        if (this.currentChart2) {
            this.currentChart2.destroy();
        }

        // Get selected metrics for secondary chart
        const selectedMetrics = this.getSelectedMetrics2();
        
        // Prepare chart data
        const labels = data.map(d => d.business_date).reverse();
        const datasets = [];
        
        // Define colors for different metrics with better visibility
        const colors = {
            'close': '#0d6efd',      // Blue
            'open': '#198754',       // Green
            'high': '#dc3545',       // Red
            'low': '#fd7e14',        // Orange
            'adj_close': '#6f42c1',  // Purple
            'adj_open': '#20c997',   // Teal
            'adj_high': '#e91e63',   // Pink
            'adj_low': '#795548',    // Brown
            'volume': '#6c757d',     // Gray
            'adj_volume': '#607d8b', // Blue Gray
            'split_ratio': '#ff9800' // Amber
        };

        // Enhanced color palette for additional metrics
        const fallbackColors = [
            '#FF6B35', '#F7931E', '#FFD23F', '#06FFA5', '#3BCEAC',
            '#0EAD69', '#68EDC6', '#8CD867', '#C0CA33', '#FBC02D',
            '#FF7043', '#8E24AA', '#5E35B1', '#3949AB', '#1E88E5'
        ];

        // Create datasets for selected metrics
        selectedMetrics.forEach((metric, index) => {
            const isVolumeMetric = metric === 'volume' || metric === 'adj_volume';
            const metricData = data.map(d => d.values_double?.[metric] || 0).reverse();
            const baseColor = colors[metric] || fallbackColors[index % fallbackColors.length];
            
            datasets.push({
                label: this.formatMetricName(metric),
                data: metricData,
                borderColor: baseColor,
                backgroundColor: 'transparent',
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 0,
                pointHoverRadius: 5,
                pointBackgroundColor: baseColor,
                pointBorderColor: baseColor,
                pointHoverBackgroundColor: baseColor,
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2,
                yAxisID: isVolumeMetric ? 'y1' : 'y',
                fill: false
            });
        });

        const ctx = canvas.getContext('2d');
        this.currentChart2 = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    title: {
                        display: true,
                        text: `Secondary Chart - ${selectedMetrics.map(m => this.formatMetricName(m)).join(', ')}`
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            generateLabels: function(chart) {
                                // Ensure all datasets are shown in legend with their colors
                                return chart.data.datasets.map((dataset, index) => {
                                    return {
                                        text: dataset.label,
                                        fillStyle: dataset.borderColor,
                                        strokeStyle: dataset.borderColor,
                                        lineWidth: 2,
                                        hidden: !chart.isDatasetVisible(index),
                                        datasetIndex: index
                                    };
                                });
                            },
                            usePointStyle: false,
                            padding: 10
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1,
                        displayColors: true,
                        filter: function(tooltipItem) {
                            // Always show all datasets
                            return true;
                        },
                        callbacks: {
                            title: function(context) {
                                return 'Date: ' + context[0].label;
                            },
                            label: function(context) {
                                return context.dataset.label + ': ' + 
                                       (typeof context.parsed.y === 'number' ? 
                                        context.parsed.y.toFixed(2) : context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
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
                    }
                }
            }
        });
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

    // View data source details
    async viewDataSource(dataSourceId) {
        try {
            const dataSource = await this.apiCall(`/data-sources/${dataSourceId}`);
            
            // Format attributes for display
            const attributesHtml = dataSource.attributes && Object.keys(dataSource.attributes).length > 0
                ? Object.entries(dataSource.attributes)
                    .map(([key, value]) => `<li><strong>${key}:</strong> ${value}</li>`)
                    .join('')
                : '<li class="text-muted">No attributes defined</li>';
            
            // Show details in a modal-like toast
            const detailsHtml = `
                <div class="mb-2"><strong>ID:</strong> ${dataSource.id}</div>
                <div class="mb-2"><strong>Name:</strong> ${dataSource.name}</div>
                <div class="mb-2"><strong>Provider:</strong> ${dataSource.provider}</div>
                <div class="mb-2"><strong>Description:</strong> ${dataSource.description || 'None'}</div>
                <div class="mb-2"><strong>Created:</strong> ${new Date(dataSource.system_date).toLocaleString()}</div>
                <div class="mb-2"><strong>Attributes:</strong></div>
                <ul class="mb-0 ps-3">${attributesHtml}</ul>
            `;
            
            this.showToast('Data Source Details', detailsHtml, 'info', 8000);
        } catch (error) {
            console.error('Failed to load data source details:', error);
            this.showToast('Error', 'Failed to load data source details', 'error');
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

    showToast(title, message, type = 'info', duration = 5000) {
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
        const toast = new bootstrap.Toast(toastElement, { delay: duration });
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

// Make viewAsset function globally available for onclick handlers
window.viewAsset = (assetId) => {
    if (window.app) {
        window.app.viewAsset(assetId);
    }
};

// Make viewDataSource function globally available for onclick handlers
window.viewDataSource = (dataSourceId) => {
    if (window.app) {
        window.app.viewDataSource(dataSourceId);
    }
};

// Make deleteDataSource function globally available for onclick handlers
window.deleteDataSource = (dataSourceId) => {
    if (window.app) {
        window.app.deleteDataSource(dataSourceId);
    }
};
