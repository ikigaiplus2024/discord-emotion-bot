import discord
import asyncio
import os
import sys
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

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

async def post_message(channel_id, message_text, token):
    """指定されたチャンネルにメッセージを投稿"""
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        logger.info(f'{client.user} がログインしました')
        try:
            channel = client.get_channel(channel_id)
            
            if channel:
                message = await channel.send(message_text)
                
                # スタンプを自動で付与
                for emoji in EMOTION_MAP.keys():
                    await message.add_reaction(emoji)
                
                logger.info(f"投稿完了: Channel {channel_id}, Message ID {message.id}")
            else:
                logger.error(f"チャンネルが見つかりません: {channel_id}")
        except Exception as e:
            logger.error(f"投稿エラー: {e}")
        finally:
            await client.close()
    
    try:
        await client.start(token)
    except Exception as e:
        logger.error(f"接続エラー: {e}")

async def post_morning(token):
    """朝9:00の投稿を実行"""
    message_text = (
        "🌅 **今日はどんな気分でスタート？**\n\n"
        "下のスタンプで今の気分を教えてね！\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    logger.info("朝の投稿を実行します")
    await post_message(MORNING_CHANNEL_ID, message_text, token)

async def post_noon(token):
    """昼12:00の投稿を実行"""
    message_text = (
        "☀️ **ここまでの学校の時間、どうだった？**\n\n"
        "下のスタンプで今の気分を教えてね！\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    logger.info("昼の投稿を実行します")
    await post_message(NOON_CHANNEL_ID, message_text, token)

if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    if not TOKEN:
        logger.error("DISCORD_BOT_TOKENが設定されていません")
        sys.exit(1)
    
    # コマンドライン引数で朝/昼を判定
    if len(sys.argv) > 1:
        if sys.argv[1] == "morning":
            asyncio.run(post_morning(TOKEN))
        elif sys.argv[1] == "noon":
            asyncio.run(post_noon(TOKEN))
        else:
            logger.error("引数は 'morning' または 'noon' を指定してください")
            sys.exit(1)
    else:
        logger.error("引数が必要です: 'morning' または 'noon'")
        sys.exit(1)
