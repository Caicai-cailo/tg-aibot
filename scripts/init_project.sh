#!/bin/bash

# 项目初始化脚本
echo "🚀 初始化 Telegram AI Bot 项目..."

# 创建必要目录
mkdir -p data/logs
mkdir -p monitoring/grafana/dashboards

# 设置权限
chmod +x scripts/*.sh

# 创建.env文件（如果不存在）
if [ ! -f .env ]; then
    echo "📝 创建环境配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件并填入您的API密钥！"
fi

# 创建初始用户数据文件
if [ ! -f data/users.json ]; then
    echo "{}" > data/users.json
fi

# 创建日志文件
touch data/logs/bot.log

echo "✅ 项目初始化完成！"
echo "📋 下一步："
echo "1. 编辑 .env 文件"
echo "2. 运行: docker-compose up -d"