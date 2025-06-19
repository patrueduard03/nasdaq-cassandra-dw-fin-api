// Financial Data Warehouse Web Interface
// Main JavaScript file for handling UI interactions and API calls

class FinancialDataApp {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.currentChart = null;
        this.currentChart2 = null; // Secondary chart instance
        this.assetsAdminMode = false; // Track admin mode for assets
        this.dataSourcesAdminMode = false; // Track admin mode for data sources
        this.websocket = null; // WebSocket connection for real-time updates
        this.currentIngestionSession = null; // Track current ingestion session
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialData();
        this.setDefaultTab();
        this.initWebSocket(); // Initialize WebSocket for real-time updates
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
        document.getElementById('edit-asset-form').addEventListener('submit', (e) => this.handleEditAsset(e));
        document.getElementById('edit-datasource-form').addEventListener('submit', (e) => this.handleEditDataSource(e));
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
                await this.loadIngestionStatus();
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
            const endpoint = this.assetsAdminMode ? '/assets/admin/all' : '/assets';
            const assets = await this.apiCall(endpoint);
            this.populateAssetsTable(assets);
        } catch (error) {
            console.error('Failed to load assets:', error);
        }
    }

    populateAssetsTable(assets) {
        const tbody = document.querySelector('#assets-table tbody');
        tbody.innerHTML = '';

        // Group assets by ID to detect multiple versions
        const assetVersions = {};
        assets.forEach(asset => {
            if (!assetVersions[asset.id]) {
                assetVersions[asset.id] = [];
            }
            assetVersions[asset.id].push(asset);
        });

        // Sort versions within each group by valid_from (newest first)
        Object.keys(assetVersions).forEach(id => {
            assetVersions[id].sort((a, b) => new Date(b.valid_from) - new Date(a.valid_from));
        });

        assets.forEach((asset, index) => {
            const row = document.createElement('tr');
            const symbol = asset.attributes?.symbol || 'N/A';
            
            // Determine status and type for temporal display
            let status, statusBadge, rowClass = '';
            
            if (asset.is_deleted) {
                status = 'Deletion Marker';
                statusBadge = '<span class="badge bg-danger">Deleted</span>';
                rowClass = 'table-danger';
            } else {
                // Check if this is the current active version
                const allVersions = assetVersions[asset.id];
                
                // Find if there's any deletion marker after this version
                const hasLaterDeletion = allVersions.some(v => 
                    v.is_deleted && new Date(v.valid_from) > new Date(asset.valid_from)
                );
                
                // Find the latest non-deleted version
                const latestActiveVersion = allVersions
                    .filter(v => !v.is_deleted)
                    .sort((a, b) => new Date(b.valid_from) - new Date(a.valid_from))[0];
                
                const isCurrentVersion = latestActiveVersion && 
                    latestActiveVersion.valid_from === asset.valid_from;
                
                if (hasLaterDeletion) {
                    status = 'Superseded by Deletion';
                    statusBadge = '<span class="badge bg-warning">Historical</span>';
                    rowClass = 'table-warning';
                } else if (isCurrentVersion) {
                    status = 'Current Version';
                    statusBadge = '<span class="badge bg-success">Active</span>';
                    rowClass = 'table-success';
                } else {
                    status = 'Historical Version';
                    statusBadge = '<span class="badge bg-secondary">Historical</span>';
                    rowClass = 'table-light';
                }
            }
            
            // Add version info for admin mode
            const versionCount = assetVersions[asset.id].length;
            const versionIndex = assetVersions[asset.id].findIndex(v => 
                v.valid_from === asset.valid_from && v.is_deleted === asset.is_deleted
            ) + 1;
            
            const versionIndicator = this.assetsAdminMode && versionCount > 1 ? 
                ` <small class="text-muted">(v${versionIndex}/${versionCount})</small>` : '';
            
            row.className = this.assetsAdminMode ? rowClass : '';
            
            // Admin mode columns (hidden by default)
            const adminColumns = this.assetsAdminMode ? `
                <td class="admin-only">${statusBadge}</td>
                <td class="admin-only"><small>${this.formatDateTime(asset.valid_from)}</small></td>
                <td class="admin-only"><small>${this.formatDateTime(asset.valid_to)}</small></td>
            ` : `
                <td class="admin-only d-none">${statusBadge}</td>
                <td class="admin-only d-none"><small>${this.formatDateTime(asset.valid_from)}</small></td>
                <td class="admin-only d-none"><small>${this.formatDateTime(asset.valid_to)}</small></td>
            `;
            
            row.innerHTML = `
                <td>${asset.id}${versionIndicator}</td>
                <td><strong>${asset.name}</strong></td>
                <td>${asset.description}</td>
                <td><span class="badge bg-info">${symbol}</span></td>
                ${adminColumns}
                <td style="min-width: 120px;">
                    <button class="btn btn-sm btn-outline-info me-1" onclick="viewAsset(${asset.id})" title="View Details">
                        <i class="fas fa-info-circle"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning me-1" onclick="editAsset(${asset.id})" title="Edit Asset">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteAsset(${asset.id})" title="Delete Asset">
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
                ${asset.valid_to ? `<div class="mb-2"><strong>Valid To:</strong> ${new Date(asset.valid_to).toLocaleString()}</div>` : ''}
                <div class="mb-2"><strong>Attributes:</
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

    // Edit asset functionality
    async editAsset(assetId) {
        try {
            const asset = await this.apiCall(`/assets/${assetId}`);
            
            // Populate edit form with current asset data
            document.getElementById('edit-asset-id').value = asset.id;
            document.getElementById('edit-asset-name').value = asset.name;
            document.getElementById('edit-asset-description').value = asset.description;
            document.getElementById('edit-asset-symbol').value = asset.attributes?.symbol || '';
            document.getElementById('edit-asset-type').value = asset.attributes?.type || 'equity';
            document.getElementById('edit-asset-exchange').value = asset.attributes?.exchange || '';
            
            // Populate additional attributes
            this.populateEditAssetAttributes(asset.attributes);
            
            // Show edit modal
            new bootstrap.Modal(document.getElementById('editAssetModal')).show();
        } catch (error) {
            console.error('Failed to load asset for editing:', error);
            this.showToast('Error', 'Failed to load asset for editing', 'error');
        }
    }

    // Handle edit asset form submission
    async handleEditAsset(e) {
        e.preventDefault();
        
        const assetId = document.getElementById('edit-asset-id').value;
        
        // Collect additional attributes from dynamic form
        const additionalAttributes = this.collectEditAssetAttributes();
        
        // Combine default attributes with additional ones
        const allAttributes = {
            symbol: document.getElementById('edit-asset-symbol').value,
            type: document.getElementById('edit-asset-type').value,
            exchange: document.getElementById('edit-asset-exchange').value || 'NASDAQ',
            ...additionalAttributes
        };
        
        const assetData = {
            name: document.getElementById('edit-asset-name').value,
            description: document.getElementById('edit-asset-description').value,
            attributes: allAttributes
        };

        try {
            await this.apiCall(`/assets/${assetId}`, 'PUT', assetData);
            this.showToast('Success', 'Asset updated successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editAssetModal')).hide();
            await this.loadAssets();
        } catch (error) {
            console.error('Failed to update asset:', error);
            this.showToast('Error', 'Failed to update asset. Please try again.', 'error');
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
            const endpoint = this.dataSourcesAdminMode ? '/data-sources/admin/all' : '/data-sources';
            const dataSources = await this.apiCall(endpoint);
            this.populateDataSourcesTable(dataSources);
        } catch (error) {
            console.error('Failed to load data sources:', error);
        }
    }

    populateDataSourcesTable(dataSources) {
        const tbody = document.querySelector('#datasources-table tbody');
        tbody.innerHTML = '';

        // Group data sources by ID to detect multiple versions
        const dataSourceVersions = {};
        dataSources.forEach(ds => {
            if (!dataSourceVersions[ds.id]) {
                dataSourceVersions[ds.id] = [];
            }
            dataSourceVersions[ds.id].push(ds);
        });

        // Sort versions within each group by valid_from (newest first)
        Object.keys(dataSourceVersions).forEach(id => {
            dataSourceVersions[id].sort((a, b) => new Date(b.valid_from) - new Date(a.valid_from));
        });

        dataSources.forEach(ds => {
            // Format attributes for display with limited width
            const attributesDisplay = ds.attributes && Object.keys(ds.attributes).length > 0 
                ? Object.entries(ds.attributes)
                    .map(([key, value]) => `<span class="badge bg-secondary me-1" style="font-size: 0.7em;">${key}: ${value}</span>`)
                    .join('')
                : '<span class="text-muted">None</span>';

            // Determine status and type for temporal display
            let status, statusBadge, rowClass = '';
            
            if (ds.is_deleted) {
                status = 'Deletion Marker';
                statusBadge = '<span class="badge bg-danger">Deleted</span>';
                rowClass = 'table-danger';
            } else {
                // Check if this is the current active version
                const allVersions = dataSourceVersions[ds.id];
                
                // Find if there's any deletion marker after this version
                const hasLaterDeletion = allVersions.some(v => 
                    v.is_deleted && new Date(v.valid_from) > new Date(ds.valid_from)
                );
                
                // Find the latest non-deleted version
                const latestActiveVersion = allVersions
                    .filter(v => !v.is_deleted)
                    .sort((a, b) => new Date(b.valid_from) - new Date(a.valid_from))[0];
                
                const isCurrentVersion = latestActiveVersion && 
                    latestActiveVersion.valid_from === ds.valid_from;
                
                if (hasLaterDeletion) {
                    status = 'Superseded by Deletion';
                    statusBadge = '<span class="badge bg-warning">Historical</span>';
                    rowClass = 'table-warning';
                } else if (isCurrentVersion) {
                    status = 'Current Version';
                    statusBadge = '<span class="badge bg-success">Active</span>';
                    rowClass = 'table-success';
                } else {
                    status = 'Historical Version';
                    statusBadge = '<span class="badge bg-secondary">Historical</span>';
                    rowClass = 'table-light';
                }
            }

            // Add version info for admin mode
            const versionCount = dataSourceVersions[ds.id].length;
            const versionIndex = dataSourceVersions[ds.id].findIndex(v => 
                v.valid_from === ds.valid_from && v.is_deleted === ds.is_deleted
            ) + 1;
            
            const versionIndicator = this.dataSourcesAdminMode && versionCount > 1 ? 
                ` <small class="text-muted">(v${versionIndex}/${versionCount})</small>` : '';
            
            // Admin mode columns (hidden by default)
            const adminColumns = this.dataSourcesAdminMode ? `
                <td class="admin-only">${statusBadge}</td>
                <td class="admin-only"><small>${this.formatDateTime(ds.valid_from)}</small></td>
                <td class="admin-only"><small>${this.formatDateTime(ds.valid_to)}</small></td>
            ` : `
                <td class="admin-only d-none">${statusBadge}</td>
                <td class="admin-only d-none"><small>${this.formatDateTime(ds.valid_from)}</small></td>
                <td class="admin-only d-none"><small>${this.formatDateTime(ds.valid_to)}</small></td>
            `;

            const row = document.createElement('tr');
            row.className = this.dataSourcesAdminMode ? rowClass : '';
            
            row.innerHTML = `
                <td>${ds.id}${versionIndicator}</td>
                <td><strong>${ds.name}</strong></td>
                <td><span class="badge bg-primary">${ds.provider}</span></td>
                <td>${ds.description || 'N/A'}</td>
                <td style="max-width: 300px;"><div style="max-height: 60px; overflow-y: auto;">${attributesDisplay}</div></td>
                ${adminColumns}
                <td style="min-width: 120px;">
                    <button class="btn btn-sm btn-outline-info me-1" onclick="viewDataSource(${ds.id})" title="View Details">
                        <i class="fas fa-info-circle"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning me-1" onclick="editDataSource(${ds.id})" title="Edit Data Source">
                        <i class="fas fa-edit"></i>
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

    // Helper functions for edit forms
    populateEditAssetAttributes(attributes) {
        const container = document.getElementById('editAssetAttributesContainer');
        container.innerHTML = '';
        
        // Get non-default attributes (exclude symbol, type, exchange)
        const defaultKeys = ['symbol', 'type', 'exchange'];
        const additionalAttributes = Object.entries(attributes || {})
            .filter(([key]) => !defaultKeys.includes(key));
        
        if (additionalAttributes.length === 0) {
            // Add one empty pair
            this.addEditAssetAttribute();
        } else {
            // Add pairs for each additional attribute
            additionalAttributes.forEach(([key, value]) => {
                const attributeDiv = document.createElement('div');
                attributeDiv.className = 'edit-asset-attribute-pair mb-2';
                attributeDiv.innerHTML = `
                    <div class="row align-items-center">
                        <div class="col-5">
                            <input type="text" class="form-control edit-asset-attribute-key" placeholder="Key" value="${key}">
                        </div>
                        <div class="col-5">
                            <input type="text" class="form-control edit-asset-attribute-value" placeholder="Value" value="${value}">
                        </div>
                        <div class="col-2">
                            <button type="button" class="btn btn-outline-danger btn-sm" onclick="app.removeEditAssetAttribute(this)">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
                container.appendChild(attributeDiv);
            });
        }
    }

    populateEditDataSourceAttributes(attributes) {
        const container = document.getElementById('editDataSourceAttributesContainer');
        container.innerHTML = '';
        
        if (Object.keys(attributes || {}).length === 0) {
            // Add one empty pair
            this.addEditDataSourceAttribute();
        } else {
            // Add pairs for each attribute
            Object.entries(attributes).forEach(([key, value]) => {
                const attributeDiv = document.createElement('div');
                attributeDiv.className = 'edit-datasource-attribute-pair mb-2';
                attributeDiv.innerHTML = `
                    <div class="row align-items-center">
                        <div class="col-5">
                            <input type="text" class="form-control edit-datasource-attribute-key" placeholder="Key" value="${key}">
                        </div>
                        <div class="col-5">
                            <input type="text" class="form-control edit-datasource-attribute-value" placeholder="Value" value="${value}">
                        </div>
                        <div class="col-2">
                            <button type="button" class="btn btn-outline-danger btn-sm" onclick="app.removeEditDataSourceAttribute(this)">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
                container.appendChild(attributeDiv);
            });
        }
    }

    collectEditAssetAttributes() {
        const attributes = {};
        const attributePairs = document.querySelectorAll('.edit-asset-attribute-pair');
        
        attributePairs.forEach(pair => {
            const key = pair.querySelector('.edit-asset-attribute-key').value.trim();
            const value = pair.querySelector('.edit-asset-attribute-value').value.trim();
            
            if (key && value) {
                attributes[key] = value;
            }
        });
        
        return attributes;
    }

    collectEditDataSourceAttributes() {
        const attributes = {};
        const attributePairs = document.querySelectorAll('.edit-datasource-attribute-pair');
        
        attributePairs.forEach(pair => {
            const key = pair.querySelector('.edit-datasource-attribute-key').value.trim();
            const value = pair.querySelector('.edit-datasource-attribute-value').value.trim();
            
            if (key && value) {
                attributes[key] = value;
            }
        });
        
        return attributes;
    }

    // Add/remove methods for edit forms
    addEditAssetAttribute() {
        const container = document.getElementById('editAssetAttributesContainer');
        const newAttribute = document.createElement('div');
        newAttribute.className = 'edit-asset-attribute-pair mb-2';
        newAttribute.innerHTML = `
            <div class="row align-items-center">
                <div class="col-5">
                    <input type="text" class="form-control edit-asset-attribute-key" placeholder="Key">
                </div>
                <div class="col-5">
                    <input type="text" class="form-control edit-asset-attribute-value" placeholder="Value">
                </div>
                <div class="col-2">
                    <button type="button" class="btn btn-outline-danger btn-sm" onclick="app.removeEditAssetAttribute(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        container.appendChild(newAttribute);
    }

    removeEditAssetAttribute(button) {
        const container = document.getElementById('editAssetAttributesContainer');
        const attributePair = button.closest('.edit-asset-attribute-pair');
        
        if (container.children.length > 1) {
            attributePair.remove();
        } else {
            // Clear the inputs instead
            attributePair.querySelector('.edit-asset-attribute-key').value = '';
            attributePair.querySelector('.edit-asset-attribute-value').value = '';
        }
    }

    addEditDataSourceAttribute() {
        const container = document.getElementById('editDataSourceAttributesContainer');
        const newAttribute = document.createElement('div');
        newAttribute.className = 'edit-datasource-attribute-pair mb-2';
        newAttribute.innerHTML = `
            <div class="row align-items-center">
                <div class="col-5">
                    <input type="text" class="form-control edit-datasource-attribute-key" placeholder="Key">
                </div>
                <div class="col-5">
                    <input type="text" class="form-control edit-datasource-attribute-value" placeholder="Value">
                </div>
                <div class="col-2">
                    <button type="button" class="btn btn-outline-danger btn-sm" onclick="app.removeEditDataSourceAttribute(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        container.appendChild(newAttribute);
    }

    removeEditDataSourceAttribute(button) {
        const container = document.getElementById('editDataSourceAttributesContainer');
        const attributePair = button.closest('.edit-datasource-attribute-pair');
        
        if (container.children.length > 1) {
            attributePair.remove();
        } else {
            // Clear the inputs instead
            attributePair.querySelector('.edit-datasource-attribute-key').value = '';
            attributePair.querySelector('.edit-datasource-attribute-value').value = '';
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
            
            // Check if we have pending prefill values
            if (this.pendingTimeSeriesPrefill) {
                const { assetId, dataSourceId } = this.pendingTimeSeriesPrefill;
                
                // Wait a bit for DOM to update, then prefill
                setTimeout(async () => {
                    const assetSelect = document.getElementById('timeseries-asset');
                    const dataSourceSelect = document.getElementById('timeseries-datasource');
                    
                    if (assetSelect && dataSourceSelect) {
                        assetSelect.value = assetId;
                        dataSourceSelect.value = dataSourceId;
                        
                        // Automatically load the data
                        await this.loadTimeSeriesData();
                        
                        this.showToast('Success', 'Time series data loaded for selected asset', 'success');
                    }
                }, 100);
            }
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
            const assets = await this.apiCall('/assets');
            this.populateSelect('ingest-asset', assets, 'id', 'name');
            
            // Remove any existing event listeners first
            const assetSelect = document.getElementById('ingest-asset');
            const existingListener = assetSelect.cloneNode(true);
            assetSelect.parentNode.replaceChild(existingListener, assetSelect);
            
            // Add event listener for asset selection to update data sources
            document.getElementById('ingest-asset').addEventListener('change', async (e) => {
                await this.updateDataSourcesForAsset(e.target.value);
            });
            
            // Initially populate with all Nasdaq data sources
            await this.loadNasdaqDataSources();
            
        } catch (error) {
            console.error('Failed to populate ingestion selects:', error);
        }
    }

    async loadNasdaqDataSources(selectedAssetId = null) {
        try {
            const dataSources = await this.apiCall('/data-sources');
            
            // Filter for Nasdaq-related data sources (including "Nasdaq Data Link")
            let nasdaqDataSources = dataSources.filter(ds => 
                ds.provider?.toLowerCase().includes('nasdaq')
            );
            
            if (nasdaqDataSources.length === 0) {
                console.log('No Nasdaq-related sources found, showing all data sources');
                nasdaqDataSources = dataSources; // Show all if no Nasdaq sources found
            }
            
            const select = document.getElementById('ingest-datasource');
            select.innerHTML = '<option value="">Select Data Source</option>';
            
            if (selectedAssetId) {
                // Get existing data source IDs for this asset
                try {
                    const response = await this.apiCall(`/ingest/compatible-data-sources/${selectedAssetId}`);
                    const compatibleSources = response.data || [];
                    const existingDataSourceIds = compatibleSources
                        .filter(ds => ds.has_existing_data)
                        .map(ds => ds.id);
                    
                    if (existingDataSourceIds.length > 0) {
                        // Asset has existing data - show only the data sources that have data
                        const sourcesWithData = nasdaqDataSources.filter(ds => existingDataSourceIds.includes(ds.id));
                        this.populateSelect('ingest-datasource', sourcesWithData, 'id', (ds) => {
                            return `${ds.name} (has data)`;
                        });
                    } else {
                        // Asset has no existing data - show all Nasdaq sources
                        this.populateSelect('ingest-datasource', nasdaqDataSources, 'id', 'name');
                    }
                } catch (error) {
                    // Fallback to showing all Nasdaq sources
                    console.warn('Could not check data compatibility, showing all sources:', error);
                    this.populateSelect('ingest-datasource', nasdaqDataSources, 'id', 'name');
                }
            } else {
                // No asset selected, show all Nasdaq sources normally
                this.populateSelect('ingest-datasource', nasdaqDataSources, 'id', 'name');
            }
            
        } catch (error) {
            console.error('Failed to load Nasdaq data sources:', error);
            const select = document.getElementById('ingest-datasource');
            select.innerHTML = '<option value="">Error loading data sources</option>';
        }
    }

    async updateDataSourcesForAsset(assetId) {
        await this.loadNasdaqDataSources(assetId);
    }

    async handleDataIngestion(e) {
        e.preventDefault();
        
        const forceRefresh = document.getElementById('force-refresh').checked;
        const ingestionData = {
            asset_id: parseInt(document.getElementById('ingest-asset').value),
            data_source_id: parseInt(document.getElementById('ingest-datasource').value),
            start_date: document.getElementById('ingest-start-date').value,
            end_date: document.getElementById('ingest-end-date').value
        };

        const progressDiv = document.getElementById('ingestion-progress');
        const progressBar = progressDiv.querySelector('.progress-bar');
        const progressText = progressDiv.querySelector('small');
        const submitBtn = document.querySelector('#ingest-form button[type="submit"]');
        
        try {
            // Reset progress bar
            progressBar.style.width = '0%';
            progressBar.textContent = '0%';
            progressText.textContent = 'Starting ingestion...';
            
            // Show progress and disable submit button
            progressDiv.style.display = 'block';
            submitBtn.disabled = true;
            
            // Choose endpoint based on force refresh option
            const endpoint = forceRefresh ? '/ingest/nasdaq/refresh' : '/ingest/nasdaq';
            const response = await this.apiCall(endpoint, 'POST', ingestionData);
            
            // Store session ID for progress tracking
            if (response.session_id) {
                this.currentIngestionSession = response.session_id;
                console.log('Set current ingestion session:', this.currentIngestionSession); // Debug log
                progressText.textContent = 'Ingestion started, waiting for progress updates...';
            } else {
                // Fallback for older API response without session_id
                const message = forceRefresh ? 
                    'Data refresh completed with temporal versioning!' : 
                    'Data ingestion completed successfully!';
                    
                this.showToast('Success', message, 'success');
                document.getElementById('ingest-form').reset();
                
                // Refresh the status table
                await this.loadIngestionStatus();
                
                // Hide progress
                progressDiv.style.display = 'none';
                submitBtn.disabled = false;
            }
            
        } catch (error) {
            console.error('Failed to ingest data:', error);
            const errorMessage = forceRefresh ? 'Failed to refresh data' : 'Failed to ingest data';
            this.showToast('Error', errorMessage, 'error');
            
            // Hide progress and re-enable submit button
            progressDiv.style.display = 'none';
            submitBtn.disabled = false;
            this.currentIngestionSession = null;
        }
    }

    // WebSocket Management
    initWebSocket() {
        // Prevent multiple WebSocket connections
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            return;
        }
        
        try {
            const wsUrl = this.baseURL.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws';
            console.log('Connecting to WebSocket:', wsUrl);
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected for real-time updates');
                this.websocketReconnectAttempts = 0;
                this.websocketConnected = true;
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleProgressUpdate(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e, event.data);
                }
            };
            
            this.websocket.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                this.websocketConnected = false;
                
                // Auto-reconnect only if we have an active ingestion session
                if (this.currentIngestionSession && this.websocketReconnectAttempts < 3) {
                    this.websocketReconnectAttempts = (this.websocketReconnectAttempts || 0) + 1;
                    console.log(`WebSocket reconnection attempt ${this.websocketReconnectAttempts}/3`);
                    setTimeout(() => this.initWebSocket(), 1000 * this.websocketReconnectAttempts);
                } else if (this.currentIngestionSession) {
                    console.log('WebSocket reconnection limit reached, using polling fallback');
                    this.startProgressPolling();
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.websocketConnected = false;
            };
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
            this.websocketConnected = false;
            if (this.currentIngestionSession) {
                this.startProgressPolling();
            }
        }
    }

    // Fallback when WebSocket connection fails - use polling
    startProgressPolling() {
        if (!this.currentIngestionSession) return;
        
        console.log('Starting progress polling for session:', this.currentIngestionSession);
        
        this.pollInterval = setInterval(async () => {
            try {
                // Poll ingestion status to check completion
                const response = await this.apiCall(`/ingest/status?session_id=${this.currentIngestionSession}`);
                
                if (response.status === 'complete') {
                    this.handleIngestionComplete(true, response.message || 'Ingestion completed');
                    clearInterval(this.pollInterval);
                } else if (response.status === 'error') {
                    this.handleIngestionError(response.message || 'Ingestion failed');
                    clearInterval(this.pollInterval);
                } else {
                    // Update progress if available
                    const progress = response.progress || 50; // Default progress
                    this.updateProgressBar(progress, response.message || 'Processing...');
                }
            } catch (error) {
                console.error('Polling error:', error);
                // After several failed polls, assume completion
                this.pollFailures = (this.pollFailures || 0) + 1;
                if (this.pollFailures >= 5) {
                    this.handleIngestionComplete(true, 'Ingestion completed (polling timeout)');
                    clearInterval(this.pollInterval);
                }
            }
        }, 2000); // Poll every 2 seconds
        
        // Timeout after 5 minutes
        setTimeout(() => {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
                this.handleIngestionComplete(true, 'Ingestion completed (timeout)');
            }
        }, 300000);
    }

    handleProgressUpdate(data) {
        console.log('Received progress update:', data); // Debug log
        
        if (data.type === 'progress_update') {
            const stage = data.data.stage;
            const progress = data.data.progress || 0;
            const message = data.data.message || 'Processing...';
            
            console.log(`Progress update: ${progress}% - ${message} (stage: ${stage}, session: ${data.session_id})`); // Debug log
            
            // If we don't have a current session, or if this is a new session, accept it
            if (!this.currentIngestionSession || data.session_id === this.currentIngestionSession) {
                console.log('Processing message for session:', data.session_id);
                
                // Update current session if not set
                if (!this.currentIngestionSession) {
                    this.currentIngestionSession = data.session_id;
                    console.log('Updated current session to:', this.currentIngestionSession);
                }
                
                if (stage === 'complete') {
                    this.handleIngestionComplete(true, message);
                } else if (stage === 'error') {
                    this.handleIngestionError(message);
                } else {
                    this.updateProgressBar(progress, message);
                }
            } else {
                console.log('Ignoring message - session mismatch:', {
                    received_session: data.session_id,
                    current_session: this.currentIngestionSession,
                    type: data.type
                });
            }
        } else {
            console.log('Ignoring message - unknown type:', data.type);
        }
    }

    updateProgressBar(progress, message) {
        const progressDiv = document.getElementById('ingestion-progress');
        const progressBar = progressDiv.querySelector('.progress-bar');
        const progressText = progressDiv.querySelector('small');
        
        // Update progress bar
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${Math.round(progress)}%`;
        
        // Update message
        if (message) {
            progressText.textContent = message;
        }
        
        // Show progress if hidden
        if (progressDiv.style.display === 'none') {
            progressDiv.style.display = 'block';
        }
    }

    handleIngestionComplete(success, message) {
        const progressDiv = document.getElementById('ingestion-progress');
        const submitBtn = document.querySelector('#ingest-form button[type="submit"]');
        
        // Clear any active polling
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
        
        if (success) {
            this.showToast('Success', message || 'Data ingestion completed successfully!', 'success');
            document.getElementById('ingest-form').reset();
            // Refresh the status table
            this.loadIngestionStatus();
        } else {
            this.showToast('Error', message || 'Data ingestion failed', 'error');
        }
        
        // Hide progress and re-enable submit button
        progressDiv.style.display = 'none';
        submitBtn.disabled = false;
        this.currentIngestionSession = null;
        this.pollFailures = 0;
    }

    handleIngestionError(message) {
        const progressDiv = document.getElementById('ingestion-progress');
        const submitBtn = document.querySelector('#ingest-form button[type="submit"]');
        
        this.showToast('Error', message || 'Data ingestion failed', 'error');
        
        // Hide progress and re-enable submit button
        progressDiv.style.display = 'none';
        submitBtn.disabled = false;
        this.currentIngestionSession = null;
    }

    // Admin Mode Functions
    toggleAssetsAdminMode() {
        this.assetsAdminMode = document.getElementById('assets-admin-mode').checked;
        
        // Toggle admin-only columns visibility
        const adminColumns = document.querySelectorAll('#assets-table .admin-only');
        adminColumns.forEach(col => {
            if (this.assetsAdminMode) {
                col.classList.remove('d-none');
            } else {
                col.classList.add('d-none');
            }
        });
        
        // Reload assets with appropriate data
        this.loadAssets();
    }

    toggleDataSourcesAdminMode() {
        this.dataSourcesAdminMode = document.getElementById('datasources-admin-mode').checked;
        
        // Toggle admin-only columns visibility
        const adminColumns = document.querySelectorAll('#datasources-table .admin-only');
        adminColumns.forEach(col => {
            if (this.dataSourcesAdminMode) {
                col.classList.remove('d-none');
            } else {
                col.classList.add('d-none');
            }
        });
        
        // Reload data sources with appropriate data
        this.loadDataSources();
    }

    formatDateTime(dateTime) {
        if (!dateTime) return '<span class="text-muted">N/A</span>';
        try {
            return new Date(dateTime).toLocaleString();
        } catch (e) {
            console.error('Error formatting date:', dateTime, e);
            return '<span class="text-danger">Invalid Date</span>';
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
            
            // Handle both string field names and functions
            if (typeof textField === 'function') {
                optionElement.textContent = textField(option);
            } else {
                optionElement.textContent = option[textField];
            }
            
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

    // Edit data source functionality
    async editDataSource(dataSourceId) {
        try {
            const dataSource = await this.apiCall(`/data-sources/${dataSourceId}`);
            
            // Populate edit form with current data source data
            document.getElementById('edit-datasource-id').value = dataSource.id;
            document.getElementById('edit-datasource-name').value = dataSource.name;
            document.getElementById('edit-datasource-provider').value = dataSource.provider;
            document.getElementById('edit-datasource-description').value = dataSource.description || '';
            
            // Populate additional attributes
            this.populateEditDataSourceAttributes(dataSource.attributes);
            
            // Show edit modal
            new bootstrap.Modal(document.getElementById('editDataSourceModal')).show();
        } catch (error) {
            console.error('Failed to load data source for editing:', error);
            this.showToast('Error', 'Failed to load data source for editing', 'error');
        }
    }

    // Handle edit data source form submission
    async handleEditDataSource(e) {
        e.preventDefault();
        
        const dataSourceId = document.getElementById('edit-datasource-id').value;
        
        // Collect additional attributes from dynamic form
        const additionalAttributes = this.collectEditDataSourceAttributes();
        
        const dataSourceData = {
            name: document.getElementById('edit-datasource-name').value,
            provider: document.getElementById('edit-datasource-provider').value,
            description: document.getElementById('edit-datasource-description').value,
            attributes: additionalAttributes
        };

        try {
            await this.apiCall(`/data-sources/${dataSourceId}`, 'PUT', dataSourceData);
            this.showToast('Success', 'Data source updated successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editDataSourceModal')).hide();
            await this.loadDataSources();
        } catch (error) {
            console.error('Failed to update data source:', error);
            this.showToast('Error', 'Failed to update data source. Please try again.', 'error');
        }
    }

    // Data Ingestion Status
    async loadIngestionStatus() {
        try {
            const response = await this.apiCall('/ingest/status');
            const statusData = response.data || [];
            
            const tbody = document.querySelector('#ingestion-status-table tbody');
            const noDataMessage = document.getElementById('no-data-message');
            
            if (statusData.length === 0) {
                tbody.innerHTML = '';
                noDataMessage.style.display = 'block';
                return;
            }
            
            noDataMessage.style.display = 'none';
            tbody.innerHTML = statusData.map(item => `
                <tr>
                    <td>
                        <strong>${item.asset_name}</strong><br>
                        <small class="text-muted">${item.asset_symbol || 'N/A'}</small>
                    </td>
                    <td>
                        <strong>${item.data_source_name}</strong><br>
                        <small class="text-muted">${item.data_source_provider}</small>
                    </td>
                    <td>
                        ${item.coverage_start} to ${item.coverage_end}
                    </td>
                    <td>
                        <span class="badge bg-primary">${item.total_days} days</span>
                    </td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="app.extendCoverage(${item.asset_id}, ${item.data_source_id}, '${item.coverage_end}')" title="Extend coverage">
                                <i class="fas fa-plus"></i>
                            </button>
                            <button class="btn btn-outline-success" onclick="app.refreshData(${item.asset_id}, ${item.data_source_id}, '${item.coverage_start}', '${item.coverage_end}')" title="Refresh data">
                                <i class="fas fa-sync"></i>
                            </button>
                            <button class="btn btn-outline-info" onclick="app.viewTimeSeries(${item.asset_id}, ${item.data_source_id})" title="View time series">
                                <i class="fas fa-chart-line"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
            
        } catch (error) {
            console.error('Failed to load ingestion status:', error);
            this.showToast('Error', 'Failed to load ingestion status', 'error');
        }
    }

    async refreshIngestionStatus() {
        await this.loadIngestionStatus();
        this.showToast('Success', 'Ingestion status refreshed', 'success');
    }

    async extendCoverage(assetId, dataSourceId, currentEndDate) {
        try {
            // Switch to the ingestion tab
            this.showSection('ingest');
            
            // Wait a bit for the section to load
            await new Promise(resolve => setTimeout(resolve, 200));
            
            // Prefill the form
            document.getElementById('ingest-asset').value = assetId;
            
            // Update data sources for the asset and then select the specific one
            await this.updateDataSourcesForAsset(assetId);
            document.getElementById('ingest-datasource').value = dataSourceId;
            
            // Set start date to the day after current end date
            const nextDay = new Date(currentEndDate);
            nextDay.setDate(nextDay.getDate() + 1);
            document.getElementById('ingest-start-date').value = nextDay.toISOString().split('T')[0];
            
            // Set end date to today
            const today = new Date();
            document.getElementById('ingest-end-date').value = today.toISOString().split('T')[0];
            
            // Don't check force refresh for extension
            document.getElementById('force-refresh').checked = false;
            
            // Scroll to the form
            document.getElementById('ingest-form').scrollIntoView({ behavior: 'smooth' });
            
            this.showToast('Info', `Form prefilled to extend coverage from ${nextDay.toISOString().split('T')[0]}`, 'info');
            
        } catch (error) {
            console.error('Error extending coverage:', error);
            this.showToast('Error', 'Failed to prefill extension form', 'error');
        }
    }

    async refreshData(assetId, dataSourceId, startDate, endDate) {
        if (!confirm('This will refresh all data in the coverage period using temporal versioning. Are you sure?')) {
            return;
        }
        
        try {
            const refreshData = {
                asset_id: assetId,
                data_source_id: dataSourceId,
                start_date: startDate,
                end_date: endDate
            };
            
            const progressDiv = document.getElementById('ingestion-progress');
            progressDiv.style.display = 'block';
            
            await this.apiCall('/ingest/nasdaq/refresh', 'POST', refreshData);
            
            this.showToast('Success', 'Data refresh completed successfully!', 'success');
            
            // Reload the status table
            await this.loadIngestionStatus();
            
        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.showToast('Error', 'Failed to refresh data: ' + (error.message || 'Unknown error'), 'error');
        } finally {
            document.getElementById('ingestion-progress').style.display = 'none';
        }
    }

    // View time series from ingestion status
    async viewTimeSeries(assetId, dataSourceId) {
        try {
            // Store the values to prefill after section load
            this.pendingTimeSeriesPrefill = { assetId, dataSourceId };
            
            // Switch to time series tab
            this.showSection('timeseries');
            
            // Clear the pending prefill after a short delay to allow for proper prefill
            setTimeout(() => {
                this.pendingTimeSeriesPrefill = null;
            }, 1000);
            
        } catch (error) {
            console.error('Error viewing time series:', error);
            this.showToast('Error', 'Failed to load time series data', 'error');
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

// Make editAsset function globally available for onclick handlers
window.editAsset = (assetId) => {
    if (window.app) {
        window.app.editAsset(assetId);
    }
};

// Make deleteDataSource function globally available for onclick handlers
window.deleteDataSource = (dataSourceId) => {
    if (window.app) {
        window.app.deleteDataSource(dataSourceId);
    }
};

// Make viewDataSource function globally available for onclick handlers
window.viewDataSource = (dataSourceId) => {
    if (window.app) {
        window.app.viewDataSource(dataSourceId);
    }
};

// Make editDataSource function globally available for onclick handlers
window.editDataSource = (dataSourceId) => {
    if (window.app) {
        window.app.editDataSource(dataSourceId);
    } else {
        console.error('App instance not found!');
    }
};

// Make admin mode toggle functions globally available
window.toggleAssetsAdminMode = () => {
    if (window.app) {
        window.app.toggleAssetsAdminMode();
    }
};

window.toggleDataSourcesAdminMode = () => {
    if (window.app) {
        window.app.toggleDataSourcesAdminMode();
    }
};
