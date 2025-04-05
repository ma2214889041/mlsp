// 添加到主屏幕指南
document.addEventListener('DOMContentLoaded', function() {
  // 检查是否已经作为应用运行
  if (window.matchMedia('(display-mode: standalone)').matches || 
      window.matchMedia('(display-mode: fullscreen)').matches ||
      window.navigator.standalone === true) {
    console.log('已作为应用运行');
    return;
  }
  
  // 检查是否已经提示过
  if (localStorage.getItem('homeScreenPrompt') === 'dismissed') {
    return;
  }
  
  // 延迟显示提示
  setTimeout(function() {
    // 创建提示元素
    var promptDiv = document.createElement('div');
    promptDiv.style.position = 'fixed';
    promptDiv.style.bottom = '0';
    promptDiv.style.left = '0';
    promptDiv.style.right = '0';
    promptDiv.style.backgroundColor = 'white';
    promptDiv.style.boxShadow = '0 -2px 10px rgba(0,0,0,0.1)';
    promptDiv.style.padding = '15px';
    promptDiv.style.zIndex = '9999';
    promptDiv.style.display = 'flex';
    promptDiv.style.justifyContent = 'space-between';
    promptDiv.style.alignItems = 'center';
    
    // 判断设备类型
    var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    var guideText = '';
    
    if (isIOS) {
      guideText = '点击 <strong>分享按钮</strong> 然后 <strong>"添加到主屏幕"</strong>';
    } else {
      guideText = '点击浏览器菜单然后 <strong>"添加到主屏幕"</strong>';
    }
    
    // 设置提示内容
    promptDiv.innerHTML = 
      '<div>' +
        '<strong>将网站添加到主屏幕</strong><br>' +
        '<small>' + guideText + '</small>' +
      '</div>' +
      '<div>' +
        '<button id="show-guide" style="background-color: #dc3545; color: white; border: none; padding: 8px 12px; border-radius: 4px; margin-right: 8px;">查看如何安装</button>' +
        '<button id="dismiss-prompt" style="background: none; border: none;">&times;</button>' +
      '</div>';
    
    // 添加到页面
    document.body.appendChild(promptDiv);
    
    // 关闭按钮事件
    document.getElementById('dismiss-prompt').addEventListener('click', function() {
      document.body.removeChild(promptDiv);
      localStorage.setItem('homeScreenPrompt', 'dismissed');
    });
    
    // 显示指南按钮事件
    document.getElementById('show-guide').addEventListener('click', function() {
      // 创建模态对话框
      var modalDiv = document.createElement('div');
      modalDiv.style.position = 'fixed';
      modalDiv.style.top = '0';
      modalDiv.style.left = '0';
      modalDiv.style.right = '0';
      modalDiv.style.bottom = '0';
      modalDiv.style.backgroundColor = 'rgba(0,0,0,0.7)';
      modalDiv.style.zIndex = '10000';
      modalDiv.style.display = 'flex';
      modalDiv.style.alignItems = 'center';
      modalDiv.style.justifyContent = 'center';
      
      var instructions = '';
      
      if (isIOS) {
        instructions = 
          '<p><strong>在iOS设备上安装:</strong></p>' +
          '<ol>' +
            '<li>点击Safari底部的<strong>分享按钮</strong> <span style="border: 1px solid #ddd; padding: 2px 8px; border-radius: 4px;">⬆️</span></li>' +
            '<li>滚动并选择<strong>"添加到主屏幕"</strong></li>' +
            '<li>点击右上角的<strong>"添加"</strong></li>' +
          '</ol>' +
          '<p>完成后，应用将显示在您的主屏幕上！</p>';
      } else {
        instructions = 
          '<p><strong>在Android设备上安装:</strong></p>' +
          '<ol>' +
            '<li>点击Chrome右上角的<strong>菜单按钮</strong> ⋮</li>' +
            '<li>选择<strong>"添加到主屏幕"</strong></li>' +
            '<li>点击<strong>"添加"</strong>确认</li>' +
          '</ol>' +
          '<p>完成后，应用将显示在您的主屏幕上！</p>';
      }
      
      // 模态框内容
      modalDiv.innerHTML = 
        '<div style="background-color: white; padding: 20px; border-radius: 8px; max-width: 90%; width: 350px;">' +
          '<div style="display: flex; justify-content: space-between; margin-bottom: 15px;">' +
            '<h3 style="margin: 0;">如何安装应用</h3>' +
            '<button id="close-modal" style="background: none; border: none; font-size: 20px;">&times;</button>' +
          '</div>' +
          instructions +
        '</div>';
      
      document.body.appendChild(modalDiv);
      
      // 关闭模态框
      document.getElementById('close-modal').addEventListener('click', function() {
        document.body.removeChild(modalDiv);
      });
    });
  }, 2000); // 2秒后显示
});
