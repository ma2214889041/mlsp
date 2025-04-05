document.addEventListener('DOMContentLoaded', function() {
    // 初始化日期选择器
    flatpickr(".datepicker", {
        dateFormat: "Y-m-d",
        locale: "zh",
        defaultDate: calculateDefaultExpiryDate(),
        minDate: "today",
        disableMobile: "true"
    });
    
    // 产品选择变更时更新单位显示和默认过期日期
    const productSelect = document.getElementById('product_id');
    const unitAddon = document.getElementById('unit-addon');
    const expiryDateInput = document.getElementById('expiry_date');
    
    if (productSelect) {
        productSelect.addEventListener('change', function() {
            // 获取选中的选项
            const selectedOption = this.options[this.selectedIndex];
            
            // 更新单位显示
            if (selectedOption.dataset.unit) {
                unitAddon.textContent = selectedOption.dataset.unit;
            } else {
                unitAddon.textContent = "份";
            }
            
            // 更新默认过期日期
            if (selectedOption.dataset.expiry) {
                const expiryDays = parseInt(selectedOption.dataset.expiry);
                const expiry = new Date();
                expiry.setDate(expiry.getDate() + expiryDays);
                
                // 更新日期选择器
                flatpickr(expiryDateInput, {
                    dateFormat: "Y-m-d",
                    locale: "zh",
                    defaultDate: expiry,
                    minDate: "today",
                    disableMobile: "true"
                });
            }
        });
    }
    
    // 货架位置选择逻辑
    const shelfSelect = document.getElementById('shelf_id');
    const slotSelect = document.getElementById('slot_id');
    
    if (shelfSelect && slotSelect) {
        // 当选择货架时加载该货架的所有可用货位
        shelfSelect.addEventListener('change', function() {
            const selectedShelfId = this.value;
            
            // 清空当前货位选项
            slotSelect.innerHTML = '<option value="">选择货位(可选)</option>';
            
            if (selectedShelfId) {
                // 向服务器请求该货架的所有货位
                fetch(`/admin/api/shelf/${selectedShelfId}/slots`)
                    .then(response => response.json())
                    .then(data => {
                        console.log("获取到的货位数据:", data);
                        if (data.slots && data.slots.length > 0) {
                            // 添加所有货位选项
                            data.slots.forEach(slot => {
                                const option = document.createElement('option');
                                option.value = slot.id;
                                option.textContent = slot.position;
                                slotSelect.appendChild(option);
                            });
                        } else {
                            // 没有可用货位
                            const option = document.createElement('option');
                            option.disabled = true;
                            option.textContent = "该货架没有可用货位";
                            slotSelect.appendChild(option);
                        }
                    })
                    .catch(error => {
                        console.error("加载货位失败:", error);
                    });
            }
        });
    }
    
    // 计算默认过期日期（一年后）
    function calculateDefaultExpiryDate() {
        const today = new Date();
        const nextYear = new Date(today);
        nextYear.setFullYear(today.getFullYear() + 1);
        return nextYear;
    }
});
