// 判断当前应用类型并设置相应变量
let appType = "default";
let appName = "米兰食品系统";
let appIcon = "/static/icons/client.png";
let manifestPath = "/static/basic-manifest.json";

if (window.location.pathname.startsWith('/client')) {
  appType = "client";
  appName = "米兰客户端";
  appIcon = "/static/icons/client.png";
  manifestPath = "/static/client-manifest.json";
} else if (window.location.pathname.startsWith('/admin')) {
  appType = "admin";
  appName = "米兰管理端";
  appIcon = "/static/icons/admin.png";
  manifestPath = "/static/admin-manifest.json";
} else if (window.location.pathname.startsWith('/employee')) {
  appType = "employee";
  appName = "米兰仓库端";
  appIcon = "/static/icons/employee.png";
  manifestPath = "/static/employee-manifest.json";
}

// 动态添加manifest链接
const linkEl = document.createElement('link');
linkEl.rel = 'manifest';
linkEl.href = manifestPath;
document.head.appendChild(linkEl);

// 设置Apple Touch Icon
const touchIconEl = document.createElement('link');
touchIconEl.rel = 'apple-touch-icon';
touchIconEl.href = appIcon;
document.head.appendChild(touchIconEl);

// 检查是否已经作为应用运行
if (window.matchMedia('(display-mode: standalone)').matches || 
    window.matchMedia('(display-mode: fullscreen)').matches ||
    window.navigator.standalone === true) {
  console.log('已作为应用运行');
} else {
  // 检查是否已经提示过或者用户已安装
  const storageKey = `${appType}_pwa_installed`;
  const dismissKey = `${appType}_pwa_dismissed`;
  const lastDismissed = localStorage.getItem(dismissKey);
  const now = new Date().getTime();
  
  // 如果尚未安装且未在24小时内被关闭，则显示安装提示
  if (!localStorage.getItem(storageKey) && 
      (!lastDismissed || (now - lastDismissed) > 24 * 60 * 60 * 1000)) {
    // 延迟显示，以便页面加载完成
    setTimeout(() => {
      showInstallPrompt();
    }, 2000);
  }
}

// 显示安装提示
function showInstallPrompt() {
  const promptDiv = document.createElement('div');
  promptDiv.id = 'pwa-install-prompt';
  promptDiv.style.position = 'fixed';
  promptDiv.style.bottom = '0';
  promptDiv.style.left = '0';
  promptDiv.style.right = '0';
  promptDiv.style.backgroundColor = 'white';
  promptDiv.style.boxShadow = '0 -2px 10px rgba(0,0,0,0.2)';
  promptDiv.style.padding = '15px';
  promptDiv.style.zIndex = '9999';
  promptDiv.style.display = 'flex';
  promptDiv.style.justifyContent = 'space-between';
  promptDiv.style.alignItems = 'center';
  
  // 判断设备类型
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  let installGuideText = '';
  
  if (isIOS) {
    installGuideText = '点击分享按钮，然后"添加到主屏幕"';
  } else {
    installGuideText = '点击菜单，然后"安装应用"';
  }
  
  promptDiv.innerHTML = `
    <div style="display: flex; align-items: center;">
      <img src="${appIcon}" style="width: 40px; height: 40px; margin-right: 10px; border-radius: 8px;">
      <div>
        <div style="font-weight: bold;">${appName}</div>
        <div style="font-size: 0.8em; color: #666;">${installGuideText}</div>
      </div>
    </div>
    <div>
      <button id="pwa-install-guide" style="background-color: #007bff; color: white; border: none; border-radius: 4px; padding: 8px 12px; margin-right: 8px;">安装指南</button>
      <button id="pwa-dismiss" style="background: none; border: none; font-size: 20px;">×</button>
    </div>
  `;
  
  document.body.appendChild(promptDiv);
  
  // 安装指南按钮事件
  document.getElementById('pwa-install-guide').addEventListener('click', () => {
    showInstallGuide();
  });
  
  // 关闭按钮事件
  document.getElementById('pwa-dismiss').addEventListener('click', () => {
    document.body.removeChild(promptDiv);
    localStorage.setItem(`${appType}_pwa_dismissed`, new Date().getTime());
  });
}

// 显示安装指南
function showInstallGuide() {
  const modalDiv = document.createElement('div');
  modalDiv.id = 'pwa-install-guide';
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
  
  // 判断设备类型
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isChrome = /chrome|crios/i.test(navigator.userAgent);
  const isSafari = /safari/i.test(navigator.userAgent) && !isChrome;
  
  let guideContent = '';
  
  if (isIOS) {
    if (isSafari) {
      guideContent = `
        <h4>在iPhone/iPad上安装${appName}</h4>
        <div style="margin: 15px 0;">
          <img src="/static/icons/${appType}.png" style="width: 60px; height: 60px; border-radius: 12px;">
        </div>
        <ol style="text-align: left; padding-left: 20px;">
          <li>点击屏幕底部的<strong>分享按钮</strong> <span style="border: 1px solid #ddd; padding: 2px 8px; border-radius: 4px;">⬆️</span></li>
          <li>在弹出的菜单中滚动找到<strong>"添加到主屏幕"</strong></li>
          <li>点击<strong>"添加"</strong>完成安装</li>
        </ol>
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 15px;">
          <strong>注意:</strong> 必须使用Safari浏览器才能添加到主屏幕
        </div>
      `;
    } else {
      guideContent = `
        <h4>在iPhone/iPad上安装${appName}</h4>
        <div style="margin: 15px 0;">
          <img src="/static/icons/${appType}.png" style="width: 60px; height: 60px; border-radius: 12px;">
        </div>
        <p>请使用Safari浏览器打开此页面:</p>
        <ol style="text-align: left; padding-left: 20px;">
          <li>复制当前页面地址</li>
          <li>打开Safari浏览器并粘贴地址</li>
          <li>然后按照安装指南操作</li>
        </ol>
      `;
    }
  } else {
    if (isChrome) {
      guideContent = `
        <h4>在Android上安装${appName}</h4>
        <div style="margin: 15px 0;">
          <img src="/static/icons/${appType}.png" style="width: 60px; height: 60px; border-radius: 12px;">
        </div>
        <ol style="text-align: left; padding-left: 20px;">
          <li>点击右上角的<strong>菜单按钮</strong> ⋮</li>
          <li>选择<strong>"安装应用"</strong>或<strong>"添加到主屏幕"</strong></li>
          <li>点击<strong>"安装"</strong>确认</li>
        </ol>
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 15px;">
          <strong>提示:</strong> 安装后可从主屏幕直接启动，享受全屏体验
        </div>
      `;
    } else {
      guideContent = `
        <h4>安装${appName}</h4>
        <div style="margin: 15px 0;">
          <img src="/static/icons/${appType}.png" style="width: 60px; height: 60px; border-radius: 12px;">
        </div>
        <ol style="text-align: left; padding-left: 20px;">
          <li>点击浏览器菜单</li>
          <li>查找并选择<strong>"添加到主屏幕"</strong>选项</li>
          <li>按照提示完成安装</li>
        </ol>
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 15px;">
          <strong>提示:</strong> 不同浏览器的安装选项可能位置不同
        </div>
      `;
    }
  }
  
  modalDiv.innerHTML = `
    <div style="background-color: white; padding: 20px; border-radius: 8px; max-width: 90%; width: 350px; text-align: center;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
        <h3 style="margin: 0;">安装指南</h3>
        <button id="close-install-guide" style="background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
      </div>
      ${guideContent}
    </div>
  `;
  
  document.body.appendChild(modalDiv);
  
  // 关闭按钮事件
  document.getElementById('close-install-guide').addEventListener('click', () => {
    document.body.removeChild(modalDiv);
  });
  
  // 点击背景也可以关闭
  modalDiv.addEventListener('click', (e) => {
    if (e.target === modalDiv) {
      document.body.removeChild(modalDiv);
    }
  });
}

// 监测应用安装状态
window.addEventListener('appinstalled', (evt) => {
  console.log(`${appType} 已被安装`);
  localStorage.setItem(`${appType}_pwa_installed`, 'true');
  
  // 移除安装提示（如果存在）
  const prompt = document.getElementById('pwa-install-prompt');
  if (prompt) {
    document.body.removeChild(prompt);
  }
});
