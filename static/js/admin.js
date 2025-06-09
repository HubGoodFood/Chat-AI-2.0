// 管理员页面JavaScript
class AdminDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.inventoryData = [];
        this.feedbackData = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.checkAuthStatus();
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
                statusDiv.innerHTML = '<p class="no-data">✅ 所有产品库存充足</p>';
            }
        } catch (error) {
            console.error('加载库存状态失败:', error);
            document.getElementById('inventoryStatus').innerHTML = '<p class="error">加载失败</p>';
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
                    const typeText = feedback.feedback_type === 'positive' ? '正面' : '负面';
                    
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
                feedbackDiv.innerHTML = '<p class="no-data">暂无最新反馈</p>';
            }
        } catch (error) {
            console.error('加载最新反馈失败:', error);
            document.getElementById('recentFeedback').innerHTML = '<p class="error">加载失败</p>';
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
            this.showError('网络错误');
        }
    }

    renderInventoryTable(data) {
        const tbody = document.getElementById('inventoryTableBody');
        
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">暂无库存数据</td></tr>';
            return;
        }

        let html = '';
        data.forEach(product => {
            const statusClass = product.status === 'active' ? 'status-active' : 'status-inactive';
            const statusText = product.status === 'active' ? '正常' : '停用';
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
                        <button class="secondary-btn" onclick="admin.editProduct('${product.product_id}')">编辑</button>
                        <button class="secondary-btn" onclick="admin.adjustStock('${product.product_id}')">调库存</button>
                        <button class="danger-btn" onclick="admin.deleteProduct('${product.product_id}')">删除</button>
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
            this.showError('网络错误');
        }
    }

    renderFeedbackTable(data) {
        const tbody = document.getElementById('feedbackTableBody');
        
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">暂无反馈数据</td></tr>';
            return;
        }

        let html = '';
        data.forEach(feedback => {
            const typeClass = feedback.feedback_type === 'positive' ? 'feedback-positive' : 'feedback-negative';
            const typeText = feedback.feedback_type === 'positive' ? '正面反馈' : '负面反馈';
            
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
                        <button class="secondary-btn" onclick="admin.viewFeedback('${feedback.feedback_id}')">查看</button>
                        <button class="secondary-btn" onclick="admin.processFeedback('${feedback.feedback_id}')">处理</button>
                        <button class="danger-btn" onclick="admin.deleteFeedback('${feedback.feedback_id}')">删除</button>
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
        alert('错误: ' + message);
    }

    showSuccess(message) {
        alert('成功: ' + message);
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
        document.getElementById('productModalTitle').textContent = '添加产品';
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
        if (confirm('确定要删除这个产品吗？此操作将设置产品状态为停用。')) {
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
                const typeText = feedback.feedback_type === 'positive' ? '正面反馈' : '负面反馈';
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
                            <strong>产品名称：</strong>${feedback.product_name}
                        </div>
                        <div class="detail-row">
                            <strong>反馈类型：</strong><span class="${typeClass}">${typeText}</span>
                        </div>
                        <div class="detail-row">
                            <strong>客户昵称：</strong>${feedback.customer_wechat_name}
                        </div>
                        <div class="detail-row">
                            <strong>客户群号：</strong>${feedback.customer_group_number}
                        </div>
                        <div class="detail-row">
                            <strong>付款状态：</strong>${feedback.payment_status}
                        </div>
                        <div class="detail-row">
                            <strong>反馈时间：</strong>${new Date(feedback.feedback_time).toLocaleString()}
                        </div>
                        <div class="detail-row">
                            <strong>处理状态：</strong>${feedback.processing_status}
                        </div>
                        ${feedback.processor ? `<div class="detail-row"><strong>处理人：</strong>${feedback.processor}</div>` : ''}
                        <div class="detail-row">
                            <strong>反馈内容：</strong>
                            <div style="margin-top: 5px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                                ${feedback.feedback_content}
                            </div>
                        </div>
                        ${feedback.processing_notes ? `
                            <div class="detail-row">
                                <strong>处理备注：</strong>
                                <div style="margin-top: 5px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                                    ${feedback.processing_notes}
                                </div>
                            </div>
                        ` : ''}
                        ${customerImages ? `
                            <div class="detail-row">
                                <strong>客户图片：</strong>
                                <div style="margin-top: 5px;">
                                    ${customerImages}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;

                this.showModal('反馈详情', content);
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
                    <p><strong>客户：</strong>${feedback.customer_wechat_name}</p>
                    <p><strong>反馈类型：</strong>${feedback.feedback_type === 'positive' ? '正面反馈' : '负面反馈'}</p>
                    <p><strong>当前状态：</strong>${feedback.processing_status}</p>
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
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">暂无日志数据</td></tr>';
            return;
        }

        let html = '';
        data.forEach(log => {
            const timestamp = new Date(log.timestamp).toLocaleString();
            const resultClass = `result-${log.result}`;
            const details = JSON.stringify(log.details || {});

            html += `
                <tr>
                    <td>${timestamp}</td>
                    <td>${log.operator}</td>
                    <td>${log.operation_type}</td>
                    <td>${log.target_type}</td>
                    <td>${log.target_id}</td>
                    <td><span class="${resultClass}">${log.result}</span></td>
                    <td><div class="log-details" title="${details}">${details}</div></td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
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
}

// 初始化管理员控制台
const admin = new AdminDashboard();
