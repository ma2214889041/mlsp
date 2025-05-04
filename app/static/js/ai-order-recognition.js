// AI订单识别系统JavaScript

// 全局变量，保存当前订单会话
let currentSessionId = null;
let orderItems = [];
let totalAmount = 0;

// DOM元素
document.addEventListener('DOMContentLoaded', function() {
    // 上传相关元素
    const uploadArea = document.getElementById('uploadArea');
    const photoInput = document.getElementById('photoInput');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');
    const previewContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    const changePhotoBtn = document.getElementById('changePhotoBtn');
    const recognizeBtn = document.getElementById('recognizeBtn');
    
    // 处理与结果相关元素
    const processingIndicator = document.getElementById('processingIndicator');
    const recognitionResults = document.getElementById('recognitionResults');
    const orderItemsList = document.getElementById('orderItemsList');
    const orderTotal = document.getElementById('orderTotal');
    const totalAmountSpan = document.getElementById('totalAmount');
    
    // 对话相关元素
    const chatSection = document.getElementById('chatSection');
    const chatContainer = document.getElementById('chatContainer');
    const messageInput = document.getElementById('messageInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const toggleChatBtn = document.getElementById('toggleChatBtn');
    const suggestionTags = document.querySelectorAll('.suggestion-tag');
    
    // 按钮和导航元素
    const backToUploadBtn = document.getElementById('backToUploadBtn');
    const confirmOrderBtn = document.getElementById('confirmOrderBtn');
    const orderConfirmation = document.getElementById('orderConfirmation');
    const orderItemsSummary = document.getElementById('orderItemsSummary');
    const confirmTotalAmount = document.getElementById('confirmTotalAmount');
    const backToAdjustBtn = document.getElementById('backToAdjustBtn');
    const submitOrderBtn = document.getElementById('submitOrderBtn');
    const orderNote = document.getElementById('orderNote');
    const orderSuccess = document.getElementById('orderSuccess');
    const successOrderId = document.getElementById('successOrderId');
    
    // 步骤指示器
    const steps = {
        step1: document.getElementById('step-1'),
        step2: document.getElementById('step-2'),
        step3: document.getElementById('step-3'),
        step4: document.getElementById('step-4')
    };
    
    // 设置当前步骤
    function setCurrentStep(stepNumber) {
        // 清除所有步骤的状态
        Object.values(steps).forEach(step => {
            step.classList.remove('active', 'completed');
        });
        
        // 设置当前步骤为激活状态
        steps[`step${stepNumber}`].classList.add('active');
        
        // 设置之前的步骤为已完成状态
        for (let i = 1; i < stepNumber; i++) {
            steps[`step${i}`].classList.add('completed');
        }
    }
    
    // 初始化上传功能
    function initUpload() {
        // 点击上传区域触发文件选择
        uploadArea.addEventListener('click', function() {
            if (uploadPlaceholder.style.display !== 'none') {
                photoInput.click();
            }
        });
        
        // 拖拽上传功能
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('bg-light');
        });
        
        uploadArea.addEventListener('dragleave', function() {
            uploadArea.classList.remove('bg-light');
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('bg-light');
            
            if (e.dataTransfer.files.length) {
                handleFileSelection(e.dataTransfer.files[0]);
            }
        });
        
        // 文件选择处理
        photoInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                handleFileSelection(this.files[0]);
            }
        });
        
        // 更换照片按钮
        changePhotoBtn.addEventListener('click', function() {
            photoInput.click();
        });
        
        // 开始识别按钮
        recognizeBtn.addEventListener('click', startRecognition);
    }
    
    // 文件选择处理
    function handleFileSelection(file) {
        // 验证文件是否为图片
        if (!file.type.match('image.*')) {
            alert('请选择图片文件');
            return;
        }
        
        // 显示预览
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
            uploadPlaceholder.style.display = 'none';
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
    
    // 开始识别
    function startRecognition() {
        // 显示处理中指示器
        uploadSection.style.display = 'none';
        processingIndicator.style.display = 'block';
        recognitionResults.style.display = 'none';
        setCurrentStep(2); // 设置步骤为"识别订单"
        
        // 准备表单数据
        const formData = new FormData();
        formData.append('image', photoInput.files[0]);
        
        // 发送API请求
        fetch('/mlsp/api/order-recognition/upload-photo', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络请求失败');
            }
            return response.json();
        })
        .then(data => {
            // 处理识别结果
            if (data.success) {
                currentSessionId = data.session_id;
                orderItems = data.items || [];
                updateOrderItems();
                showRecognitionResults();
                setCurrentStep(3); // 设置步骤为"调整订单"
            } else {
                throw new Error(data.message || '识别失败');
            }
        })
        .catch(error => {
            alert('识别失败: ' + error.message);
            uploadSection.style.display = 'block';
            processingIndicator.style.display = 'none';
            setCurrentStep(1); // 返回到上传步骤
        });
    }
    
    // 显示识别结果
    function showRecognitionResults() {
        processingIndicator.style.display = 'none';
        recognitionResults.style.display = 'block';
        
        // 如果没有识别到商品，显示提示
        if (orderItems.length === 0) {
            orderItemsList.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i> 未识别到任何商品，请调整照片后重试
                </div>
            `;
        }
    }
    
    // 更新订单项目
    function updateOrderItems() {
        orderItemsList.innerHTML = '';
        totalAmount = 0;
        
        orderItems.forEach((item, index) => {
            const confidenceClass = getConfidenceClass(item.confidence);
            
            const itemElement = document.createElement('div');
            itemElement.className = 'order-item';
            itemElement.innerHTML = `
                <div class="item-details">
                    <div>
                        <span class="confidence-indicator ${confidenceClass}"></span>
                        <span class="item-name-editable" data-index="${index}">${item.name}</span>
                    </div>
                    <div class="small text-muted">
                        单价: ¥${item.price.toFixed(2)}
                    </div>
                </div>
                <div class="item-quantity">
                    <div class="quantity-control">
                        <button type="button" class="btn btn-sm btn-outline-secondary decrease-btn" data-index="${index}">-</button>
                        <input type="number" class="quantity-input" data-index="${index}" value="${item.quantity}" min="1">
                        <button type="button" class="btn btn-sm btn-outline-secondary increase-btn" data-index="${index}">+</button>
                    </div>
                </div>
                <div class="item-subtotal ms-3 text-nowrap">
                    ¥${(item.price * item.quantity).toFixed(2)}
                </div>
                <button type="button" class="btn btn-sm btn-link text-danger remove-item" data-index="${index}">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            
            orderItemsList.appendChild(itemElement);
            totalAmount += item.price * item.quantity;
        });
        
        // 更新总金额显示
        totalAmountSpan.textContent = `¥${totalAmount.toFixed(2)}`;
        
        // 添加事件监听器
        addOrderItemEventListeners();
    }
    
    // 添加订单项目的事件监听器
    function addOrderItemEventListeners() {
        // 数量减少按钮
        document.querySelectorAll('.decrease-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                if (orderItems[index].quantity > 1) {
                    orderItems[index].quantity--;
                    updateItemQuantity(index, orderItems[index].quantity);
                }
            });
        });
        
        // 数量增加按钮
        document.querySelectorAll('.increase-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                orderItems[index].quantity++;
                updateItemQuantity(index, orderItems[index].quantity);
            });
        });
        
        // 数量输入框
        document.querySelectorAll('.quantity-input').forEach(input => {
            input.addEventListener('change', function() {
                const index = parseInt(this.getAttribute('data-index'));
                const newQuantity = Math.max(1, parseInt(this.value) || 1);
                this.value = newQuantity; // 确保显示的值有效
                orderItems[index].quantity = newQuantity;
                updateItemQuantity(index, newQuantity);
            });
        });
        

        // 删除商品按钮
        document.querySelectorAll('.remove-item').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                removeOrderItem(index);
            });
        });
        
        // 商品名称点击编辑
        document.querySelectorAll('.item-name-editable').forEach(nameElement => {
            nameElement.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                const currentName = orderItems[index].name;
                const newName = prompt('修改商品名称', currentName);
                
                if (newName && newName.trim() !== '' && newName !== currentName) {
                    // 调用API更新商品名称
                    updateItemName(index, newName.trim());
                }
            });
        });
    }
    
    // 更新商品数量
    function updateItemQuantity(index, newQuantity) {
        // 本地更新UI
        const quantityInputs = document.querySelectorAll('.quantity-input');
        if (quantityInputs[index]) {
            quantityInputs[index].value = newQuantity;
        }
        
        // 更新小计金额
        const subtotalElements = document.querySelectorAll('.item-subtotal');
        if (subtotalElements[index]) {
            const subtotal = orderItems[index].price * newQuantity;
            subtotalElements[index].textContent = `¥${subtotal.toFixed(2)}`;
        }
        
        // 更新总金额
        calculateTotal();
        
        // 调用API更新数量
        if (currentSessionId) {
            fetch('/mlsp/api/order-recognition/update-item-quantity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    item_index: index,
                    quantity: newQuantity
                })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    console.error('更新数量失败:', data.message);
                }
            })
            .catch(error => {
                console.error('更新数量请求失败:', error);
            });
        }
    }
    
    // 更新商品名称
    function updateItemName(index, newName) {
        // 本地更新UI
        const nameElements = document.querySelectorAll('.item-name-editable');
        if (nameElements[index]) {
            nameElements[index].textContent = newName;
        }
        
        // 更新本地数据
        orderItems[index].name = newName;
        
        // 调用API进行适应性调整
        if (currentSessionId) {
            fetch('/mlsp/api/order-recognition/adjust-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    message: `将商品"${orderItems[index].original_name || ''}"修改为"${newName}"`
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 更新订单项
                    orderItems = data.items || orderItems;
                    updateOrderItems();
                    
                    // 添加AI消息到对话
                    addChatMessage('将商品修改为"' + newName + '"', 'user');
                    if (data.message) {
                        addChatMessage(data.message, 'ai');
                    } else {
                        addChatMessage('已更新商品信息', 'ai');
                    }
                } else {
                    console.error('调整订单失败:', data.message);
                    addChatMessage('抱歉，无法更新商品名称', 'ai');
                }
            })
            .catch(error => {
                console.error('调整订单请求失败:', error);
                addChatMessage('网络错误，无法更新商品名称', 'ai');
            });
        }
    }
    
    // 移除订单项
    function removeOrderItem(index) {
        // 保存要移除的商品名称
        const itemName = orderItems[index].name;
        
        // 本地移除
        orderItems.splice(index, 1);
        updateOrderItems();
        
        // 调用API
        if (currentSessionId) {
            fetch('/mlsp/api/order-recognition/adjust-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    message: `删除商品"${itemName}"`
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 添加AI消息到对话
                    addChatMessage(`删除商品"${itemName}"`, 'user');
                    if (data.message) {
                        addChatMessage(data.message, 'ai');
                    } else {
                        addChatMessage(`已删除商品"${itemName}"`, 'ai');
                    }
                } else {
                    console.error('删除商品失败:', data.message);
                }
            })
            .catch(error => {
                console.error('删除商品请求失败:', error);
            });
        }
    }
    
    // 计算订单总金额
    function calculateTotal() {
        totalAmount = orderItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        totalAmountSpan.textContent = `¥${totalAmount.toFixed(2)}`;
    }
    
    // 获取商品置信度对应的类名
    function getConfidenceClass(confidence) {
        if (!confidence) return 'confidence-medium';
        
        if (confidence >= 0.8) {
            return 'confidence-high';
        } else if (confidence >= 0.5) {
            return 'confidence-medium';
        } else {
            return 'confidence-low';
        }
    }
    
    // 初始化对话功能
    function initChat() {
        // 切换对话区域显示
        toggleChatBtn.addEventListener('click', function() {
            if (chatSection.style.display === 'none' || chatSection.style.display === '') {
                chatSection.style.display = 'block';
                this.innerHTML = '<i class="bi bi-chat-square-dots-fill"></i> 关闭对话';
            } else {
                chatSection.style.display = 'none';
                this.innerHTML = '<i class="bi bi-chat"></i> 对话调整';
            }
        });
        
        // 发送消息
        sendMessageBtn.addEventListener('click', sendMessage);
        
        // 输入框回车发送
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // 快速建议标签
        suggestionTags.forEach(tag => {
            tag.addEventListener('click', function() {
                const message = this.getAttribute('data-message');
                messageInput.value = message;
                sendMessage();
            });
        });
    }
    
    // 发送对话消息
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // 添加用户消息到对话
        addChatMessage(message, 'user');
        
        // 清空输入框
        messageInput.value = '';
        
        // 调用API进行订单调整
        if (currentSessionId) {
            fetch('/mlsp/api/order-recognition/adjust-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    message: message
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 更新订单项
                    if (data.items && data.items.length > 0) {
                        orderItems = data.items;
                        updateOrderItems();
                    }
                    
                    // 添加AI回复
                    if (data.message) {
                        addChatMessage(data.message, 'ai');
                    }
                } else {
                    console.error('调整订单失败:', data.message);
                    addChatMessage('抱歉，无法处理您的请求', 'ai');
                }
            })
            .catch(error => {
                console.error('调整订单请求失败:', error);
                addChatMessage('网络错误，请稍后重试', 'ai');
            });
        }
    }
    
    // 添加对话消息
    function addChatMessage(text, type) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}-message`;
        messageElement.textContent = text;
        
        chatContainer.appendChild(messageElement);
        
        // 滚动到底部
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // 初始化确认订单功能
    function initConfirmation() {
        // 返回上传按钮
        backToUploadBtn.addEventListener('click', function() {
            recognitionResults.style.display = 'none';
            uploadSection.style.display = 'block';
            setCurrentStep(1);
        });
        
        // 确认订单按钮
        confirmOrderBtn.addEventListener('click', function() {
            // 显示确认页面
            recognitionResults.style.display = 'none';
            orderConfirmation.style.display = 'block';
            setCurrentStep(4);
            
            // 更新订单摘要
            updateOrderSummary();
        });
        
        // 返回调整按钮
        backToAdjustBtn.addEventListener('click', function() {
            orderConfirmation.style.display = 'none';
            recognitionResults.style.display = 'block';
            setCurrentStep(3);
        });
        
        // 提交订单按钮
        submitOrderBtn.addEventListener('click', submitOrder);
    }
    
    // 更新订单摘要
    function updateOrderSummary() {
        orderItemsSummary.innerHTML = '';
        
        orderItems.forEach(item => {
            const itemElement = document.createElement('div');
            itemElement.className = 'd-flex justify-content-between mb-2';
            itemElement.innerHTML = `
                <span>${item.name} × ${item.quantity}</span>
                <span>¥${(item.price * item.quantity).toFixed(2)}</span>
            `;
            
            orderItemsSummary.appendChild(itemElement);
        });
        
        // 更新总金额
        confirmTotalAmount.textContent = `¥${totalAmount.toFixed(2)}`;
    }
    
    // 提交订单
    function submitOrder() {
        // 禁用提交按钮防止重复提交
        submitOrderBtn.disabled = true;
        submitOrderBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 提交中...';
        
        if (currentSessionId) {
            fetch('/mlsp/api/order-recognition/confirm-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    note: orderNote.value.trim()
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 显示成功页面
                    orderConfirmation.style.display = 'none';
                    orderSuccess.style.display = 'block';
                    
                    // 显示订单ID
                    if (data.order_id) {
                        successOrderId.textContent = data.order_id;
                    }
                } else {
                    console.error('提交订单失败:', data.message);
                    alert('提交订单失败: ' + (data.message || '未知错误'));
                    
                    // 恢复提交按钮
                    submitOrderBtn.disabled = false;
                    submitOrderBtn.innerHTML = '<i class="bi bi-send-check"></i> 提交订单';
                }
            })
            .catch(error => {
                console.error('提交订单请求失败:', error);
                alert('网络错误，请稍后重试');
                
                // 恢复提交按钮
                submitOrderBtn.disabled = false;
                submitOrderBtn.innerHTML = '<i class="bi bi-send-check"></i> 提交订单';
            });
        }
    }
    
    // 初始化组件
    function init() {
        initUpload();
        initChat();
        initConfirmation();
        setCurrentStep(1);
    }
    
    // 启动应用
    init();
});
