// 修复AI订单识别功能
document.addEventListener('DOMContentLoaded', function() {
    console.log("订单识别页面初始化...");
    
    // 获取聊天相关元素
    const chatInput = document.getElementById('chat-input');
    const sendMessage = document.getElementById('send-message');
    const chatMessages = document.getElementById('chat-messages');
    
    // 获取订单项目区域
    const productPreview = document.getElementById('product-preview');
    const emptyItemsState = document.getElementById('empty-items-state');
    
    // 全局变量
    window.sessionId = '';
    window.productList = [];
    
    // 发送聊天消息
    async function sendChatMessage(message) {
        console.log("发送消息:", message);
        // 创建用户消息
        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'message user-message';
        userMessageDiv.textContent = message;
        chatMessages.appendChild(userMessageDiv);
        
        // 自动滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        if (!window.sessionId) {
            // 如果没有会话ID，提示用户先上传照片
            const aiMessageDiv = document.createElement('div');
            aiMessageDiv.className = 'message ai-message';
            aiMessageDiv.textContent = '请先上传订单照片';
            chatMessages.appendChild(aiMessageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            return;
        }
        
        try {
            // 发送请求到后端
            const formData = new FormData();
            formData.append('session_id', window.sessionId);
            formData.append('message', message);
            
            const response = await fetch('/mlsp/api/order-recognition/adjust-order', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            console.log("收到后端响应:", result);
            
            if (result.success) {
                // 添加AI回复
                const aiMessageDiv = document.createElement('div');
                aiMessageDiv.className = 'message ai-message';
                aiMessageDiv.textContent = result.response;
                chatMessages.appendChild(aiMessageDiv);
                
                // 更新产品列表
                if (result.products && Array.isArray(result.products)) {
                    console.log("更新产品列表:", result.products);
                    window.productList = result.products;
                    
                    // 必须立即切换到"订单项目"标签以显示更新后的产品
                    const itemsTab = document.getElementById('items-tab');
                    if (itemsTab) {
                        itemsTab.click();
                    }
                    
                    updateProductDisplay();
                }
            } else {
                // 显示错误消息
                const aiMessageDiv = document.createElement('div');
                aiMessageDiv.className = 'message ai-message';
                aiMessageDiv.textContent = result.message || '处理消息时出错';
                chatMessages.appendChild(aiMessageDiv);
            }
            
            // 自动滚动到底部
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } catch (error) {
            console.error('发送消息失败:', error);
            
            // 显示错误消息
            const aiMessageDiv = document.createElement('div');
            aiMessageDiv.className = 'message ai-message';
            aiMessageDiv.textContent = '网络错误，请稍后重试';
            chatMessages.appendChild(aiMessageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    
    // 更新产品显示
    function updateProductDisplay() {
        console.log("执行更新产品显示函数", window.productList);
        
        // 确定正确的产品列表容器
        const itemsContent = document.getElementById('items-content');
        
        if (!itemsContent) {
            console.error("找不到商品列表容器");
            return;
        }
        
        // 清空当前显示
        while (itemsContent.firstChild) {
            itemsContent.removeChild(itemsContent.firstChild);
        }
        
        // 处理空列表情况
        if (!window.productList || window.productList.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.id = 'empty-items-state';
            emptyState.innerHTML = `
                <div class="empty-icon">
                    <i class="bi bi-cart"></i>
                </div>
                <h5>暂无识别结果</h5>
                <p class="text-muted">请先上传订单照片或使用AI助手添加商品</p>
            `;
            itemsContent.appendChild(emptyState);
            return;
        }
        
        // 创建新的产品列表容器
        const productListContainer = document.createElement('div');
        productListContainer.id = 'product-preview';
        
        // 计算总金额
        let totalAmount = 0;
        
        // 添加每个产品
        window.productList.forEach((product, index) => {
            const itemPrice = product.price * product.quantity;
            totalAmount += itemPrice;
            
            const itemCard = document.createElement('div');
            itemCard.className = 'item-card';
            itemCard.innerHTML = `
                <div class="d-flex justify-content-between">
                    <div>
                        <div class="fw-bold">${product.name}</div>
                        <div class="text-muted">¥${product.price.toFixed(2)} × ${product.quantity} ${product.unit_type || '份'}</div>
                    </div>
                    <div class="d-flex align-items-center">
                        <button class="btn btn-sm btn-outline-secondary decrease-btn" data-index="${index}">-</button>
                        <span class="mx-2">${product.quantity}</span>
                        <button class="btn btn-sm btn-outline-secondary increase-btn" data-index="${index}">+</button>
                        <div class="ms-3 text-danger fw-bold">¥${itemPrice.toFixed(2)}</div>
                        <button class="btn btn-sm btn-link text-danger remove-btn" data-index="${index}"><i class="bi bi-x-circle"></i></button>
                    </div>
                </div>
            `;
            
            productListContainer.appendChild(itemCard);
        });
        
        // 添加总金额
        const totalSection = document.createElement('div');
        totalSection.id = 'total-section';
        totalSection.className = 'total-section';
        totalSection.innerHTML = `总计: <span id="total-amount">¥${totalAmount.toFixed(2)}</span>`;
        
        // 将产品列表和总金额添加到容器中
        itemsContent.appendChild(productListContainer);
        itemsContent.appendChild(totalSection);
        
        // 添加按钮事件监听
        document.querySelectorAll('.decrease-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                if (window.productList[index].quantity > 1) {
                    updateItemQuantity(window.productList[index].id, window.productList[index].quantity - 1);
                }
            });
        });
        
        document.querySelectorAll('.increase-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                updateItemQuantity(window.productList[index].id, window.productList[index].quantity + 1);
            });
        });
        
        document.querySelectorAll('.remove-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                updateItemQuantity(window.productList[index].id, 0);
            });
        });
        
        console.log("产品显示更新完成");
    }
    
    // 更新商品数量
    async function updateItemQuantity(productId, quantity) {
        console.log(`更新商品数量: ID=${productId}, 数量=${quantity}`);
        
        if (!window.sessionId) {
            console.error('没有活动会话');
            return;
        }
        
        try {
            const formData = new FormData();
            formData.append('session_id', window.sessionId);
            formData.append('product_id', productId);
            formData.append('quantity', quantity);
            
            const response = await fetch('/mlsp/api/order-recognition/update-item-quantity', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 更新产品列表
                if (result.products && Array.isArray(result.products)) {
                    console.log("更新后的产品列表:", result.products);
                    window.productList = result.products;
                    updateProductDisplay();
                }
            } else {
                console.error('更新商品数量失败:', result.message);
                alert(result.message || '更新商品数量失败');
            }
        } catch (error) {
            console.error('更新商品数量失败:', error);
            alert('网络错误，请稍后重试');
        }
    }
    
    // 处理图片上传
    const uploadTrigger = document.getElementById('upload-trigger');
    const fileInput = document.getElementById('file-input');
    const processImage = document.getElementById('process-image');
    const processingIndicator = document.getElementById('processing-indicator');
    const imagePreview = document.getElementById('image-preview');
    const previewImage = document.getElementById('preview-image');
    
    if (uploadTrigger && fileInput) {
        uploadTrigger.addEventListener('click', function() {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                    uploadTrigger.style.display = 'none';
                    imagePreview.style.display = 'block';
                };
                
                reader.readAsDataURL(file);
            }
        });
    }
    
    if (processImage) {
        processImage.addEventListener('click', async function() {
            if (!fileInput || !fileInput.files.length) {
                alert('请先选择图片');
                return;
            }
            
            processingIndicator.style.display = 'block';
            imagePreview.style.display = 'none';
            
            try {
                const formData = new FormData();
                formData.append('photo', fileInput.files[0]);
                
                const response = await fetch('/mlsp/api/order-recognition/upload-photo', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                console.log("上传照片结果:", result);
                
                if (result.success) {
                    window.sessionId = result.session_id;
                    
                    // 修正这里：检查并使用recognized_items或products
                    if (result.recognized_items && Array.isArray(result.recognized_items)) {
                        window.productList = result.recognized_items;
                        console.log("识别到的产品:", window.productList);
                    } else if (result.products && Array.isArray(result.products)) {
                        window.productList = result.products;
                        console.log("识别到的产品:", window.productList);
                    } else {
                        window.productList = [];
                        console.warn("响应中没有产品信息");
                    }
                    
                    // 添加欢迎消息
                    if (chatMessages) {
                        chatMessages.innerHTML = '';
                        const welcomeMessage = document.createElement('div');
                        welcomeMessage.className = 'message ai-message';
                        welcomeMessage.textContent = '订单照片上传成功！我已经识别出以下商品，您可以通过对话进行调整，例如"添加5份牛肉"。';
                        chatMessages.appendChild(welcomeMessage);
                    }
                    
                    // 切换到调整步骤
                    const uploadStep = document.getElementById('upload-step');
                    const adjustStep = document.getElementById('adjust-step');
                    
                    if (uploadStep && adjustStep) {
                        uploadStep.style.display = 'none';
                        adjustStep.style.display = 'block';
                        
                        // 立即更新产品显示
                        updateProductDisplay();
                        
                        // 更新步骤指示器
                        updateStepIndicators(1);
                    }
                } else {
                    alert(result.message || '照片上传失败');
                    if (uploadTrigger) uploadTrigger.style.display = 'block';
                    if (imagePreview) imagePreview.style.display = 'none';
                }
            } catch (error) {
                console.error('上传照片失败:', error);
                alert('网络错误，请稍后重试');
                if (uploadTrigger) uploadTrigger.style.display = 'block';
                if (imagePreview) imagePreview.style.display = 'none';
            } finally {
                if (processingIndicator) processingIndicator.style.display = 'none';
            }
        });
    }
    
    // 绑定发送消息事件
    if (sendMessage && chatInput) {
        sendMessage.addEventListener('click', function() {
            const message = chatInput.value.trim();
            if (message) {
                sendChatMessage(message);
                chatInput.value = '';
            }
        });
        
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const message = chatInput.value.trim();
                if (message) {
                    sendChatMessage(message);
                    chatInput.value = '';
                }
                e.preventDefault();
            }
        });
    }
    
    // 更新步骤指示器
    function updateStepIndicators(activeStep) {
        const stepIcons = [
            document.getElementById('step-icon-1'),
            document.getElementById('step-icon-2'),
            document.getElementById('step-icon-3')
        ];
        
        const stepLines = [
            document.getElementById('step-line-1'),
            document.getElementById('step-line-2')
        ];
        
        const stepTexts = [
            document.getElementById('step-text-1'),
            document.getElementById('step-text-2'),
            document.getElementById('step-text-3')
        ];
        
        if (!stepIcons[0] || !stepTexts[0]) return;
        
        // 重置所有步骤
        stepIcons.forEach((icon, i) => {
            if (icon) {
                icon.classList.remove('active', 'completed');
            }
            if (stepTexts[i]) {
                stepTexts[i].classList.remove('active');
            }
        });
        
        stepLines.forEach(line => {
            if (line) {
                line.classList.remove('active');
            }
        });
        
        // 设置当前活动步骤之前的步骤为已完成
        for (let i = 0; i < activeStep; i++) {
            if (stepIcons[i]) {
                stepIcons[i].classList.add('completed');
            }
            if (i < stepLines.length && stepLines[i]) {
                stepLines[i].classList.add('active');
            }
        }
        
        // 设置当前活动步骤
        if (activeStep < stepIcons.length && stepIcons[activeStep]) {
            stepIcons[activeStep].classList.add('active');
            if (stepTexts[activeStep]) {
                stepTexts[activeStep].classList.add('active');
            }
        }
    }
    
    // 确认订单
    const goToConfirm = document.getElementById('go-to-confirm');
    const confirmStep = document.getElementById('confirm-step');
    const adjustStep = document.getElementById('adjust-step');
    const finalProductList = document.getElementById('final-product-list');
    const finalTotalAmount = document.getElementById('final-total-amount');
    
    if (goToConfirm) {
        goToConfirm.addEventListener('click', function() {
            if (!window.productList || window.productList.length === 0) {
                alert('请至少添加一件商品');
                return;
            }
            
            // 更新最终产品列表
            if (finalProductList) {
                finalProductList.innerHTML = '';
                
                let totalAmount = 0;
                
                window.productList.forEach(product => {
                    const itemAmount = product.price * product.quantity;
                    totalAmount += itemAmount;
                    
                    const item = document.createElement('div');
                    item.className = 'item-card';
                    item.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <div class="fw-bold">${product.name}</div>
                                <div class="text-muted">¥${product.price.toFixed(2)} × ${product.quantity} ${product.unit_type || '份'}</div>
                            </div>
                            <div class="text-danger fw-bold">¥${itemAmount.toFixed(2)}</div>
                        </div>
                    `;
                    
                    finalProductList.appendChild(item);
                });
                
                if (finalTotalAmount) {
                    finalTotalAmount.textContent = `¥${totalAmount.toFixed(2)}`;
                }
            }
            
            // 切换到确认步骤
            if (adjustStep && confirmStep) {
                adjustStep.style.display = 'none';
                confirmStep.style.display = 'block';
                
                // 更新步骤指示器
                updateStepIndicators(2);
            }
        });
    }
    
    // 返回调整步骤
    const backToAdjust = document.getElementById('back-to-adjust');
    
    if (backToAdjust) {
        backToAdjust.addEventListener('click', function() {
            if (adjustStep && confirmStep) {
                confirmStep.style.display = 'none';
                adjustStep.style.display = 'block';
                
                // 更新步骤指示器
                updateStepIndicators(1);
            }
        });
    }
    
    // 提交订单
    const submitOrder = document.getElementById('submit-order');
    const orderNote = document.getElementById('order-note');
    const successStep = document.getElementById('success-step');
    const orderId = document.getElementById('order-id');
    
    if (submitOrder) {
        submitOrder.addEventListener('click', async function() {
            if (!window.sessionId) {
                alert('会话已过期，请重新开始');
                return;
            }
            
            submitOrder.disabled = true;
            submitOrder.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 提交中...';
            
            try {
                const formData = new FormData();
                formData.append('session_id', window.sessionId);
                if (orderNote && orderNote.value) {
                    formData.append('note', orderNote.value);
                }
                
                const response = await fetch('/mlsp/api/order-recognition/confirm-order', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // 显示订单ID
                    if (orderId) {
                        orderId.textContent = result.order_id;
                    }
                    
                    // 切换到成功步骤
                    if (confirmStep && successStep) {
                        confirmStep.style.display = 'none';
                        successStep.style.display = 'block';
                        
                        // 更新步骤指示器
                        updateStepIndicators(3);
                    }
                } else {
                    alert(result.message || '提交订单失败');
                    submitOrder.disabled = false;
                    submitOrder.innerHTML = '<i class="bi bi-check-circle"></i> 提交订单';
                }
            } catch (error) {
                console.error('提交订单失败:', error);
                alert('网络错误，请稍后重试');
                submitOrder.disabled = false;
                submitOrder.innerHTML = '<i class="bi bi-check-circle"></i> 提交订单';
            }
        });
    }
    
    // 切换标签页
    const itemsTab = document.getElementById('items-tab');
    const chatTab = document.getElementById('chat-tab');
    const addTab = document.getElementById('add-tab');
    const itemsContent = document.getElementById('items-content');
    const chatContent = document.getElementById('chat-content');
    const addContent = document.getElementById('add-content');
    
    if (itemsTab && chatTab && addTab && itemsContent && chatContent && addContent) {
        itemsTab.addEventListener('click', function() {
            itemsTab.classList.add('active');
            chatTab.classList.remove('active');
            addTab.classList.remove('active');
            
            itemsContent.style.display = 'block';
            chatContent.style.display = 'none';
            addContent.style.display = 'none';
            
            // 每次切换到商品标签页都更新显示
            updateProductDisplay();
        });
        
        chatTab.addEventListener('click', function() {
            chatTab.classList.add('active');
            itemsTab.classList.remove('active');
            addTab.classList.remove('active');
            
            chatContent.style.display = 'block';
            itemsContent.style.display = 'none';
            addContent.style.display = 'none';
        });
        
        addTab.addEventListener('click', function() {
            addTab.classList.add('active');
            itemsTab.classList.remove('active');
            chatTab.classList.remove('active');
            
            addContent.style.display = 'block';
            itemsContent.style.display = 'none';
            chatContent.style.display = 'none';
        });
    }
});
