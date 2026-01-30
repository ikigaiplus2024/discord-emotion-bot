import discord
import asyncio
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime
import pytz
import os
import sys
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

# Google Sheets認証設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1-y3HMW_ET23363riQbn-DHx1Thd82Lt-Xf-C48ARaFs'

# チャンネルID
MORNING_CHANNEL_ID = 1167330758927597608  # 朝、夕方の会の部屋
NOON_CHANNEL_ID = 1334677890893090817      # 今日の出来事共有＆休憩部屋

# スタンプ・感情対応表
EMOTION_MAP = {
    '😄': '最高',
    '😊': '楽しい',
    '😌': '良い感じ',
    '💪': '頑張ってる',
    '😐': '普通',
    '😴': '眠い',
    '😤': 'イライラ',
    '😔': 'モヤモヤ',
    '😟': '不安',
    '😞': 'つらい'
}

class EmotionBot:
    def __init__(self, token):
        self.token = token
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        intents.members = True
        self.client = discord.Client(intents=intents)
        
    async def post_message(self, channel_id, message_text):
        """指定されたチャンネルにメッセージを投稿"""
        await self.client.wait_until_ready()
        channel = self.client.get_channel(channel_id)
        
        if channel:
            message = await channel.send(message_text)
            
            # スタンプを自動で付与
            for emoji in EMOTION_MAP.keys():
                await message.add_reaction(emoji)
            
            logger.info(f"投稿完了: Channel {channel_id}, Message ID {message.id}")
            return True
        else:
            logger.error(f"チャンネルが見つかりません: {channel_id}")
            return False
    
    async def run_morning_post(self):
        """朝9:00の投稿を実行"""
        message_text = (
            "🌅 **今日はどんな気分でスタート？**\n\n"
            "下のスタンプで今の気分を教えてね！\n"
            "━━━━━━━━━━━━━━━━━━"
        )
        await self.client.start(self.token)
        await self.post_message(MORNING_CHANNEL_ID, message_text)
        await self.client.close()
    
    async def run_noon_post(self):
        """昼12:00の投稿を実行"""
        message_text = (
            "☀️ **ここまでの学校の時間、どうだった？**\n\n"
            "下のスタンプで今の気分を教えてね！\n"
            "━━━━━━━━━━━━━━━━━━"
        )
        await self.client.start(self.token)
        await self.post_message(NOON_CHANNEL_ID, message_text)
        await self.client.close()

if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    if not TOKEN:
        logger.error("DISCORD_BOT_TOKENが設定されていません")
        sys.exit(1)
    
    bot = EmotionBot(TOKEN)
    
    # コマンドライン引数で朝/昼を判定
    if len(sys.argv) > 1:
        if sys.argv[1] == "morning":
            logger.info("朝の投稿を実行します")
            asyncio.run(bot.run_morning_post())
        elif sys.argv[1] == "noon":
            logger.info("昼の投稿を実行します")
            asyncio.run(bot.run_noon_post())
        else:
            logger.error("引数は 'morning' または 'noon' を指定してください")
            sys.exit(1)
    else:
        logger.error("引数が必要です: 'morning' または 'noon'")
        sys.exit(1)
