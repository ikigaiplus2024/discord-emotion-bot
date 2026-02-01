import discord
from discord.ext import commands
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime
import pytz
import os
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

# Discord Bot初期化
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Google Sheets認証設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1-y3HMW_ET23363riQbn-DHx1Thd82Lt-Xf-C48ARaFs'

# チャンネルID
MORNING_CHANNEL_ID = 1167330758927597608
NOON_CHANNEL_ID = 1334677890893090817

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

# Google Sheetsクライアント初期化
def get_sheets_client():
    """Google Sheetsクライアントを取得"""
    try:
        # 環境変数からGoogle認証情報を取得
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        
        if credentials_json:
            # 環境変数から読み込む場合（本番環境）
            import json
            credentials_dict = json.loads(credentials_json)
            creds = Credentials.from_service_account_info(
                credentials_dict,
                scopes=SCOPES
            )
        else:
            # ファイルから読み込む場合（ローカル開発用）
            creds = Credentials.from_service_account_file(
                'service_account.json', 
                scopes=SCOPES
            )
        
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        logger.error(f"Google Sheets認証エラー: {e}")
        return None

# スプレッドシートへの書き込み
async def write_to_sheets(date, time_slot, username, user_id, emoji, emotion):
    """感情データをスプレッドシートに記録"""
    try:
        client = get_sheets_client()
        if not client:
            logger.error("Sheetsクライアントの取得に失敗")
            return False
        
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet('感情記録')
        
        jst = pytz.timezone('Asia/Tokyo')
        timestamp = datetime.now(jst).strftime('%H:%M:%S')
        
        row = [date, time_slot, username, emoji, emotion, timestamp]
        worksheet.append_row(row)
        
        logger.info(f"記録成功: {username} - {emotion} at {timestamp}")
        return True
    except Exception as e:
        logger.error(f"Sheets書き込みエラー: {e}")
        return False

# リアクション追加イベント
@bot.event
async def on_raw_reaction_add(payload):
    """リアクションが追加されたときの処理"""
    if payload.user_id == bot.user.id:
        return
    
    emoji_str = str(payload.emoji)
    if emoji_str not in EMOTION_MAP:
        return
    
    # 対象チャンネルのメッセージか確認
    if payload.channel_id not in [MORNING_CHANNEL_ID, NOON_CHANNEL_ID]:
        return
    
    try:
        # チャンネルとメッセージを取得
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        
        # Botが投稿したメッセージか確認
        if message.author.id != bot.user.id:
            return
        
        # メッセージの内容から時間帯を判定
        time_slot = None
        if "今日はどんな気分でスタート" in message.content:
            time_slot = '朝9:00'
        elif "今日のフォレストリンクはどうだった" in message.content:
            time_slot = '昼12:00'
        else:
            return
        
        user = await bot.fetch_user(payload.user_id)
        username = user.name
        
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst)
        date = now.strftime('%Y-%m-%d')
        
        emotion = EMOTION_MAP[emoji_str]
        
        await write_to_sheets(date, time_slot, username, user.id, emoji_str, emotion)
        
    except Exception as e:
        logger.error(f"リアクション処理エラー: {e}")

@bot.event
async def on_ready():
    """Botが起動したときの処理"""
    logger.info(f'{bot.user} がログインしました（リアクション記録モード）')
    logger.info(f'Bot ID: {bot.user.id}')
    logger.info("リアクションの記録を開始します")

if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        logger.error("DISCORD_BOT_TOKENが設定されていません")
    else:
        bot.run(TOKEN)
