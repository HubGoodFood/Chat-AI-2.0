// 管理员页面JavaScript - 版本: 20250101-4 (操作日志翻译修复版)
console.log('🔄 Admin.js 加载完成 - 版本: 20250101-4');

class AdminDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.inventoryData = [];
        this.feedbackData = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
        this.initializeFromURL();
    }

    setupEventListeners() {
        // 侧边栏菜单点击
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.switchSection(section);
            });
        });

        // 退出登录
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.logout();
        });

        // 搜索功能
        document.getElementById('searchInventoryBtn')?.addEventListener('click', () => {
            this.searchInventory();
        });

        document.getElementById('searchFeedbackBtn')?.addEventListener('click', () => {
            this.searchFeedback();
        });

        // 过滤器
        document.getElementById('categoryFilter')?.addEventListener('change', () => {
            this.filterInventory();
        });

        document.getElementById('statusFilter')?.addEventListener('change', () => {
            this.filterInventory();
        });

        document.getElementById('feedbackTypeFilter')?.addEventListener('change', () => {
            this.filterFeedback();
        });

        document.getElementById('feedbackStatusFilter')?.addEventListener('change', () => {
            this.filterFeedback();
        });

        // 添加按钮
        document.getElementById('addProductBtn')?.addEventListener('click', () => {
            this.showAddProductModal();
        });

        document.getElementById('addFeedbackBtn')?.addEventListener('click', () => {
            this.showAddFeedbackModal();
        });

        // 修改密码表单
        document.getElementById('changePasswordForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.changePassword();
        });

        // 刷新日志按钮
        document.getElementById('refreshLogsBtn')?.addEventListener('click', () => {
            this.loadLogsData();
        });

        // 日志过滤器
        document.getElementById('logOperatorFilter')?.addEventListener('change', () => {
            this.filterLogs();
        });

        document.getElementById('logOperationFilter')?.addEventListener('change', () => {
            this.filterLogs();
        });

        document.getElementById('logTargetFilter')?.addEventListener('change', () => {
            this.filterLogs();
        });

        document.getElementById('logLimitInput')?.addEventListener('change', () => {
            this.filterLogs();
        });

        // 模态框关闭
        document.querySelector('.close')?.addEventListener('click', () => {
            this.closeModal();
        });

        // 点击模态框外部关闭
        document.getElementById('modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'modal') {
                this.closeModal();
            }
        });

        // 新页面事件监听器
        this.setupNewPagesEventListeners();
    }

    async checkAuthStatus() {
        try {
            const response = await fetch('/api/admin/status');
            const result = await response.json();

            if (!result.authenticated) {
                window.location.href = '/admin/login';
                return;
            }

            document.getElementById('adminUsername').textContent = result.username || '管理员';
        } catch (error) {
            console.error('检查认证状态失败:', error);
            window.location.href = '/admin/login';
        }
    }

    initializeFromURL() {
        // 检查URL路径，确定要显示的section
        const path = window.location.pathname;
        let defaultSection = 'dashboard';

        if (path.includes('/admin/inventory/products/add')) {
            defaultSection = 'inventory-add-product';
        } else if (path.includes('/admin/inventory/counts')) {
            defaultSection = 'inventory-counts';
        } else if (path.includes('/admin/inventory/analysis')) {
            defaultSection = 'inventory-analysis';
        }

        // 如果模板传递了默认section参数，优先使用
        const templateSection = document.body.dataset.defaultSection;
        if (templateSection) {
            defaultSection = templateSection;
        }

        // 切换到对应的section
        this.switchSection(defaultSection);
    }

    switchSection(section) {
        // 更新菜单状态
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).classList.add('active');

        // 切换内容区域
        document.querySelectorAll('.content-section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`${section}Section`).classList.add('active');

        this.currentSection = section;

        // 加载对应数据
        switch (section) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'inventory':
                this.loadInventoryData();
                break;
            case 'inventory-add-product':
                this.loadAddProductPage();
                break;
            case 'inventory-counts':
                this.loadInventoryCountsPage();
                break;
            case 'inventory-analysis':
                this.loadInventoryAnalysisPage();
                break;
            case 'feedback':
                this.loadFeedbackData();
                break;
            case 'logs':
                this.loadLogsData();
                break;
            case 'export':
                // 导出页面不需要加载数据
                break;
        }
    }

    async loadDashboardData() {
        try {
            // 加载库存统计
            const inventoryResponse = await fetch('/api/admin/inventory/summary');
            const inventoryStats = await inventoryResponse.json();
            
            if (inventoryStats.success) {
                document.getElementById('totalProducts').textContent = inventoryStats.data.total_products;
                document.getElementById('lowStockCount').textContent = inventoryStats.data.low_stock_count;
            }

            // 加载反馈统计
            const feedbackResponse = await fetch('/api/admin/feedback/statistics');
            const feedbackStats = await feedbackResponse.json();
            
            if (feedbackStats.success) {
                document.getElementById('totalFeedback').textContent = feedbackStats.data.total_feedback;
                document.getElementById('pendingFeedback').textContent = feedbackStats.data.pending_feedback;
            }

            // 加载库存状态
            this.loadInventoryStatus();
            
            // 加载最新反馈
            this.loadRecentFeedback();

        } catch (error) {
            console.error('加载控制台数据失败:', error);
        }
    }

    async loadInventoryStatus() {
        try {
            const response = await fetch('/api/admin/inventory/low-stock');
            const result = await response.json();
            
            const statusDiv = document.getElementById('inventoryStatus');
            
            if (result.success && result.data.length > 0) {
                let html = '<div class="low-stock-list">';
                result.data.slice(0, 5).forEach(product => {
                    html += `
                        <div class="low-stock-item">
                            <span class="product-name">${product.product_name}</span>
                            <span class="stock-count">${product.current_stock}</span>
                        </div>
                    `;
                });
                html += '</div>';
                statusDiv.innerHTML = html;
            } else {
                statusDiv.innerHTML = `<p class="no-data">✅ ${_('所有产品库存充足')}</p>`;
            }
        } catch (error) {
            console.error('加载库存状态失败:', error);
            document.getElementById('inventoryStatus').innerHTML = `<p class="error">${_('加载失败')}</p>`;
        }
    }

    async loadRecentFeedback() {
        try {
            const response = await fetch('/api/admin/feedback/recent');
            const result = await response.json();
            
            const feedbackDiv = document.getElementById('recentFeedback');
            
            if (result.success && result.data.length > 0) {
                let html = '<div class="recent-feedback-list">';
                result.data.slice(0, 5).forEach(feedback => {
                    const typeClass = feedback.feedback_type === 'positive' ? 'feedback-positive' : 'feedback-negative';
                    const typeText = feedback.feedback_type === 'positive' ? _('正面') : _('负面');
                    
                    html += `
                        <div class="feedback-item">
                            <div class="feedback-header">
                                <span class="product-name">${feedback.product_name}</span>
                                <span class="${typeClass}">${typeText}</span>
                            </div>
                            <div class="feedback-meta">
                                <span>${feedback.customer_wechat_name}</span>
                                <span>${new Date(feedback.feedback_time).toLocaleDateString()}</span>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                feedbackDiv.innerHTML = html;
            } else {
                feedbackDiv.innerHTML = `<p class="no-data">${_('暂无最新反馈')}</p>`;
            }
        } catch (error) {
            console.error('加载最新反馈失败:', error);
            document.getElementById('recentFeedback').innerHTML = `<p class="error">${_('加载失败')}</p>`;
        }
    }

    async loadInventoryData() {
        try {
            const response = await fetch('/api/admin/inventory');
            const result = await response.json();
            
            if (result.success) {
                this.inventoryData = result.data;
                this.renderInventoryTable(this.inventoryData);
                this.loadCategoryFilter();
            } else {
                this.showError('加载库存数据失败');
            }
        } catch (error) {
            console.error('加载库存数据失败:', error);
            this.showError(_('网络错误'));
        }
    }

    renderInventoryTable(data) {
        const tbody = document.getElementById('inventoryTableBody');
        
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="no-data">${_('暂无库存数据')}</td></tr>`;
            return;
        }

        let html = '';
        data.forEach(product => {
            const statusClass = product.status === 'active' ? 'status-active' : 'status-inactive';
            const statusText = product.status === 'active' ? _('正常') : _('停用');
            const lowStock = product.current_stock <= product.min_stock_warning;
            
            html += `
                <tr ${lowStock ? 'class="low-stock-row"' : ''}>
                    <td>
                        ${product.product_name}
                        ${lowStock ? '<span class="low-stock-warning">⚠️</span>' : ''}
                    </td>
                    <td>${product.category}</td>
                    <td>${product.price}</td>
                    <td>
                        <span class="stock-count ${lowStock ? 'low-stock' : ''}">${product.current_stock}</span>
                        <span class="stock-unit">${product.unit}</span>
                    </td>
                    <td><span class="${statusClass}">${statusText}</span></td>
                    <td>
                        <button class="secondary-btn" onclick="admin.editProduct('${product.product_id}')">${_('编辑')}</button>
                        <button class="secondary-btn" onclick="admin.adjustStock('${product.product_id}')">${_('调库存')}</button>
                        <button class="danger-btn" onclick="admin.deleteProduct('${product.product_id}')">${_('删除')}</button>
                    </td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
    }

    async loadFeedbackData() {
        try {
            const response = await fetch('/api/admin/feedback');
            const result = await response.json();
            
            if (result.success) {
                this.feedbackData = result.data;
                this.renderFeedbackTable(this.feedbackData);
            } else {
                this.showError('加载反馈数据失败');
            }
        } catch (error) {
            console.error('加载反馈数据失败:', error);
            this.showError(_('网络错误'));
        }
    }

    renderFeedbackTable(data) {
        const tbody = document.getElementById('feedbackTableBody');
        
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="no-data">${_('暂无反馈数据')}</td></tr>`;
            return;
        }

        let html = '';
        data.forEach(feedback => {
            const typeClass = feedback.feedback_type === 'positive' ? 'feedback-positive' : 'feedback-negative';
            const typeText = feedback.feedback_type === 'positive' ? _('正面反馈') : _('负面反馈');
            
            let statusClass = 'status-pending';
            if (feedback.processing_status === '处理中') statusClass = 'status-processing';
            if (feedback.processing_status === '已解决') statusClass = 'status-resolved';
            
            html += `
                <tr>
                    <td>${feedback.product_name}</td>
                    <td>${feedback.customer_wechat_name}</td>
                    <td><span class="${typeClass}">${typeText}</span></td>
                    <td>${feedback.payment_status}</td>
                    <td><span class="${statusClass}">${feedback.processing_status}</span></td>
                    <td>${new Date(feedback.feedback_time).toLocaleString()}</td>
                    <td>
                        <button class="secondary-btn" onclick="admin.viewFeedback('${feedback.feedback_id}')">${_('查看')}</button>
                        <button class="secondary-btn" onclick="admin.processFeedback('${feedback.feedback_id}')">${_('处理')}</button>
                        <button class="danger-btn" onclick="admin.deleteFeedback('${feedback.feedback_id}')">${_('删除')}</button>
                    </td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
    }

    async logout() {
        try {
            const response = await fetch('/api/admin/logout', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                window.location.href = '/admin/login';
            }
        } catch (error) {
            console.error('退出登录失败:', error);
        }
    }

    showModal(title, content) {
        const modal = document.getElementById('modal');
        const modalBody = document.getElementById('modalBody');

        modalBody.innerHTML = `
            <h2>${title}</h2>
            ${content}
        `;

        modal.style.display = 'block';
    }

    showModalTemplate(templateId) {
        const modal = document.getElementById('modal');
        const modalBody = document.getElementById('modalBody');
        const template = document.getElementById(templateId);

        if (template) {
            modalBody.innerHTML = template.innerHTML;
            modal.style.display = 'block';

            // 绑定表单事件
            this.bindModalEvents(templateId);
        }
    }

    bindModalEvents(templateId) {
        switch (templateId) {
            case 'productModal':
                document.getElementById('productForm')?.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.saveProduct();
                });
                break;
            case 'stockModal':
                document.getElementById('stockForm')?.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.saveStockAdjustment();
                });
                break;
            case 'addFeedbackModal':
                document.getElementById('feedbackForm')?.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.saveFeedback();
                });
                break;
            case 'processFeedbackModal':
                document.getElementById('processFeedbackForm')?.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.saveProcessFeedback();
                });
                break;
        }
    }

    closeModal() {
        document.getElementById('modal').style.display = 'none';
    }

    showError(message) {
        alert(_('错误') + ': ' + message);
    }

    showSuccess(message) {
        alert(_('成功') + ': ' + message);
    }

    showModal(content) {
        const modal = document.getElementById('modal');
        const modalBody = document.getElementById('modalBody');

        if (modal && modalBody) {
            modalBody.innerHTML = content;
            modal.style.display = 'block';

            // 点击模态框外部关闭
            modal.onclick = (e) => {
                if (e.target === modal) {
                    this.hideModal();
                }
            };

            // ESC键关闭
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.hideModal();
                }
            });
        }
    }

    hideModal() {
        const modal = document.getElementById('modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // 库存相关方法
    searchInventory() {
        const keyword = document.getElementById('inventorySearch').value.toLowerCase();
        const filtered = this.inventoryData.filter(product => 
            product.product_name.toLowerCase().includes(keyword) ||
            product.category.toLowerCase().includes(keyword)
        );
        this.renderInventoryTable(filtered);
    }

    filterInventory() {
        const categoryFilter = document.getElementById('categoryFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;
        
        let filtered = this.inventoryData;
        
        if (categoryFilter) {
            filtered = filtered.filter(product => product.category === categoryFilter);
        }
        
        if (statusFilter) {
            filtered = filtered.filter(product => product.status === statusFilter);
        }
        
        this.renderInventoryTable(filtered);
    }

    loadCategoryFilter() {
        const categories = [...new Set(this.inventoryData.map(product => product.category))];
        const select = document.getElementById('categoryFilter');
        
        select.innerHTML = '<option value="">所有分类</option>';
        categories.forEach(category => {
            select.innerHTML += `<option value="${category}">${category}</option>`;
        });
    }

    // 反馈相关方法
    searchFeedback() {
        const keyword = document.getElementById('feedbackSearch').value.toLowerCase();
        const filtered = this.feedbackData.filter(feedback => 
            feedback.product_name.toLowerCase().includes(keyword) ||
            feedback.customer_wechat_name.toLowerCase().includes(keyword) ||
            feedback.feedback_content.toLowerCase().includes(keyword)
        );
        this.renderFeedbackTable(filtered);
    }

    filterFeedback() {
        const typeFilter = document.getElementById('feedbackTypeFilter').value;
        const statusFilter = document.getElementById('feedbackStatusFilter').value;
        
        let filtered = this.feedbackData;
        
        if (typeFilter) {
            filtered = filtered.filter(feedback => feedback.feedback_type === typeFilter);
        }
        
        if (statusFilter) {
            filtered = filtered.filter(feedback => feedback.processing_status === statusFilter);
        }
        
        this.renderFeedbackTable(filtered);
    }

    // 产品管理方法
    showAddProductModal() {
        this.showModalTemplate('productModal');
        document.getElementById('productModalTitle').textContent = _('添加产品');
        document.getElementById('productForm').reset();
    }

    async editProduct(productId) {
        try {
            const response = await fetch(`/api/admin/inventory/${productId}`);
            const result = await response.json();

            if (result.success) {
                this.showModalTemplate('productModal');
                document.getElementById('productModalTitle').textContent = '编辑产品';

                const product = result.data;
                document.getElementById('productName').value = product.product_name;
                document.getElementById('productCategory').value = product.category;
                document.getElementById('productPrice').value = product.price;
                document.getElementById('productUnit').value = product.unit;
                document.getElementById('productSpecification').value = product.specification;
                document.getElementById('minStockWarning').value = product.min_stock_warning;
                document.getElementById('productStatus').value = product.status;
                document.getElementById('productDescription').value = product.description;
                document.getElementById('productImage').value = product.image_url;

                // 存储产品ID用于更新
                document.getElementById('productForm').dataset.productId = productId;
            } else {
                this.showError(result.error || '获取产品信息失败');
            }
        } catch (error) {
            console.error('获取产品信息失败:', error);
            this.showError('网络错误');
        }
    }

    async adjustStock(productId) {
        try {
            const response = await fetch(`/api/admin/inventory/${productId}`);
            const result = await response.json();

            if (result.success) {
                this.showModalTemplate('stockModal');

                const product = result.data;
                document.getElementById('stockProductId').value = productId;
                document.getElementById('stockProductInfo').innerHTML = `
                    <h4>${product.product_name}</h4>
                    <p><strong>当前库存：</strong>${product.current_stock} ${product.unit}</p>
                    <p><strong>最小库存警告：</strong>${product.min_stock_warning} ${product.unit}</p>
                `;
                document.getElementById('stockChange').value = 0;
                document.getElementById('stockNote').value = '';
            } else {
                this.showError(result.error || '获取产品信息失败');
            }
        } catch (error) {
            console.error('获取产品信息失败:', error);
            this.showError('网络错误');
        }
    }

    async deleteProduct(productId) {
        if (confirm(_('确定要删除这个产品吗？此操作将设置产品状态为停用。'))) {
            try {
                const response = await fetch(`/api/admin/inventory/${productId}`, {
                    method: 'DELETE'
                });
                const result = await response.json();

                if (result.success) {
                    this.showSuccess('产品删除成功');
                    this.loadInventoryData();
                } else {
                    this.showError(result.error || '删除产品失败');
                }
            } catch (error) {
                console.error('删除产品失败:', error);
                this.showError('网络错误');
            }
        }
    }

    // 反馈管理方法
    showAddFeedbackModal() {
        this.showModalTemplate('addFeedbackModal');
        document.getElementById('feedbackForm').reset();
    }

    async viewFeedback(feedbackId) {
        try {
            const response = await fetch(`/api/admin/feedback/${feedbackId}`);
            const result = await response.json();

            if (result.success) {
                const feedback = result.data;
                const typeText = feedback.feedback_type === 'positive' ? _('正面反馈') : _('负面反馈');
                const typeClass = feedback.feedback_type === 'positive' ? 'feedback-positive' : 'feedback-negative';

                let customerImages = '';
                if (feedback.customer_images && feedback.customer_images.length > 0) {
                    customerImages = feedback.customer_images.map(img =>
                        `<img src="${img}" alt="客户图片" style="max-width: 200px; margin: 5px;">`
                    ).join('');
                }

                const content = `
                    <div class="feedback-detail">
                        <div class="detail-row">
                            <strong>${_('产品名称')}：</strong>${feedback.product_name}
                        </div>
                        <div class="detail-row">
                            <strong>${_('反馈类型')}：</strong><span class="${typeClass}">${typeText}</span>
                        </div>
                        <div class="detail-row">
                            <strong>${_('客户昵称')}：</strong>${feedback.customer_wechat_name}
                        </div>
                        <div class="detail-row">
                            <strong>${_('客户群号')}：</strong>${feedback.customer_group_number}
                        </div>
                        <div class="detail-row">
                            <strong>${_('付款状态')}：</strong>${feedback.payment_status}
                        </div>
                        <div class="detail-row">
                            <strong>${_('反馈时间')}：</strong>${new Date(feedback.feedback_time).toLocaleString()}
                        </div>
                        <div class="detail-row">
                            <strong>${_('处理状态')}：</strong>${feedback.processing_status}
                        </div>
                        ${feedback.processor ? `<div class="detail-row"><strong>${_('处理人')}：</strong>${feedback.processor}</div>` : ''}
                        <div class="detail-row">
                            <strong>${_('反馈内容')}：</strong>
                            <div style="margin-top: 5px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                                ${feedback.feedback_content}
                            </div>
                        </div>
                        ${feedback.processing_notes ? `
                            <div class="detail-row">
                                <strong>${_('处理备注')}：</strong>
                                <div style="margin-top: 5px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                                    ${feedback.processing_notes}
                                </div>
                            </div>
                        ` : ''}
                        ${customerImages ? `
                            <div class="detail-row">
                                <strong>${_('客户图片')}：</strong>
                                <div style="margin-top: 5px;">
                                    ${customerImages}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;

                this.showModal(_('反馈详情'), content);
            } else {
                this.showError(result.error || '获取反馈详情失败');
            }
        } catch (error) {
            console.error('获取反馈详情失败:', error);
            this.showError('网络错误');
        }
    }

    async processFeedback(feedbackId) {
        try {
            const response = await fetch(`/api/admin/feedback/${feedbackId}`);
            const result = await response.json();

            if (result.success) {
                this.showModalTemplate('processFeedbackModal');

                const feedback = result.data;
                document.getElementById('processFeedbackId').value = feedbackId;
                document.getElementById('processingStatus').value = feedback.processing_status;
                document.getElementById('processingNotes').value = feedback.processing_notes || '';

                document.getElementById('processFeedbackInfo').innerHTML = `
                    <h4>${feedback.product_name}</h4>
                    <p><strong>${_('客户')}：</strong>${feedback.customer_wechat_name}</p>
                    <p><strong>${_('反馈类型')}：</strong>${feedback.feedback_type === 'positive' ? _('正面反馈') : _('负面反馈')}</p>
                    <p><strong>${_('当前状态')}：</strong>${feedback.processing_status}</p>
                `;
            } else {
                this.showError(result.error || '获取反馈信息失败');
            }
        } catch (error) {
            console.error('获取反馈信息失败:', error);
            this.showError('网络错误');
        }
    }

    async deleteFeedback(feedbackId) {
        if (confirm('确定要删除这条反馈吗？此操作不可恢复。')) {
            try {
                const response = await fetch(`/api/admin/feedback/${feedbackId}`, {
                    method: 'DELETE'
                });
                const result = await response.json();

                if (result.success) {
                    this.showSuccess('反馈删除成功');
                    this.loadFeedbackData();
                } else {
                    this.showError(result.error || '删除反馈失败');
                }
            } catch (error) {
                console.error('删除反馈失败:', error);
                this.showError('网络错误');
            }
        }
    }

    // 保存方法
    async saveProduct() {
        try {
            const form = document.getElementById('productForm');
            const formData = new FormData(form);
            const productData = Object.fromEntries(formData.entries());

            // 处理客户图片（将换行分隔的URL转换为数组）
            if (productData.customer_images) {
                productData.customer_images = productData.customer_images.split('\n').filter(url => url.trim());
            }

            const productId = form.dataset.productId;
            const isEdit = !!productId;

            const url = isEdit ? `/api/admin/inventory/${productId}` : '/api/admin/inventory';
            const method = isEdit ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(productData)
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(isEdit ? '产品更新成功' : '产品添加成功');
                this.closeModal();
                this.loadInventoryData();
                this.loadDashboardData();
            } else {
                this.showError(result.error || '保存产品失败');
            }
        } catch (error) {
            console.error('保存产品失败:', error);
            this.showError('网络错误');
        }
    }

    async saveStockAdjustment() {
        try {
            const form = document.getElementById('stockForm');
            const formData = new FormData(form);
            const stockData = Object.fromEntries(formData.entries());

            const productId = stockData.product_id;
            const quantityChange = parseInt(stockData.quantity_change);

            if (quantityChange === 0) {
                this.showError('库存变动不能为0');
                return;
            }

            const response = await fetch(`/api/admin/inventory/${productId}/stock`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    quantity_change: quantityChange,
                    note: stockData.note
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('库存调整成功');
                this.closeModal();
                this.loadInventoryData();
                this.loadDashboardData();
            } else {
                this.showError(result.error || '库存调整失败');
            }
        } catch (error) {
            console.error('库存调整失败:', error);
            this.showError('网络错误');
        }
    }

    async saveFeedback() {
        try {
            const form = document.getElementById('feedbackForm');
            const formData = new FormData(form);
            const feedbackData = Object.fromEntries(formData.entries());

            // 处理客户图片（将换行分隔的URL转换为数组）
            if (feedbackData.customer_images) {
                feedbackData.customer_images = feedbackData.customer_images.split('\n').filter(url => url.trim());
            }

            const response = await fetch('/api/admin/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(feedbackData)
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('反馈添加成功');
                this.closeModal();
                this.loadFeedbackData();
                this.loadDashboardData();
            } else {
                this.showError(result.error || '添加反馈失败');
            }
        } catch (error) {
            console.error('添加反馈失败:', error);
            this.showError('网络错误');
        }
    }

    async saveProcessFeedback() {
        try {
            const form = document.getElementById('processFeedbackForm');
            const formData = new FormData(form);
            const processData = Object.fromEntries(formData.entries());

            const feedbackId = processData.feedback_id;

            const response = await fetch(`/api/admin/feedback/${feedbackId}/status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    status: processData.status,
                    notes: processData.notes
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('反馈状态更新成功');
                this.closeModal();
                this.loadFeedbackData();
                this.loadDashboardData();
            } else {
                this.showError(result.error || '更新反馈状态失败');
            }
        } catch (error) {
            console.error('更新反馈状态失败:', error);
            this.showError('网络错误');
        }
    }

    // 日志管理方法
    async loadLogsData() {
        try {
            const response = await fetch('/api/admin/logs?limit=100');
            const result = await response.json();

            if (result.success) {
                this.logsData = result.data;
                this.renderLogsTable(this.logsData);
            } else {
                this.showError('加载日志数据失败');
            }
        } catch (error) {
            console.error('加载日志数据失败:', error);
            this.showError('网络错误');
        }
    }

    renderLogsTable(data) {
        const tbody = document.getElementById('logsTableBody');

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="no-data">${_('暂无日志数据')}</td></tr>`;
            return;
        }

        let html = '';
        data.forEach(log => {
            const timestamp = new Date(log.timestamp).toLocaleString();
            const resultClass = `result-${log.result}`;
            const details = JSON.stringify(log.details || {});

            // 翻译操作类型
            const operationType = this.translateOperationType(log.operation_type);
            // 翻译目标类型
            const targetType = this.translateTargetType(log.target_type);
            // 翻译结果
            const result = this.translateResult(log.result);

            html += `
                <tr>
                    <td>${timestamp}</td>
                    <td>${log.operator}</td>
                    <td>${operationType}</td>
                    <td>${targetType}</td>
                    <td>${log.target_id}</td>
                    <td><span class="${resultClass}">${result}</span></td>
                    <td><div class="log-details" title="${details}">${details}</div></td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    }

    translateOperationType(operationType) {
        const translations = {
            'create': _('创建'),
            'update': _('更新'),
            'delete': _('删除'),
            'view': _('查看'),
            'update_stock': _('库存调整'),
            'export': _('数据导出'),
            'login': _('登录'),
            'logout': _('登出'),
            'count': _('盘点'),
            'complete_count': _('完成盘点'),
            'cancel_count': _('取消盘点'),
            'process_feedback': _('处理反馈'),
            'test': _('测试')
        };
        return translations[operationType] || operationType;
    }

    translateTargetType(targetType) {
        const translations = {
            'inventory': _('库存'),
            'feedback': _('反馈'),
            'admin': _('管理员'),
            'product': _('产品'),
            'count_task': _('盘点任务'),
            'system': _('系统'),
            'export': _('导出'),
            'backup': _('备份')
        };
        return translations[targetType] || targetType;
    }

    translateResult(result) {
        const translations = {
            'success': _('成功'),
            'failed': _('失败'),
            'error': _('错误'),
            'cancelled': _('已取消'),
            'pending': _('待处理')
        };
        return translations[result] || result;
    }

    filterLogs() {
        const operatorFilter = document.getElementById('logOperatorFilter').value;
        const operationFilter = document.getElementById('logOperationFilter').value;
        const targetFilter = document.getElementById('logTargetFilter').value;
        const limit = parseInt(document.getElementById('logLimitInput').value) || 100;

        let params = new URLSearchParams();
        if (operatorFilter) params.append('operator', operatorFilter);
        if (operationFilter) params.append('operation_type', operationFilter);
        if (targetFilter) params.append('target_type', targetFilter);
        params.append('limit', limit);

        fetch(`/api/admin/logs?${params}`)
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    this.renderLogsTable(result.data);
                } else {
                    this.showError('过滤日志失败');
                }
            })
            .catch(error => {
                console.error('过滤日志失败:', error);
                this.showError('网络错误');
            });
    }

    // 数据导出方法
    exportData(type, format) {
        const url = `/api/admin/export/${type}?format=${format}`;
        window.open(url, '_blank');
    }

    exportLogs(format) {
        const startDate = document.getElementById('exportStartDate').value;
        const endDate = document.getElementById('exportEndDate').value;

        let url = `/api/admin/export/logs?format=${format}`;
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;

        window.open(url, '_blank');
    }

    generateReport(type) {
        const url = `/api/admin/reports/${type}`;
        window.open(url, '_blank');
    }

    createBackup() {
        if (confirm('确定要创建完整数据备份吗？这可能需要一些时间。')) {
            // 这里可以实现完整备份功能
            this.showModal('创建备份', '<p>备份功能开发中...</p>');
        }
    }

    // 系统维护方法
    clearOldLogs() {
        if (confirm('确定要清理30天前的旧日志吗？此操作不可恢复。')) {
            this.showModal('清理日志', '<p>清理功能开发中...</p>');
        }
    }

    optimizeDatabase() {
        if (confirm('确定要优化数据库吗？这可能需要一些时间。')) {
            this.showModal('优化数据', '<p>优化功能开发中...</p>');
        }
    }

    resetSystem() {
        if (confirm('⚠️ 警告：确定要重置系统吗？这将删除所有数据！此操作不可恢复！')) {
            if (confirm('最后确认：您真的要重置整个系统吗？')) {
                this.showModal('重置系统', '<p>重置功能已禁用，请联系系统管理员。</p>');
            }
        }
    }

    // 辅助方法
    adjustStockInput(delta) {
        const input = document.getElementById('stockChange');
        const currentValue = parseInt(input.value) || 0;
        input.value = currentValue + delta;
    }

    async changePassword() {
        const oldPassword = document.getElementById('oldPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        if (newPassword !== confirmPassword) {
            this.showError('新密码和确认密码不匹配');
            return;
        }
        
        try {
            const response = await fetch('/api/admin/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ oldPassword, newPassword })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('密码修改成功');
                document.getElementById('changePasswordForm').reset();
            } else {
                this.showError(result.error || '密码修改失败');
            }
        } catch (error) {
            console.error('修改密码失败:', error);
            this.showError('网络错误');
        }
    }

    // ==================== 新页面方法 ====================

    setupNewPagesEventListeners() {
        // 产品入库页面事件
        document.getElementById('addProductForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveNewProduct();
        });

        // 产品信息变化时实时生成条形码预览
        ['productName', 'productCategory'].forEach(id => {
            document.getElementById(id)?.addEventListener('input', () => {
                this.updateBarcodePreview();
            });
        });

        // 库存盘点页面事件
        document.getElementById('createCountTaskBtn')?.addEventListener('click', () => {
            this.createCountTask();
        });

        document.getElementById('refreshCountTasksBtn')?.addEventListener('click', () => {
            this.loadCountTasks();
        });

        document.getElementById('countStatusFilter')?.addEventListener('change', () => {
            this.filterCountTasks();
        });

        document.getElementById('addByBarcodeBtn')?.addEventListener('click', () => {
            this.addCountItemByBarcode();
        });

        document.getElementById('searchProductBtn')?.addEventListener('click', () => {
            this.searchProductsForCount();
        });

        document.getElementById('completeCountBtn')?.addEventListener('click', () => {
            this.completeCurrentCount();
        });

        document.getElementById('cancelCountBtn')?.addEventListener('click', () => {
            this.cancelCurrentCount();
        });

        // 数据对比分析页面事件
        document.getElementById('createWeeklyAnalysisBtn')?.addEventListener('click', () => {
            this.createWeeklyAnalysis();
        });

        document.getElementById('createManualAnalysisBtn')?.addEventListener('click', () => {
            this.createManualAnalysis();
        });

        document.getElementById('downloadAnalysisReportBtn')?.addEventListener('click', () => {
            this.downloadAnalysisReport();
        });

        document.getElementById('downloadChangesExcelBtn')?.addEventListener('click', () => {
            this.downloadChangesExcel();
        });

        // 过滤器事件
        document.getElementById('changeTypeFilter')?.addEventListener('change', () => {
            this.filterAnalysisChanges();
        });

        document.getElementById('categoryAnalysisFilter')?.addEventListener('change', () => {
            this.filterAnalysisChanges();
        });
    }

    // ==================== 产品入库页面方法 ====================

    loadAddProductPage() {
        console.log('加载产品入库页面');
        // 重置表单
        document.getElementById('addProductForm')?.reset();
        // 清空条形码预览
        this.clearBarcodePreview();
    }

    updateBarcodePreview() {
        const productName = document.getElementById('productName')?.value;
        const category = document.getElementById('productCategory')?.value;

        if (productName && category) {
            // 模拟条形码生成（实际应该调用API）
            const mockBarcode = `880000${Math.random().toString().substr(2, 6)}`;
            const mockProductId = `P${Date.now().toString().substr(-6)}`;

            document.getElementById('barcodePreview').innerHTML = `
                <div class="barcode-image">
                    <div style="font-family: monospace; font-size: 14px; text-align: center; padding: 20px; border: 1px solid #ddd;">
                        <div style="margin-bottom: 10px;">||||| |||| ||||| |||| |||||</div>
                        <div>${mockBarcode}</div>
                    </div>
                </div>
            `;

            document.getElementById('barcodeNumber').textContent = mockBarcode;
            document.getElementById('productId').textContent = mockProductId;
            document.getElementById('barcodeInfo').style.display = 'block';
        } else {
            this.clearBarcodePreview();
        }
    }

    clearBarcodePreview() {
        document.getElementById('barcodePreview').innerHTML = `
            <div class="barcode-placeholder">
                <p>📊</p>
                <p>输入产品信息后将自动生成条形码</p>
            </div>
        `;
        document.getElementById('barcodeInfo').style.display = 'none';
    }

    async saveNewProduct() {
        try {
            const formData = new FormData(document.getElementById('addProductForm'));
            const productData = Object.fromEntries(formData.entries());

            const response = await fetch('/api/admin/inventory', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(productData)
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('产品添加成功！');
                document.getElementById('addProductForm').reset();
                this.clearBarcodePreview();

                // 显示成功信息
                this.showModal('产品添加成功', `
                    <div class="success-info">
                        <p><strong>产品ID：</strong>${result.product_id}</p>
                        <p><strong>条形码：</strong>已自动生成</p>
                        <p>产品已成功添加到库存系统中。</p>
                    </div>
                    <div style="text-align: center; margin-top: 20px;">
                        <button class="primary-btn" onclick="admin.closeModal()">确定</button>
                    </div>
                `);
            } else {
                this.showError(result.error || '添加产品失败');
            }
        } catch (error) {
            console.error('添加产品失败:', error);
            this.showError('网络错误');
        }
    }

    // ==================== 库存盘点页面方法 ====================

    loadInventoryCountsPage() {
        console.log('加载库存盘点页面');
        this.loadCountTasks();
        this.hideCurrentCountSection();
    }

    async loadCountTasks() {
        try {
            const response = await fetch('/api/admin/inventory/counts');
            const result = await response.json();

            if (result.success) {
                this.renderCountTasksTable(result.data);
            } else {
                this.showError('加载盘点任务失败');
            }
        } catch (error) {
            console.error('加载盘点任务失败:', error);
            this.showError('网络错误');
        }
    }

    renderCountTasksTable(tasks) {
        const tbody = document.getElementById('countTasksTableBody');

        if (tasks.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="no-data">${_('暂无盘点任务')}</td></tr>`;
            return;
        }

        let html = '';
        tasks.forEach(task => {
            const statusClass = `status-${task.status.replace('_', '-')}`;
            const statusText = {
                'in_progress': _('进行中'),
                'completed': _('已完成'),
                'cancelled': _('已取消')
            }[task.status] || task.status;

            html += `
                <tr>
                    <td>${task.count_id}</td>
                    <td>${new Date(task.count_date).toLocaleString()}</td>
                    <td>${task.operator}</td>
                    <td><span class="${statusClass}">${statusText}</span></td>
                    <td>${task.summary.total_items}</td>
                    <td>
                        <button class="secondary-btn" onclick="admin.viewCountTask('${task.count_id}')">${_('查看')}</button>
                        ${task.status === 'in_progress' ?
                            `<button class="primary-btn" onclick="admin.continueCountTask('${task.count_id}')">${_('继续')}</button>` :
                            ''
                        }
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    }

    async filterCountTasks() {
        try {
            const statusFilter = document.getElementById('countStatusFilter')?.value;

            let url = '/api/admin/inventory/counts';
            if (statusFilter) {
                url += `?status=${statusFilter}`;
            }

            const response = await fetch(url);
            const result = await response.json();

            if (result.success) {
                this.renderCountTasksTable(result.data);

                // 更新过滤提示
                const filterInfo = statusFilter ?
                    `已过滤显示: ${{'in_progress': '进行中', 'completed': '已完成', 'cancelled': '已取消'}[statusFilter] || statusFilter}任务` :
                    '显示所有任务';
                console.log(filterInfo);
            } else {
                this.showError('过滤盘点任务失败');
            }
        } catch (error) {
            console.error('过滤盘点任务失败:', error);
            this.showError('网络错误');
        }
    }

    async createCountTask() {
        try {
            const note = prompt(_('请输入盘点备注（可选）:')) || '';

            const response = await fetch('/api/admin/inventory/counts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ note })
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(_('盘点任务创建成功！'));
                this.loadCountTasks();
                this.continueCountTask(result.count_id);
            } else {
                this.showError(result.error || '创建盘点任务失败');
            }
        } catch (error) {
            console.error('创建盘点任务失败:', error);
            this.showError('网络错误');
        }
    }

    async viewCountTask(countId) {
        try {
            const response = await fetch(`/api/admin/inventory/counts/${countId}`);
            const result = await response.json();

            if (result.success) {
                const task = result.data;

                // 显示盘点任务详情模态框
                this.showCountTaskDetail(task);
            } else {
                this.showError('获取盘点任务详情失败');
            }
        } catch (error) {
            console.error('获取盘点任务详情失败:', error);
            this.showError('网络错误');
        }
    }

    showCountTaskDetail(task) {
        const statusText = {
            'in_progress': _('进行中'),
            'completed': _('已完成'),
            'cancelled': _('已取消')
        }[task.status] || task.status;

        const statusClass = `status-${task.status.replace('_', '-')}`;

        let itemsHtml = '';
        if (task.items && task.items.length > 0) {
            itemsHtml = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>${_('产品名称')}</th>
                            <th>${_('条形码')}</th>
                            <th>${_('存储区域')}</th>
                            <th>${_('账面数量')}</th>
                            <th>${_('实际数量')}</th>
                            <th>${_('差异')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${task.items.map(item => {
                            const difference = (item.actual_quantity || 0) - item.expected_quantity;
                            const differenceClass = difference > 0 ? 'positive' : difference < 0 ? 'negative' : 'neutral';
                            const differenceDisplay = difference !== 0 ? (difference > 0 ? `+${difference}` : difference) : '0';

                            return `
                                <tr>
                                    <td>${item.product_name}</td>
                                    <td>${item.barcode}</td>
                                    <td>${item.storage_area}</td>
                                    <td>${item.expected_quantity}</td>
                                    <td>${item.actual_quantity || '-'}</td>
                                    <td><span class="${differenceClass}">${differenceDisplay}</span></td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            `;
        } else {
            itemsHtml = `<p class="no-data">${_('暂无盘点项目')}</p>`;
        }

        const modalContent = `
            <div class="count-task-detail">
                <h3>${_('盘点任务详情')}</h3>
                <div class="task-info">
                    <div class="info-row">
                        <span class="label">${_('任务ID')}:</span>
                        <span class="value">${task.count_id}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">${_('创建时间')}:</span>
                        <span class="value">${new Date(task.count_date).toLocaleString()}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">${_('操作员')}:</span>
                        <span class="value">${task.operator}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">${_('状态')}:</span>
                        <span class="value"><span class="${statusClass}">${statusText}</span></span>
                    </div>
                    <div class="info-row">
                        <span class="label">${_('备注')}:</span>
                        <span class="value">${task.note || _('无')}</span>
                    </div>
                </div>
                <div class="task-summary">
                    <h4>${_('盘点汇总')}</h4>
                    <div class="summary-stats">
                        <span>${_('总项目')}: <strong>${task.summary.total_items}</strong></span>
                        <span>${_('有差异项目')}: <strong>${task.summary.items_with_difference}</strong></span>
                        <span>${_('总差异价值')}: <strong>¥${task.summary.total_difference_value.toFixed(2)}</strong></span>
                    </div>
                </div>
                <div class="task-items">
                    <h4>${_('盘点项目')}</h4>
                    ${itemsHtml}
                </div>
                <div class="modal-actions">
                    ${task.status === 'in_progress' ?
                        `<button class="primary-btn" onclick="admin.continueCountTask('${task.count_id}'); admin.hideModal();">${_('继续盘点')}</button>` :
                        ''
                    }
                    <button class="secondary-btn" onclick="admin.hideModal();">${_('关闭')}</button>
                </div>
            </div>
        `;

        this.showModal(modalContent);
    }

    async continueCountTask(countId) {
        try {
            const response = await fetch(`/api/admin/inventory/counts/${countId}`);
            const result = await response.json();

            if (result.success) {
                this.currentCountTask = result.data;
                this.showCurrentCountSection();
                this.updateCurrentCountInfo();
                this.renderCountItemsTable();
            } else {
                this.showError('加载盘点任务失败');
            }
        } catch (error) {
            console.error('加载盘点任务失败:', error);
            this.showError('网络错误');
        }
    }

    showCurrentCountSection() {
        document.getElementById('currentCountSection').style.display = 'block';
    }

    hideCurrentCountSection() {
        document.getElementById('currentCountSection').style.display = 'none';
        this.currentCountTask = null;
    }

    updateCurrentCountInfo() {
        if (!this.currentCountTask) return;

        document.getElementById('currentCountId').textContent = this.currentCountTask.count_id;
        document.getElementById('currentCountDate').textContent = new Date(this.currentCountTask.count_date).toLocaleString();
        document.getElementById('currentCountItemsCount').textContent = this.currentCountTask.items.length;
    }

    renderCountItemsTable() {
        if (!this.currentCountTask) return;

        const tbody = document.getElementById('countItemsTableBody');
        const items = this.currentCountTask.items;

        if (items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">暂无盘点项目，请添加产品</td></tr>';
            return;
        }

        let html = '';
        items.forEach(item => {
            const difference = item.actual_quantity !== null ?
                (item.actual_quantity - item.expected_quantity) : null;

            let differenceDisplay = '-';
            let differenceClass = 'difference-zero';

            if (difference !== null) {
                if (difference > 0) {
                    differenceDisplay = `+${difference}`;
                    differenceClass = 'difference-positive';
                } else if (difference < 0) {
                    differenceDisplay = difference.toString();
                    differenceClass = 'difference-negative';
                } else {
                    differenceDisplay = '0';
                    differenceClass = 'difference-zero';
                }
            }

            html += `
                <tr>
                    <td>${item.product_name}</td>
                    <td>${item.barcode}</td>
                    <td>${item.storage_area}</td>
                    <td>${item.expected_quantity}</td>
                    <td>
                        <input type="number" class="quantity-input"
                               value="${item.actual_quantity || ''}"
                               min="0"
                               onchange="admin.updateActualQuantity('${item.product_id}', this.value)"
                               placeholder="输入实际数量">
                    </td>
                    <td><span class="${differenceClass}">${differenceDisplay}</span></td>
                    <td>
                        <button class="danger-btn" onclick="admin.removeCountItem('${item.product_id}')">移除</button>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
        this.updateCountSummary();
    }

    updateCountSummary() {
        if (!this.currentCountTask) return;

        const items = this.currentCountTask.items;
        const totalItems = items.length;
        const recordedItems = items.filter(item => item.actual_quantity !== null).length;
        const differenceItems = items.filter(item =>
            item.actual_quantity !== null && item.actual_quantity !== item.expected_quantity
        ).length;

        document.getElementById('totalCountItems').textContent = totalItems;
        document.getElementById('recordedCountItems').textContent = recordedItems;
        document.getElementById('differenceCountItems').textContent = differenceItems;

        // 更新完成按钮状态
        const completeBtn = document.getElementById('completeCountBtn');
        if (completeBtn) {
            completeBtn.disabled = recordedItems < totalItems;
        }
    }

    async addCountItemByBarcode() {
        const barcode = document.getElementById('barcodeInput')?.value.trim();
        if (!barcode) {
            this.showError('请输入条形码');
            return;
        }

        if (!this.currentCountTask) {
            this.showError('请先选择一个盘点任务');
            return;
        }

        try {
            const response = await fetch(`/api/admin/inventory/counts/${this.currentCountTask.count_id}/items`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ barcode })
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('产品已添加到盘点列表');
                document.getElementById('barcodeInput').value = '';
                // 重新加载当前盘点任务
                this.continueCountTask(this.currentCountTask.count_id);
            } else {
                this.showError(result.error || '添加产品失败');
            }
        } catch (error) {
            console.error('添加产品失败:', error);
            this.showError('网络错误');
        }
    }

    async updateActualQuantity(productId, actualQuantity) {
        if (!this.currentCountTask) return;

        const quantity = parseInt(actualQuantity);
        if (isNaN(quantity) || quantity < 0) {
            this.showError('请输入有效的数量');
            return;
        }

        try {
            const response = await fetch(
                `/api/admin/inventory/counts/${this.currentCountTask.count_id}/items/${productId}/quantity`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ actual_quantity: quantity })
                }
            );

            const result = await response.json();

            if (result.success) {
                // 更新本地数据
                const item = this.currentCountTask.items.find(i => i.product_id === productId);
                if (item) {
                    item.actual_quantity = quantity;
                    item.difference = quantity - item.expected_quantity;
                }
                this.renderCountItemsTable();
            } else {
                this.showError(result.error || '更新数量失败');
            }
        } catch (error) {
            console.error('更新数量失败:', error);
            this.showError('网络错误');
        }
    }

    async searchProductsForCount() {
        const keyword = document.getElementById('productSearchInput')?.value.trim();
        if (!keyword) {
            this.showError('请输入搜索关键词');
            return;
        }

        if (!this.currentCountTask) {
            this.showError('请先选择一个盘点任务');
            return;
        }

        try {
            const response = await fetch(`/api/admin/inventory/search?keyword=${encodeURIComponent(keyword)}`);
            const result = await response.json();

            if (result.success && result.data.length > 0) {
                this.showProductSearchResults(result.data);
            } else {
                this.showError('未找到匹配的产品');
            }
        } catch (error) {
            console.error('搜索产品失败:', error);
            this.showError('网络错误');
        }
    }

    showProductSearchResults(products) {
        const resultsHtml = products.map(product => `
            <div class="search-result-item">
                <div class="product-info">
                    <strong>${product.product_name}</strong>
                    <span class="product-category">${product.category}</span>
                    <span class="product-stock">库存: ${product.current_stock}</span>
                </div>
                <button class="secondary-btn" onclick="admin.addProductToCount('${product.product_id}')">
                    添加到盘点
                </button>
            </div>
        `).join('');

        this.showModal('搜索结果', `
            <div class="product-search-results">
                ${resultsHtml}
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <button class="secondary-btn" onclick="admin.closeModal()">关闭</button>
            </div>
        `);
    }

    async addProductToCount(productId) {
        if (!this.currentCountTask) {
            this.showError('请先选择一个盘点任务');
            return;
        }

        try {
            const response = await fetch(`/api/admin/inventory/counts/${this.currentCountTask.count_id}/items`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ product_id: productId })
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('产品已添加到盘点列表');
                this.closeModal();
                // 重新加载当前盘点任务
                this.continueCountTask(this.currentCountTask.count_id);
            } else {
                this.showError(result.error || '添加产品失败');
            }
        } catch (error) {
            console.error('添加产品失败:', error);
            this.showError('网络错误');
        }
    }

    async completeCurrentCount() {
        if (!this.currentCountTask) {
            this.showError('没有正在进行的盘点任务');
            return;
        }

        // 检查是否所有项目都已录入实际数量
        const incompleteItems = this.currentCountTask.items.filter(item => item.actual_quantity === null);
        if (incompleteItems.length > 0) {
            this.showError(`还有 ${incompleteItems.length} 个产品未录入实际数量`);
            return;
        }

        if (!confirm('确定要完成当前盘点任务吗？完成后将无法修改。')) {
            return;
        }

        try {
            const response = await fetch(`/api/admin/inventory/counts/${this.currentCountTask.count_id}/complete`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('盘点任务已完成！');
                this.hideCurrentCountSection();
                this.loadCountTasks();
            } else {
                this.showError(result.error || '完成盘点任务失败');
            }
        } catch (error) {
            console.error('完成盘点任务失败:', error);
            this.showError('网络错误');
        }
    }

    async cancelCurrentCount() {
        if (!this.currentCountTask) {
            this.showError('没有正在进行的盘点任务');
            return;
        }

        const reason = prompt('请输入取消原因（可选）:') || '';

        if (!confirm('确定要取消当前盘点任务吗？取消后数据将无法恢复。')) {
            return;
        }

        try {
            const response = await fetch(`/api/admin/inventory/counts/${this.currentCountTask.count_id}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ reason })
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('盘点任务已取消');
                this.hideCurrentCountSection();
                this.loadCountTasks();
            } else {
                this.showError(result.error || '取消盘点任务失败');
            }
        } catch (error) {
            console.error('取消盘点任务失败:', error);
            this.showError('网络错误');
        }
    }

    // ==================== 数据对比分析页面方法 ====================

    loadInventoryAnalysisPage() {
        console.log('加载数据对比分析页面');
        this.loadCompletedCountTasks();
        this.hideAnalysisResults();
    }

    async loadCompletedCountTasks() {
        try {
            const response = await fetch('/api/admin/inventory/counts?status=completed');
            const result = await response.json();

            if (result.success) {
                this.populateCountSelects(result.data);
            }
        } catch (error) {
            console.error('加载已完成盘点任务失败:', error);
        }
    }

    populateCountSelects(tasks) {
        const currentSelect = document.getElementById('currentCountSelect');
        const previousSelect = document.getElementById('previousCountSelect');

        if (currentSelect && previousSelect) {
            const options = tasks.map(task =>
                `<option value="${task.count_id}">${task.count_id} - ${new Date(task.count_date).toLocaleDateString()}</option>`
            ).join('');

            currentSelect.innerHTML = '<option value="">请选择盘点任务</option>' + options;
            previousSelect.innerHTML = '<option value="">请选择盘点任务</option>' + options;
        }
    }

    async createWeeklyAnalysis() {
        try {
            // 第一步：创建周对比分析
            const response = await fetch('/api/admin/inventory/comparisons/weekly', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success && result.comparison_id) {
                // 第二步：获取完整的分析数据
                const detailResponse = await fetch(`/api/admin/inventory/comparisons/${result.comparison_id}`);
                const detailResult = await detailResponse.json();

                if (detailResult.success) {
                    this.showAnalysisResults(detailResult.data);
                    this.showSuccess('周对比分析创建成功！');
                } else {
                    this.showError('获取分析详情失败');
                }
            } else {
                this.showError(result.error || '生成周对比分析失败');
            }
        } catch (error) {
            console.error('生成周对比分析失败:', error);
            this.showError('网络错误');
        }
    }

    async createManualAnalysis() {
        const currentCountId = document.getElementById('currentCountSelect')?.value;
        const previousCountId = document.getElementById('previousCountSelect')?.value;

        if (!currentCountId || !previousCountId) {
            this.showError('请选择两个盘点任务进行对比');
            return;
        }

        if (currentCountId === previousCountId) {
            this.showError('请选择不同的盘点任务进行对比');
            return;
        }

        try {
            // 第一步：创建对比分析
            const response = await fetch('/api/admin/inventory/comparisons', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    current_count_id: currentCountId,
                    previous_count_id: previousCountId,
                    comparison_type: 'manual'
                })
            });

            const result = await response.json();

            if (result.success && result.comparison_id) {
                // 第二步：获取完整的分析数据
                const detailResponse = await fetch(`/api/admin/inventory/comparisons/${result.comparison_id}`);
                const detailResult = await detailResponse.json();

                if (detailResult.success) {
                    this.showAnalysisResults(detailResult.data);
                    this.showSuccess('手动对比分析创建成功！');
                } else {
                    this.showError('获取分析详情失败');
                }
            } else {
                this.showError(result.error || '生成对比分析失败');
            }
        } catch (error) {
            console.error('生成对比分析失败:', error);
            this.showError('网络错误');
        }
    }

    showAnalysisResults(analysisData) {
        document.getElementById('analysisResultsSection').style.display = 'block';

        // 更新统计汇总
        document.getElementById('totalProductsAnalyzed').textContent = analysisData.statistics.total_products;
        document.getElementById('changedProductsCount').textContent = analysisData.statistics.changed_products;
        document.getElementById('anomaliesCount').textContent = analysisData.anomalies.length;
        document.getElementById('totalValueChange').textContent = `${analysisData.statistics.total_value_change || 0}元`;

        // 渲染变化明细表格
        this.renderChangesTable(analysisData.changes);

        // 显示异常检测结果
        this.renderAnomalies(analysisData.anomalies);

        // 更新分析信息
        document.getElementById('analysisDate').textContent = new Date(analysisData.comparison_date).toLocaleString();
        document.getElementById('analysisRange').textContent = `${analysisData.previous_count.count_id} → ${analysisData.current_count.count_id}`;
        document.getElementById('analysisType').textContent = analysisData.comparison_type === 'weekly' ? '周对比分析' : '手动对比分析';

        this.currentAnalysisData = analysisData;
    }

    hideAnalysisResults() {
        document.getElementById('analysisResultsSection').style.display = 'none';
        this.currentAnalysisData = null;
    }

    renderChangesTable(changes) {
        const tbody = document.getElementById('changesTableBody');

        if (changes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="no-data">暂无变化数据</td></tr>';
            return;
        }

        let html = '';
        changes.forEach(change => {
            const changeClass = `change-${change.status}`;
            const statusText = {
                'increased': '库存增加',
                'decreased': '库存减少',
                'new': '新增产品',
                'removed': '移除产品'
            }[change.status] || change.status;

            const changePercent = change.change_percentage ? `${change.change_percentage.toFixed(1)}%` : '-';

            html += `
                <tr>
                    <td>${change.product_name}</td>
                    <td>${change.category}</td>
                    <td>${change.storage_area}</td>
                    <td>${change.previous_quantity || '-'}</td>
                    <td>${change.current_quantity || '-'}</td>
                    <td class="${changeClass}">${change.quantity_change > 0 ? '+' : ''}${change.quantity_change}</td>
                    <td class="${changeClass}">${changePercent}</td>
                    <td><span class="${changeClass}">${statusText}</span></td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    }

    renderAnomalies(anomalies) {
        const container = document.getElementById('anomaliesList');

        if (anomalies.length === 0) {
            container.innerHTML = '<div class="no-data">未检测到异常情况</div>';
            return;
        }

        let html = '';
        anomalies.forEach(anomaly => {
            html += `
                <div class="anomaly-item">
                    <h5>${anomaly.type}</h5>
                    <p>${anomaly.description}</p>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    async downloadAnalysisReport() {
        if (!this.currentAnalysisData) {
            this.showError('请先生成分析报告');
            return;
        }

        try {
            const response = await fetch(`/api/admin/inventory/comparisons/${this.currentAnalysisData.comparison_id}/report`);

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `库存对比分析报告_${this.currentAnalysisData.comparison_id}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                this.showError('下载报告失败');
            }
        } catch (error) {
            console.error('下载报告失败:', error);
            this.showError('网络错误');
        }
    }

    async downloadChangesExcel() {
        if (!this.currentAnalysisData) {
            this.showError('请先生成分析数据');
            return;
        }

        try {
            const response = await fetch(`/api/admin/inventory/comparisons/${this.currentAnalysisData.comparison_id}/excel`);

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `库存变化明细_${this.currentAnalysisData.comparison_id}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                this.showError('导出Excel失败');
            }
        } catch (error) {
            console.error('导出Excel失败:', error);
            this.showError('网络错误');
        }
    }
}

// 初始化管理员控制台
const admin = new AdminDashboard();
