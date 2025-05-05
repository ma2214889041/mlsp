// 修复AI订单识别功能 v3 - Enhanced Logging
document.addEventListener('DOMContentLoaded', function() {
    console.log("订单识别页面初始化 v3...");

    // 获取聊天相关元素
    const chatInput = document.getElementById('chat-input');
    const sendMessage = document.getElementById('send-message');
    const chatMessages = document.getElementById('chat-messages');

    // 获取订单项目区域
    const itemsContent = document.getElementById('items-content'); // Target the correct container
    const productPreviewContainer = document.getElementById('product-preview'); // This is where items go
    const emptyItemsState = document.getElementById('empty-items-state');
    const totalSection = document.getElementById('total-section'); // This holds the total amount display
    const totalAmountElement = document.getElementById('total-amount'); // The span for the total amount

    // 全局变量
    window.sessionId = '';
    window.productList = [];
    console.log("Initial window.productList:", JSON.stringify(window.productList));

    // 发送聊天消息
    async function sendChatMessage(message) {
        console.log("sendChatMessage: 发送消息:", message);
        if (!chatMessages) return;

        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'message user-message';
        userMessageDiv.textContent = message;
        chatMessages.appendChild(userMessageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        if (!window.sessionId) {
            const aiMessageDiv = document.createElement('div');
            aiMessageDiv.className = 'message ai-message';
            aiMessageDiv.textContent = '请先上传订单照片';
            chatMessages.appendChild(aiMessageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            return;
        }

        try {
            const formData = new FormData();
            formData.append('session_id', window.sessionId);
            formData.append('message', message);

            const response = await fetch('/mlsp/api/order-recognition/adjust-order', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            console.log("sendChatMessage: 收到后端响应:", result);

            if (result.success) {
                const aiMessageDiv = document.createElement('div');
                aiMessageDiv.className = 'message ai-message';
                aiMessageDiv.textContent = result.response;
                chatMessages.appendChild(aiMessageDiv);

                if (result.products && Array.isArray(result.products)) {
                    console.log("sendChatMessage: 准备更新产品列表 (来自adjust):", JSON.stringify(result.products));
                    window.productList = result.products;
                    console.log("sendChatMessage: 更新后 window.productList:", JSON.stringify(window.productList));

                    const itemsTab = document.getElementById('items-tab');
                    if (itemsTab) {
                         const itemsContent = document.getElementById('items-content');
                         const chatContent = document.getElementById('chat-content');
                         const addContent = document.getElementById('add-content');
                         if (itemsContent) itemsContent.style.display = 'block';
                         if (chatContent) chatContent.style.display = 'none';
                         if (addContent) addContent.style.display = 'none';
                         itemsTab.classList.add('active');
                         document.getElementById('chat-tab')?.classList.remove('active');
                         document.getElementById('add-tab')?.classList.remove('active');
                         console.log("sendChatMessage: 已切换到 Items Tab");
                    } else {
                         console.warn("sendChatMessage: Items Tab 未找到");
                    }
                    updateProductDisplay(); // Directly update the display
                } else {
                    console.warn("sendChatMessage: 调整成功但响应中无产品列表");
                }
            } else {
                const aiMessageDiv = document.createElement('div');
                aiMessageDiv.className = 'message ai-message';
                aiMessageDiv.textContent = result.message || '处理消息时出错';
                chatMessages.appendChild(aiMessageDiv);
            }
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } catch (error) {
            console.error('sendChatMessage: 发送消息失败:', error);
            const aiMessageDiv = document.createElement('div');
            aiMessageDiv.className = 'message ai-message';
            aiMessageDiv.textContent = '网络错误，请稍后重试';
            chatMessages.appendChild(aiMessageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // 更新产品显示
    function updateProductDisplay() {
        // *** LOGGING START ***
        console.log(">>> updateProductDisplay: 开始执行");
        console.log(">>> updateProductDisplay: 当前 window.productList:", JSON.stringify(window.productList));
        // *** LOGGING END ***

        if (!productPreviewContainer || !emptyItemsState || !totalSection || !totalAmountElement) {
            console.error("updateProductDisplay: 找不到必要的商品列表、空状态或总计元素");
            return;
        }

        productPreviewContainer.innerHTML = '';

        if (!window.productList || !Array.isArray(window.productList) || window.productList.length === 0) {
            console.log("updateProductDisplay: 产品列表为空或无效，显示空状态");
            emptyItemsState.style.display = 'block';
            totalSection.style.display = 'none';
            // Ensure empty state is inside the container if it exists
            if (emptyItemsState.parentNode !== productPreviewContainer) {
                productPreviewContainer.appendChild(emptyItemsState);
            }
            return;
        }

        console.log(`updateProductDisplay: 准备显示 ${window.productList.length} 个产品`);
        emptyItemsState.style.display = 'none';
        totalSection.style.display = 'block';

        let totalAmount = 0;
        window.productList.forEach((product, index) => {
            // *** LOGGING START ***
            console.log(`>>> updateProductDisplay: 处理产品索引 ${index}:`, JSON.stringify(product));
            // *** LOGGING END ***
            if (!product || typeof product.price !== 'number' || typeof product.quantity !== 'number' || !product.name) {
                 console.warn(`updateProductDisplay: 跳过无效的产品数据 at index ${index}:`, product);
                 return;
             }
            const itemPrice = product.price * product.quantity;
            totalAmount += itemPrice;

            const itemCard = document.createElement('div');
            itemCard.className = 'item-card';
            itemCard.innerHTML = `
                <i class="bi bi-x-circle remove-item" data-index="${index}" style="position: absolute; top: 10px; right: 10px; cursor: pointer; color: #dc3545; font-size: 1.2rem;"></i>
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
                    </div>
                </div>
            `;
            productPreviewContainer.appendChild(itemCard);
        });

        totalAmountElement.textContent = `¥${totalAmount.toFixed(2)}`;
        attachButtonListeners();
        console.log("updateProductDisplay: 产品显示更新完成");
    }

    // Function to attach event listeners
    function attachButtonListeners() {
         console.log("Attaching button listeners...");
         document.querySelectorAll('.decrease-btn').forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            newBtn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                 console.log("Decrease clicked, index:", index);
                 // Add check if product exists at index
                if (window.productList && window.productList[index] && window.productList[index].quantity > 0) { // Allow decreasing to 0 (will be handled by updateItemQuantity logic)
                     updateItemQuantity(window.productList[index].id, window.productList[index].quantity - 1);
                 } else {
                    console.warn("Cannot decrease, product not found or quantity already 0 for index:", index);
                 }
            });
        });

        document.querySelectorAll('.increase-btn').forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            newBtn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                 console.log("Increase clicked, index:", index);
                 if (window.productList && window.productList[index]) {
                    updateItemQuantity(window.productList[index].id, window.productList[index].quantity + 1);
                 } else {
                     console.warn("Cannot increase, product not found for index:", index);
                 }
            });
        });

        document.querySelectorAll('.remove-item').forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            newBtn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                 console.log("Remove clicked, index:", index);
                 if (window.productList && window.productList[index] && confirm(`确定要移除 ${window.productList[index].name} 吗？`)) {
                    updateItemQuantity(window.productList[index].id, 0); // Set quantity to 0 to remove
                 } else {
                     console.warn("Cannot remove, product not found for index:", index);
                 }
            });
        });
         console.log("Button listeners attached.");
    }

    // 更新商品数量
    async function updateItemQuantity(productId, quantity) {
        console.log(`updateItemQuantity: 更新商品数量: ID=${productId}, 数量=${quantity}`);
        if (!window.sessionId) {
            console.error('updateItemQuantity: 没有活动会话');
            alert('会话无效，请重新上传照片。');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('session_id', window.sessionId);
            formData.append('product_id', productId);
            formData.append('quantity', quantity); // Send 0 if removing

            const response = await fetch('/mlsp/api/order-recognition/update-item-quantity', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
             console.log("updateItemQuantity: 收到后端响应:", result);

            if (result.success) {
                if (result.products && Array.isArray(result.products)) {
                    console.log("updateItemQuantity: 准备更新产品列表:", JSON.stringify(result.products));
                    window.productList = result.products; // Update global list
                    console.log("updateItemQuantity: 更新后 window.productList:", JSON.stringify(window.productList));
                    updateProductDisplay(); // Refresh display
                } else {
                    console.warn("updateItemQuantity: 更新成功但响应中无产品列表?");
                    // If removing last item, backend might send empty list
                    window.productList = []; // Assume empty if not provided
                    updateProductDisplay();
                }
            } else {
                console.error('updateItemQuantity: 更新商品数量失败:', result.message);
                alert(result.message || '更新商品数量失败');
            }
        } catch (error) {
            console.error('updateItemQuantity: 网络错误:', error);
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
        uploadTrigger.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                    uploadTrigger.style.display = 'none';
                    imagePreview.style.display = 'block';
                    console.log("File selected, resetting product list.");
                    window.productList = [];
                    updateProductDisplay(); // Show empty state initially
                };
                reader.readAsDataURL(file);
            }
        });
    }

    const cancelPreviewBtn = document.getElementById('cancel-preview');
    if (cancelPreviewBtn) {
        cancelPreviewBtn.addEventListener('click', function() {
             console.log("Cancel preview clicked.");
            fileInput.value = '';
            previewImage.src = '#';
            imagePreview.style.display = 'none';
            uploadTrigger.style.display = 'block';
            window.productList = [];
            window.sessionId = '';
            updateProductDisplay();
             if (chatMessages) chatMessages.innerHTML = '<div class="message ai-message">您好！我是您的智能助手...</div>';
             updateStepIndicators(0);
        });
    }

    if (processImage) {
        processImage.addEventListener('click', async function() {
            console.log("Process image clicked.");
            if (!fileInput || !fileInput.files.length) {
                alert('请先选择图片');
                return;
            }

            processingIndicator.style.display = 'flex';
            imagePreview.style.display = 'none'; // Hide preview during processing

            try {
                const formData = new FormData();
                formData.append('photo', fileInput.files[0]);
                console.log("processImage: Sending photo to backend...");

                const response = await fetch('/mlsp/api/order-recognition/upload-photo', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                // *** LOGGING START ***
                console.log("processImage: 上传照片结果:", JSON.stringify(result, null, 2)); // Log the raw result prettified
                // *** LOGGING END ***

                if (result.success) {
                    window.sessionId = result.session_id;
                     console.log("processImage: Session ID set:", window.sessionId);

                    // --- MODIFICATION START: Assign result.products correctly ---
                    console.log("processImage: Raw result.products:", JSON.stringify(result.products)); // Log before assignment
                    if (result.products && Array.isArray(result.products)) {
                         window.productList = result.products;
                         // *** LOGGING START ***
                         console.log("processImage: Assigned window.productList:", JSON.stringify(window.productList)); // Log after assignment
                         // *** LOGGING END ***
                     } else {
                         console.warn("processImage: API returned success but 'products' is missing or not an array.");
                         window.productList = [];
                         console.log("processImage: Set window.productList to empty array.");
                     }
                    // --- MODIFICATION END ---

                    if (chatMessages) {
                        chatMessages.innerHTML = '';
                        const welcomeMessage = document.createElement('div');
                        welcomeMessage.className = 'message ai-message';
                        welcomeMessage.textContent = '订单照片上传成功！已识别出以下商品 (模拟返回所有产品)，您可以通过对话进行调整。';
                        chatMessages.appendChild(welcomeMessage);
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    }

                    const uploadStep = document.getElementById('upload-step');
                    const adjustStep = document.getElementById('adjust-step');
                    if (uploadStep && adjustStep) {
                        uploadStep.style.display = 'none';
                        adjustStep.style.display = 'block';
                         console.log("processImage: Switched to Adjust Step.");
                        updateStepIndicators(1);
                        // *** Call updateProductDisplay AFTER switching steps and ensuring list is set ***
                         console.log("processImage: Calling updateProductDisplay...");
                        updateProductDisplay(); // Display the newly assigned list
                    } else {
                         console.error("processImage: Upload or Adjust step element not found!");
                    }
                } else {
                    alert(result.message || '照片上传或识别失败');
                    if (uploadTrigger) uploadTrigger.style.display = 'block'; // Show upload button again
                    if(imagePreview) imagePreview.style.display = 'none'; // Keep preview hidden
                }
            } catch (error) {
                console.error('processImage: 上传或识别照片失败:', error);
                alert('网络错误，请稍后重试');
                if (uploadTrigger) uploadTrigger.style.display = 'block';
                 if(imagePreview) imagePreview.style.display = 'none';
            } finally {
                if (processingIndicator) processingIndicator.style.display = 'none';
                 console.log("processImage: Processing finished.");
            }
        });
    }

    // --- Rest of the functions (sendChatMessage, updateStepIndicators, confirm/submit logic, tabs, search) remain largely the same ---
    // --- Ensure necessary elements are grabbed and functions called appropriately ---

    // (Include the rest of the functions: updateStepIndicators, confirm/submit logic, tabs, search logic from previous version here)
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

        stepIcons.forEach((icon, i) => {
            if (icon) icon.classList.remove('active', 'completed');
            if (stepTexts[i]) stepTexts[i].classList.remove('active');
        });
        stepLines.forEach(line => {
            if (line) line.classList.remove('active');
        });
        for (let i = 0; i < activeStep; i++) {
            if (stepIcons[i]) stepIcons[i].classList.add('completed');
            if (i < stepLines.length && stepLines[i]) stepLines[i].classList.add('active');
        }
        if (activeStep < stepIcons.length && stepIcons[activeStep]) {
            stepIcons[activeStep].classList.add('active');
            if (stepTexts[activeStep]) stepTexts[activeStep].classList.add('active');
        }
         console.log("Updated step indicators to step", activeStep);
    }

    // 确认订单
    const goToConfirm = document.getElementById('go-to-confirm');
    const confirmStep = document.getElementById('confirm-step');
    const adjustStep = document.getElementById('adjust-step'); // Ensure this is defined
    const finalProductList = document.getElementById('final-product-list');
    const finalTotalAmount = document.getElementById('final-total-amount');

    if (goToConfirm) {
        goToConfirm.addEventListener('click', function() {
            console.log("Go to confirm clicked.");
            if (!window.productList || window.productList.length === 0) {
                alert('请至少添加一件商品');
                return;
            }

            if (finalProductList && finalTotalAmount) {
                finalProductList.innerHTML = '';
                let totalAmount = 0;
                window.productList.forEach(product => {
                     if (!product || typeof product.price !== 'number' || typeof product.quantity !== 'number') return;
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
                finalTotalAmount.textContent = `¥${totalAmount.toFixed(2)}`;
                 console.log("Final product list updated for confirmation.");
            }

            if (adjustStep && confirmStep) {
                adjustStep.style.display = 'none';
                confirmStep.style.display = 'block';
                updateStepIndicators(2);
                console.log("Switched to Confirm Step.");
            } else {
                 console.error("Adjust or Confirm step element not found for switching!");
            }
        });
    }

    // 返回调整步骤
    const backToAdjust = document.getElementById('back-to-adjust');
    if (backToAdjust) {
        backToAdjust.addEventListener('click', function() {
             console.log("Back to adjust clicked.");
            if (adjustStep && confirmStep) {
                confirmStep.style.display = 'none';
                adjustStep.style.display = 'block';
                updateStepIndicators(1);
                console.log("Switched back to Adjust Step.");
            }
        });
    }

    // 提交订单
    const submitOrder = document.getElementById('submit-order');
    const orderNote = document.getElementById('order-note');
    const successStep = document.getElementById('success-step');
    const orderIdElement = document.getElementById('order-id');
    if (submitOrder) {
        submitOrder.addEventListener('click', async function() {
             console.log("Submit order clicked.");
            if (!window.sessionId) { alert('会话已过期，请重新开始'); return; }
            if (!window.productList || window.productList.length === 0) { alert('订单为空，无法提交'); return; }

            submitOrder.disabled = true;
            submitOrder.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 提交中...';

            try {
                const formData = new FormData();
                formData.append('session_id', window.sessionId);
                if (orderNote && orderNote.value) formData.append('note', orderNote.value);

                const response = await fetch('/mlsp/api/order-recognition/confirm-order', { method: 'POST', body: formData });
                const result = await response.json();
                 console.log("Submit order response:", result);

                if (result.success) {
                    if (orderIdElement) orderIdElement.textContent = result.order_id;
                    if (confirmStep && successStep) {
                        confirmStep.style.display = 'none';
                        successStep.style.display = 'block';
                        updateStepIndicators(3);
                        console.log("Order submitted successfully, switched to Success Step.");
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
    const chatContent = document.getElementById('chat-content'); // Ensure defined
    const addContent = document.getElementById('add-content');   // Ensure defined

    if (itemsTab && chatTab && addTab && itemsContent && chatContent && addContent) {
        itemsTab.addEventListener('click', function() {
             console.log("Items tab clicked");
            itemsTab.classList.add('active'); chatTab.classList.remove('active'); addTab.classList.remove('active');
            itemsContent.style.display = 'block'; chatContent.style.display = 'none'; addContent.style.display = 'none';
            updateProductDisplay();
        });
        chatTab.addEventListener('click', function() {
             console.log("Chat tab clicked");
            chatTab.classList.add('active'); itemsTab.classList.remove('active'); addTab.classList.remove('active');
            chatContent.style.display = 'block'; itemsContent.style.display = 'none'; addContent.style.display = 'none';
        });
        addTab.addEventListener('click', function() {
             console.log("Add tab clicked");
            addTab.classList.add('active'); itemsTab.classList.remove('active'); chatTab.classList.remove('active');
            addContent.style.display = 'block'; itemsContent.style.display = 'none'; chatContent.style.display = 'none';
        });
    }

    // --- Initialize Product Search ---
    const productSearchInput = document.getElementById('product-search');
    const searchResultsContainer = document.getElementById('search-results');
    const addQuantityInput = document.getElementById('add-quantity');
    const addProductButton = document.getElementById('add-product');
    const decreaseQtyBtn = document.getElementById('decrease-quantity');
    const increaseQtyBtn = document.getElementById('increase-quantity');
    let selectedProductFromSearch = null;

    if (productSearchInput && searchResultsContainer && addProductButton) {
        function debounce(func, wait) { /* ... debounce implementation ... */
             let timeout;
             return function executedFunction(...args) {
                 const later = () => { clearTimeout(timeout); func(...args); };
                 clearTimeout(timeout);
                 timeout = setTimeout(later, wait);
             };
        }
        productSearchInput.addEventListener('input', debounce(async function() { /* ... search logic ... */
             const query = productSearchInput.value.trim();
             if (query.length < 1) { /* ... clear results ... */
                 searchResultsContainer.innerHTML = ''; searchResultsContainer.style.display = 'none'; addProductButton.disabled = true; selectedProductFromSearch = null; return;
             }
             if (!window.sessionId) { /* ... handle no session ... */
                 console.warn("Search: No session ID"); searchResultsContainer.innerHTML = '<div class="search-item text-muted">请先上传订单照片</div>'; searchResultsContainer.style.display = 'block'; addProductButton.disabled = true; selectedProductFromSearch = null; return;
             }
             try { /* ... fetch and display search results ... */
                 const response = await fetch(`/mlsp/api/order-recognition/products/search?query=${encodeURIComponent(query)}`);
                 const data = await response.json();
                 searchResultsContainer.innerHTML = '';
                 if (data.success && data.products && data.products.length > 0) {
                     data.products.forEach(product => {
                         const item = document.createElement('div'); item.className = 'search-item'; item.textContent = `${product.name} (¥${product.price.toFixed(2)})`;
                         item.addEventListener('click', () => { productSearchInput.value = product.name; selectedProductFromSearch = product; searchResultsContainer.style.display = 'none'; addProductButton.disabled = false; addQuantityInput.value = 1; });
                         searchResultsContainer.appendChild(item);
                     });
                     searchResultsContainer.style.display = 'block';
                 } else { /* ... handle no results ... */
                     searchResultsContainer.innerHTML = '<div class="search-item text-muted">未找到产品</div>'; searchResultsContainer.style.display = 'block'; addProductButton.disabled = true; selectedProductFromSearch = null;
                 }
             } catch (error) { /* ... handle search error ... */
                 console.error('搜索产品失败:', error); searchResultsContainer.innerHTML = '<div class="search-item text-danger">搜索出错</div>'; searchResultsContainer.style.display = 'block'; addProductButton.disabled = true; selectedProductFromSearch = null;
             }
         }, 300));
         document.addEventListener('click', function(event) { /* ... hide results on outside click ... */
             if (searchResultsContainer && productSearchInput && !productSearchInput.contains(event.target) && !searchResultsContainer.contains(event.target)) { searchResultsContainer.style.display = 'none'; }
         });
        addProductButton.addEventListener('click', () => { /* ... add product logic ... */
             console.log("Add product button clicked");
             if (selectedProductFromSearch) {
                 const quantity = parseInt(addQuantityInput.value);
                 if (quantity > 0) {
                     const existingIndex = window.productList.findIndex(p => p.id === selectedProductFromSearch.id);
                     const finalQuantity = existingIndex !== -1 ? window.productList[existingIndex].quantity + quantity : quantity;
                     console.log(`Adding/Updating product ${selectedProductFromSearch.id} with quantity ${finalQuantity}`);
                     updateItemQuantity(selectedProductFromSearch.id, finalQuantity);
                     productSearchInput.value = ''; selectedProductFromSearch = null; addProductButton.disabled = true; addQuantityInput.value = 1;
                     if(itemsTab) itemsTab.click();
                 } else { alert('请输入有效的数量'); }
             }
         });
        if(decreaseQtyBtn && increaseQtyBtn && addQuantityInput){ /* ... quantity controls ... */
             decreaseQtyBtn.addEventListener('click', () => { let cv = parseInt(addQuantityInput.value); if (cv > 1) addQuantityInput.value = cv - 1; });
             increaseQtyBtn.addEventListener('click', () => { let cv = parseInt(addQuantityInput.value); addQuantityInput.value = cv + 1; });
             addQuantityInput.addEventListener('change', () => { let cv = parseInt(addQuantityInput.value); if (isNaN(cv) || cv < 1) addQuantityInput.value = 1; });
        }
    }
    // --- End Initialize Product Search ---

     // Initial setup
     const initialUploadStep = document.getElementById('upload-step');
     const initialAdjustStep = document.getElementById('adjust-step');
     const initialConfirmStep = document.getElementById('confirm-step');
     const initialSuccessStep = document.getElementById('success-step');

     if(initialUploadStep) initialUploadStep.style.display = 'block';
     if(initialAdjustStep) initialAdjustStep.style.display = 'none';
     if(initialConfirmStep) initialConfirmStep.style.display = 'none';
     if(initialSuccessStep) initialSuccessStep.style.display = 'none';
     updateStepIndicators(0);
     console.log("Initial setup complete. Showing Upload Step.");

});
