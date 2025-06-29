"""
实时统计服务
"""

import json
import aioredis
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class RealTimeStatsManager:
    """实时统计管理器"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.fallback_stats = defaultdict(int)  # Redis不可用时的备用统计
        self.redis_available = False

        # 内存中的实时数据
        self.active_users = set()  # 当前活跃用户
        self.user_last_activity = {}  # 用户最后活动时间

    async def initialize(self):
        """初始化Redis连接"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )

            # 测试连接
            await self.redis.ping()
            self.redis_available = True
            logger.info("✅ Redis连接成功，启用实时统计")

        except Exception as e:
            logger.warning(f"❌ Redis连接失败，使用内存统计: {e}")
            self.redis_available = False

    async def update_user_activity(self, user_id: int, action: str, chat_type: str = "private"):
        """更新用户活动统计"""
        try:
            current_time = datetime.now()
            today = current_time.strftime('%Y-%m-%d')
            hour = current_time.strftime('%Y-%m-%d-%H')
            minute = current_time.strftime('%Y-%m-%d-%H-%M')

            # 更新活跃用户列表
            self.active_users.add(user_id)
            self.user_last_activity[user_id] = current_time

            if self.redis_available and self.redis:
                # Redis统计
                pipe = self.redis.pipeline()

                # 日统计
                pipe.hincrby("daily_users", today, 1)
                pipe.hincrby("daily_messages", today, 1)
                pipe.sadd(f"active_users:{today}", user_id)

                # 小时统计
                pipe.hincrby("hourly_messages", hour, 1)
                pipe.sadd(f"active_users:{hour}", user_id)

                # 分钟统计（用于实时监控）
                pipe.hincrby("minute_messages", minute, 1)

                # 用户个人统计
                pipe.hincrby(f"user_stats:{user_id}", "total_messages", 1)
                pipe.hincrby(f"user_stats:{user_id}", f"messages_{today}", 1)
                pipe.hset(f"user_stats:{user_id}", "last_activity", current_time.isoformat())

                # 动作类型统计
                pipe.hincrby("action_types", action, 1)
                pipe.hincrby(f"action_types:{today}", action, 1)

                # 聊天类型统计
                pipe.hincrby("chat_types", chat_type, 1)

                # 设置过期时间
                pipe.expire(f"active_users:{today}", 86400 * 7)  # 7天
                pipe.expire(f"active_users:{hour}", 3600 * 25)  # 25小时
                pipe.expire(f"user_stats:{user_id}", 86400 * 30)  # 30天
                pipe.expire("minute_messages", 3600)  # 1小时

                await pipe.execute()

            else:
                # 备用内存统计
                self.fallback_stats[f"daily_users_{today}"] += 1
                self.fallback_stats[f"hourly_messages_{hour}"] += 1
                self.fallback_stats[f"action_{action}"] += 1

        except Exception as e:
            logger.error(f"更新用户活动统计失败: {e}")

    async def get_real_time_stats(self) -> Dict:
        """获取实时统计数据"""
        try:
            current_time = datetime.now()
            today = current_time.strftime('%Y-%m-%d')
            hour = current_time.strftime('%Y-%m-%d-%H')

            if self.redis_available and self.redis:
                # 从Redis获取统计
                pipe = self.redis.pipeline()

                # 今日统计
                pipe.hget("daily_messages", today)
                pipe.scard(f"active_users:{today}")

                # 当前小时统计
                pipe.hget("hourly_messages", hour)
                pipe.scard(f"active_users:{hour}")

                # 动作类型统计
                pipe.hgetall("action_types")
                pipe.hgetall(f"action_types:{today}")

                # 聊天类型统计
                pipe.hgetall("chat_types")

                results = await pipe.execute()

                # 在线用户数（最近5分钟活跃）
                online_users = await self._get_online_users_count()

                return {
                    'today_messages': int(results[0] or 0),
                    'today_active_users': int(results[1] or 0),
                    'current_hour_messages': int(results[2] or 0),
                    'current_hour_users': int(results[3] or 0),
                    'online_users': online_users,
                    'total_action_types': results[4] or {},
                    'today_action_types': results[5] or {},
                    'chat_types': results[6] or {},
                    'last_updated': current_time.strftime('%H:%M:%S'),
                    'data_source': 'redis'
                }

            else:
                # 使用备用统计
                online_users = len([
                    uid for uid, last_time in self.user_last_activity.items()
                    if (current_time - last_time).seconds < 300  # 5分钟内活跃
                ])

                return {
                    'today_messages': self.fallback_stats.get(f"daily_users_{today}", 0),
                    'today_active_users': len(self.active_users),
                    'current_hour_messages': self.fallback_stats.get(f"hourly_messages_{hour}", 0),
                    'current_hour_users': len(self.active_users),
                    'online_users': online_users,
                    'total_action_types': {
                        k.replace('action_', ''): v
                        for k, v in self.fallback_stats.items()
                        if k.startswith('action_')
                    },
                    'today_action_types': {},
                    'chat_types': {},
                    'last_updated': current_time.strftime('%H:%M:%S'),
                    'data_source': 'memory'
                }

        except Exception as e:
            logger.error(f"获取实时统计失败: {e}")
            return {
                'error': str(e),
                'last_updated': datetime.now().strftime('%H:%M:%S'),
                'data_source': 'error'
            }

    async def _get_online_users_count(self) -> int:
        """获取在线用户数（最近5分钟活跃）"""
        try:
            current_time = datetime.now()

            if self.redis_available and self.redis:
                # 检查最近5分钟的活跃用户
                online_count = 0
                for i in range(5):
                    minute_time = current_time - timedelta(minutes=i)
                    minute_key = minute_time.strftime('%Y-%m-%d-%H-%M')
                    count = await self.redis.hget("minute_messages", minute_key)
                    if count:
                        online_count = max(online_count, int(count))

                return online_count
            else:
                # 使用内存统计
                five_minutes_ago = current_time - timedelta(minutes=5)
                return len([
                    uid for uid, last_time in self.user_last_activity.items()
                    if last_time >= five_minutes_ago
                ])

        except Exception as e:
            logger.error(f"获取在线用户数失败: {e}")
            return 0

    async def get_user_statistics(self, limit: int = 10) -> Dict:
        """获取用户统计数据"""
        try:
            if self.redis_available and self.redis:
                # 获取最活跃用户
                action_types = await self.redis.hgetall("action_types")

                # 这里可以添加更多用户统计逻辑
                return {
                    'total_registered_users': len(self.active_users),
                    'action_distribution': action_types,
                    'data_source': 'redis'
                }
            else:
                return {
                    'total_registered_users': len(self.active_users),
                    'action_distribution': {},
                    'data_source': 'memory'
                }

        except Exception as e:
            logger.error(f"获取用户统计失败: {e}")
            return {'error': str(e)}

    async def get_performance_metrics(self) -> Dict:
        """获取性能指标"""
        try:
            if self.redis_available and self.redis:
                # Redis性能统计
                info = await self.redis.info()

                return {
                    'redis_connected_clients': info.get('connected_clients', 0),
                    'redis_used_memory_human': info.get('used_memory_human', '0B'),
                    'redis_total_commands_processed': info.get('total_commands_processed', 0),
                    'redis_uptime_in_seconds': info.get('uptime_in_seconds', 0),
                    'cache_hit_rate': 'N/A',  # 可以实现缓存命中率统计
                    'data_source': 'redis'
                }
            else:
                return {
                    'redis_status': 'disconnected',
                    'data_source': 'memory'
                }

        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {'error': str(e)}

    async def cleanup_old_data(self):
        """清理过期数据"""
        if not self.redis_available or not self.redis:
            return

        try:
            # 清理超过7天的数据
            cutoff_date = datetime.now() - timedelta(days=7)

            # 清理按日期存储的键
            for i in range(8, 15):  # 8-14天前的数据
                old_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                await self.redis.delete(f"active_users:{old_date}")
                await self.redis.hdel("daily_users", old_date)
                await self.redis.hdel("daily_messages", old_date)

            logger.info("✅ 清理过期统计数据完成")

        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")