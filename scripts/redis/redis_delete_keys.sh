#!/bin/bash
# 安全删除Redis key脚本
# 使用方式：./redis_delete_keys.sh "your_pattern*" 

CONTAINER_NAME="servo_ai-redis-1"
REDIS_PASSWORD="difyai123456"

if [ -z "$1" ]; then
    echo "请指定key匹配模式（如：'user:*'）"
    exit 1
fi

echo "正在扫描匹配模式: $1"
KEYS=$(docker exec -i $CONTAINER_NAME redis-cli -a $REDIS_PASSWORD --no-auth-warning SCAN 0 MATCH "$1" COUNT 1000 | awk '{if(NR>1)print}')

# 过滤Celery系统key
FILTERED_KEYS=$(echo "$KEYS" | grep -v -E '^(_kombu|celery|unacked|unacked_mutex|tasks|_results)')

if [ -z "$FILTERED_KEYS" ]; then
    echo "没有找到匹配的key"
    exit 0
fi

echo "即将删除以下key:"
echo "$FILTERED_KEYS"
read -p "确认删除？(y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "$FILTERED_KEYS" | xargs -I {} docker exec -i $CONTAINER_NAME redis-cli -a $REDIS_PASSWORD --no-auth-warning DEL {}
    echo "已删除 ${#FILTERED_KEYS[@]} 个key"
else
    echo "操作取消"
fi