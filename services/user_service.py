"""
用户管理服务
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from telegram import User

logger = logging.getLogger(__name__)


class UserService:
    """用户管理服务类"""

    def __init__(self, data_file: str = "data/users.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.users_data = self.load_users_data()
        self.conversation_history = {}

    def load_users_data(self) -> Dict:
        """加载用户数据"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载用户数据失败: {e}")
                return {}
        return {}

    async def save_users_data(self):
        """保存用户数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.users_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存用户数据失败: {e}")

    async def register_user(self, user: User):
        """注册用户"""
        user_id = str(user.id)
        current_time = datetime.now().isoformat()

        if user_id not in self.users_data:
            self.users_data[user_id] = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'join_date': current_time,
                'total_messages': 0,
                'today_messages': 0,
                'week_messages': 0,
                'last_activity': current_time,
                'settings': {
                    'language': 'zh',
                    'notifications': True,
                    'mode': 'chat'
                },
                'statistics': {
                    'daily_usage': {},
                    'weekly_usage': {},
                    'favorite_features': []
                }
            }
            await self.save_users_data()
            logger.info(f"新用户注册: {user.first_name} ({user.id})")
        else:
            # 更新用户信息
            self.users_data[user_id].update({
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'last_activity': current_time
            })
            await self.save_users_data()

    async def get_user_data(self, user_id: int) -> Dict:
        """获取用户数据"""
        return self.users_data.get(str(user_id), {})

    async def update_user_activity(self, user_id: int):
        """更新用户活动"""
        user_id_str = str(user_id)
        current_time = datetime.now()
        today = current_time.date().isoformat()

        if user_id_str in self.users_data:
            user_data = self.users_data[user_id_str]

            # 更新总消息数
            user_data['total_messages'] = user_data.get('total_messages', 0) + 1

            # 更新今日消息数
            last_activity = datetime.fromisoformat(user_data.get('last_activity', current_time.isoformat()))
            if last_activity.date() != current_time.date():
                user_data['today_messages'] = 1
            else:
                user_data['today_messages'] = user_data.get('today_messages', 0) + 1

            # 更新本周消息数
            week_start = current_time - timedelta(days=current_time.weekday())
            if last_activity < week_start:
                user_data['week_messages'] = 1
            else:
                user_data['week_messages'] = user_data.get('week_messages', 0) + 1

            # 更新最后活动时间
            user_data['last_activity'] = current_time.isoformat()

            # 更新每日使用统计
            if 'statistics' not in user_data:
                user_data['statistics'] = {'daily_usage': {}}

            daily_usage = user_data['statistics']['daily_usage']
            daily_usage[today] = daily_usage.get(today, 0) + 1

            await self.save_users_data()

    async def get_user_stats(self, user_id: int) -> Dict:
        """获取用户统计信息"""
        user_data = await self.get_user_data(user_id)

        if not user_data:
            return {}

        total_messages = user_data.get('total_messages', 0)
        level = self.calculate_user_level(total_messages)
        badges = self.calculate_user_badges(user_data)

        return {
            'total_messages': total_messages,
            'today_messages': user_data.get('today_messages', 0),
            'week_messages': user_data.get('week_messages', 0),
            'join_date': user_data.get('join_date', 'Unknown'),
            'last_activity': user_data.get('last_activity', 'Unknown'),
            'level': level,
            'badges': badges
        }

    def calculate_user_level(self, total_messages: int) -> str:
        """计算用户等级"""
        if total_messages >= 5000:
            return "🏆 传奇大师"
        elif total_messages >= 2000:
            return "💎 钻石专家"
        elif total_messages >= 1000:
            return "🥇 黄金高手"
        elif total_messages >= 500:
            return "🥈 白银达人"
        elif total_messages >= 100:
            return "🥉 青铜新手"
        else:
            return "🌱 初来乍到"

    def calculate_user_badges(self, user_data: Dict) -> str:
        """计算用户徽章"""
        badges = []

        total_messages = user_data.get('total_messages', 0)
        join_date = datetime.fromisoformat(user_data.get('join_date', datetime.now().isoformat()))
        days_since_join = (datetime.now() - join_date).days

        # 活跃度徽章
        if total_messages >= 1000:
            badges.append("🔥 超级活跃")
        elif total_messages >= 500:
            badges.append("⚡ 非常活跃")
        elif total_messages >= 100:
            badges.append("📈 比较活跃")

        # 忠诚度徽章
        if days_since_join >= 365:
            badges.append("🎂 一年老友")
        elif days_since_join >= 180:
            badges.append("🌟 半年伙伴")
        elif days_since_join >= 30:
            badges.append("🤝 月度用户")

        # 连续使用徽章
        today_messages = user_data.get('today_messages', 0)
        if today_messages >= 50:
            badges.append("💪 今日达人")
        elif today_messages >= 20:
            badges.append("👍 今日活跃")

        return " ".join(badges) if badges else "暂无徽章"

    async def get_conversation_context(self, user_id: int) -> List[str]:
        """获取用户对话上下文"""
        return self.conversation_history.get(str(user_id), [])

    async def add_to_conversation_history(self, user_id: int, user_msg: str, bot_msg: str):
        """添加到对话历史"""
        user_id_str = str(user_id)

        if user_id_str not in self.conversation_history:
            self.conversation_history[user_id_str] = []

        history = self.conversation_history[user_id_str]
        history.append(user_msg)
        history.append(bot_msg)

        # 保持历史记录在合理长度内
        if len(history) > 20:
            history = history[-20:]
            self.conversation_history[user_id_str] = history

    async def clear_conversation_history(self, user_id: int):
        """清除对话历史"""
        user_id_str = str(user_id)
        if user_id_str in self.conversation_history:
            del self.conversation_history[user_id_str]

    async def update_user_setting(self, user_id: int, setting: str, value):
        """更新用户设置"""
        user_id_str = str(user_id)

        if user_id_str in self.users_data:
            if 'settings' not in self.users_data[user_id_str]:
                self.users_data[user_id_str]['settings'] = {}

            self.users_data[user_id_str]['settings'][setting] = value
            await self.save_users_data()

    async def get_all_users_count(self) -> int:
        """获取总用户数"""
        return len(self.users_data)

    async def get_active_users_today(self) -> int:
        """获取今日活跃用户数"""
        today = datetime.now().date().isoformat()
        count = 0

        for user_data in self.users_data.values():
            last_activity = user_data.get('last_activity', '')
            if last_activity.startswith(today):
                count += 1

        return count