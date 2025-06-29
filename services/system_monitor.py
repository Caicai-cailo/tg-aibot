"""
系统监控服务
"""

import psutil
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SystemMonitor:
    """系统资源监控器"""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.response_times: List[float] = []
        self.api_call_count = 0
        self.last_error_time: Optional[datetime] = None
        self.last_error_message = ""

        # 性能历史记录（最近24小时）
        self.hourly_stats = {}

        logger.info("🔍 系统监控器已启动")

    def get_real_system_status(self) -> Dict:
        """获取真实的系统状态"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024 ** 3)
            memory_total_gb = memory.total / (1024 ** 3)

            # 磁盘使用率
            try:
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                disk_free_gb = disk.free / (1024 ** 3)
            except:
                disk_percent = 0
                disk_free_gb = 0

            # 网络IO统计
            try:
                net_io = psutil.net_io_counters()
                bytes_sent_mb = net_io.bytes_sent / (1024 ** 2)
                bytes_recv_mb = net_io.bytes_recv / (1024 ** 2)
            except:
                bytes_sent_mb = 0
                bytes_recv_mb = 0

            # 运行时间
            uptime_seconds = time.time() - self.start_time
            uptime_str = str(timedelta(seconds=int(uptime_seconds)))

            # 平均响应时间（最近100次请求）
            recent_responses = self.response_times[-100:] if self.response_times else []
            avg_response = sum(recent_responses) / len(recent_responses) if recent_responses else 0

            # 确定系统状态
            if cpu_percent > 90 or memory_percent > 90:
                status = "🔴 严重"
                status_emoji = "🔴"
            elif cpu_percent > 70 or memory_percent > 70:
                status = "🟡 警告"
                status_emoji = "🟡"
            else:
                status = "🟢 正常"
                status_emoji = "🟢"

            # 错误率计算
            error_rate = (self.error_count / max(self.request_count, 1)) * 100

            return {
                'status': status,
                'status_emoji': status_emoji,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_used_gb': memory_used_gb,
                'memory_total_gb': memory_total_gb,
                'disk_percent': disk_percent,
                'disk_free_gb': disk_free_gb,
                'network_sent_mb': bytes_sent_mb,
                'network_recv_mb': bytes_recv_mb,
                'uptime': uptime_str,
                'uptime_seconds': uptime_seconds,
                'total_requests': self.request_count,
                'api_calls': self.api_call_count,
                'error_count': self.error_count,
                'error_rate': error_rate,
                'avg_response_time': avg_response,
                'last_error_time': self.last_error_time.strftime('%H:%M:%S') if self.last_error_time else '无',
                'last_error_message': self.last_error_message or '无',
                'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {
                'status': '🔴 监控错误',
                'error': str(e),
                'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def record_request(self, response_time: float, is_error: bool = False, error_msg: str = ""):
        """记录请求统计"""
        self.request_count += 1
        self.response_times.append(response_time)

        if is_error:
            self.error_count += 1
            self.last_error_time = datetime.now()
            self.last_error_message = error_msg[:100]  # 限制错误消息长度

        # 只保留最近1000次请求的响应时间
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

        # 记录小时统计
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        if current_hour not in self.hourly_stats:
            self.hourly_stats[current_hour] = {
                'requests': 0,
                'errors': 0,
                'total_response_time': 0
            }

        self.hourly_stats[current_hour]['requests'] += 1
        self.hourly_stats[current_hour]['total_response_time'] += response_time

        if is_error:
            self.hourly_stats[current_hour]['errors'] += 1

        # 清理超过24小时的数据
        self._cleanup_old_stats()

    def record_api_call(self):
        """记录API调用"""
        self.api_call_count += 1

    def get_hourly_stats(self, hours: int = 24) -> Dict:
        """获取指定小时数的统计数据"""
        current_time = datetime.now()
        stats = {}

        for i in range(hours):
            hour_time = current_time - timedelta(hours=i)
            hour_key = hour_time.strftime('%Y-%m-%d-%H')

            if hour_key in self.hourly_stats:
                hour_data = self.hourly_stats[hour_key]
                avg_response = (hour_data['total_response_time'] /
                                max(hour_data['requests'], 1))

                stats[hour_key] = {
                    'requests': hour_data['requests'],
                    'errors': hour_data['errors'],
                    'avg_response': avg_response,
                    'error_rate': (hour_data['errors'] / max(hour_data['requests'], 1)) * 100
                }
            else:
                stats[hour_key] = {
                    'requests': 0,
                    'errors': 0,
                    'avg_response': 0,
                    'error_rate': 0
                }

        return stats

    def _cleanup_old_stats(self):
        """清理超过24小时的统计数据"""
        cutoff_time = datetime.now() - timedelta(hours=25)
        cutoff_key = cutoff_time.strftime('%Y-%m-%d-%H')

        keys_to_remove = [
            key for key in self.hourly_stats.keys()
            if key < cutoff_key
        ]

        for key in keys_to_remove:
            del self.hourly_stats[key]

    def get_performance_trend(self) -> Dict:
        """获取性能趋势分析"""
        if len(self.response_times) < 10:
            return {'trend': 'insufficient_data', 'message': '数据不足'}

        # 分析最近的响应时间趋势
        recent_50 = self.response_times[-50:]
        older_50 = self.response_times[-100:-50] if len(self.response_times) >= 100 else []

        if not older_50:
            return {'trend': 'insufficient_data', 'message': '历史数据不足'}

        recent_avg = sum(recent_50) / len(recent_50)
        older_avg = sum(older_50) / len(older_50)

        improvement = ((older_avg - recent_avg) / older_avg) * 100

        if improvement > 10:
            return {
                'trend': 'improving',
                'message': f'性能提升 {improvement:.1f}%',
                'emoji': '📈'
            }
        elif improvement < -10:
            return {
                'trend': 'degrading',
                'message': f'性能下降 {abs(improvement):.1f}%',
                'emoji': '📉'
            }
        else:
            return {
                'trend': 'stable',
                'message': '性能稳定',
                'emoji': '📊'
            }