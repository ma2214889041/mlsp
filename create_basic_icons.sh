#!/bin/bash

# 创建一个简单的HTML文件，用于生成纯色图标
cat > /home/mlsp/app/static/icons/generate_icon.html << 'HTML'
<!DOCTYPE html>
<html>
<head>
  <title>Icon Generator</title>
  <style>
    canvas { display: none; }
  </style>
</head>
<body>
  <canvas id="canvas192" width="192" height="192"></canvas>
  <canvas id="canvas512" width="512" height="512"></canvas>
  
  <script>
    // 生成192x192图标
    var canvas192 = document.getElementById('canvas192');
    var ctx192 = canvas192.getContext('2d');
    ctx192.fillStyle = '#dc3545';
    ctx192.fillRect(0, 0, 192, 192);
    ctx192.fillStyle = 'white';
    ctx192.font = 'bold 110px Arial';
    ctx192.textAlign = 'center';
    ctx192.textBaseline = 'middle';
    ctx192.fillText('M', 96, 96);
    
    // 生成512x512图标
    var canvas512 = document.getElementById('canvas512');
    var ctx512 = canvas512.getContext('2d');
    ctx512.fillStyle = '#dc3545';
    ctx512.fillRect(0, 0, 512, 512);
    ctx512.fillStyle = 'white';
    ctx512.font = 'bold 300px Arial';
    ctx512.textAlign = 'center';
    ctx512.textBaseline = 'middle';
    ctx512.fillText('M', 256, 256);
    
    // 下载图标
    function downloadIcon(canvas, filename) {
      var link = document.createElement('a');
      link.download = filename;
      link.href = canvas.toDataURL('image/png');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
    
    downloadIcon(canvas192, 'app-192.png');
    downloadIcon(canvas512, 'app-512.png');
  </script>
</body>
</html>
HTML

echo "请打开浏览器访问 http://8.133.194.133:8000/static/icons/generate_icon.html 下载生成的图标，然后将它们放到 /home/mlsp/app/static/icons/ 目录下"
