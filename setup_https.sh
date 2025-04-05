#!/bin/bash

# 安装Certbot
apt-get update
apt-get install -y certbot python3-certbot-nginx

# 获取证书，使用您的邮箱
certbot --nginx -d 8.133.194.133 --non-interactive --agree-tos --email ma2214889041@gmail.com

# 复制NGINX配置
cp /home/mlsp/nginx_https.conf /etc/nginx/sites-available/milan-food

# 启用站点
ln -sf /etc/nginx/sites-available/milan-food /etc/nginx/sites-enabled/

# 测试NGINX配置
nginx -t

# 重启NGINX
systemctl restart nginx

echo "HTTPS设置完成！现在你可以通过https://8.133.194.133访问应用。"
