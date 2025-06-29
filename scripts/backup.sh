#!/bin/bash

# 数据备份脚本
BACKUP_DIR="/backup/telegram-bot"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="telegram_bot_backup_${DATE}.tar.gz"

echo "🔄 开始备份数据..."

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份用户数据和日志
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    data/ \
    .env \
    --exclude='data/logs/*.log'

echo "✅ 备份完成: ${BACKUP_DIR}/${BACKUP_FILE}"

# 清理7天前的备份
find $BACKUP_DIR -name "telegram_bot_backup_*.tar.gz" -mtime +7 -delete

echo "🧹 清理完成"