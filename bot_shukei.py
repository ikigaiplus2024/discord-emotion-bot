"""その日の感情スタンプを集計して「感情記録」シートへ送る（Render Cron Job・毎日18時）

bot_cron.py が朝・昼に投稿したメッセージを探し、押されたスタンプを数えて
GAS（ウェブアプリ）へ送る。シートへの書き込みと二重書き込みの防止はGAS側で行う。
2026-11-13 追加（止まっていた bot_listener.py の代わり）。

環境変数:
  DISCORD_BOT_TOKEN  bot_cron.py と同じトークン
  GAS_URL            GASウェブアプリのURL（…/exec）
  GAS_KEY            GASの UKETORI_KEY と同じ値
"""
import datetime
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('shukei')

# 時間帯の表示名とチャンネルID（bot_cron.py と同じ）
CHANNELS = [
    ('朝9:00', 1167330758927597608),   # 朝の会の部屋
    ('昼12:00', 1334677890893090817),  # 今日の出来事共有＆休憩部屋
]

# スタンプ・感情対応表（bot_cron.py と同じ）
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

JST = datetime.timezone(datetime.timedelta(hours=9))
TOKEN = os.getenv('DISCORD_BOT_TOKEN')


def discord_get(path):
    """Discord APIをGETで呼ぶ（混雑時は待ってやり直す）"""
    req = urllib.request.Request(
        'https://discord.com/api/v10' + path,
        headers={
            'Authorization': 'Bot ' + TOKEN,
            'User-Agent': 'DiscordBot (https://github.com/ikigaiplus2024/discord-emotion-bot, 2.0)',
        },
    )
    for _ in range(5):
        try:
            with urllib.request.urlopen(req) as res:
                return json.loads(res.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = json.loads(e.read().decode('utf-8')).get('retry_after', 2)
                time.sleep(wait + 0.2)
                continue
            raise
    raise RuntimeError('Discord APIが混雑していて失敗しました')


def find_today_message(channel_id, bot_id, today):
    """そのチャンネルでBotが今日投稿したメッセージを探す
    にぎやかなチャンネルでは投稿後に100件以上書き込まれるので、昨日の分に届くまでさかのぼる"""
    before = ''
    for _ in range(10):  # 最大1000件まで
        msgs = discord_get(f'/channels/{channel_id}/messages?limit=100{before}')
        if not msgs:
            return None
        for m in msgs:
            posted = datetime.datetime.fromisoformat(m['timestamp']).astimezone(JST).date()
            if posted < today:
                return None
            if m['author']['id'] == bot_id:
                return m
        before = f'&before={msgs[-1]["id"]}'
    return None


def main():
    gas_url = os.getenv('GAS_URL')
    gas_key = os.getenv('GAS_KEY')
    if not (TOKEN and gas_url and gas_key):
        logger.error('DISCORD_BOT_TOKEN / GAS_URL / GAS_KEY が設定されていません')
        sys.exit(1)

    now = datetime.datetime.now(JST)
    today = now.date()
    bot_id = discord_get('/users/@me')['id']

    rows = []
    for label, channel_id in CHANNELS:
        msg = find_today_message(channel_id, bot_id, today)
        if not msg:
            logger.info(f'今日の投稿が見つかりません: {label}')
            continue
        for emoji, emotion in EMOTION_MAP.items():
            users = discord_get(
                f'/channels/{channel_id}/messages/{msg["id"]}/reactions/'
                f'{urllib.parse.quote(emoji)}?limit=100'
            )
            for u in users:
                if not u.get('bot'):
                    rows.append([today.isoformat(), label, u['username'], emoji, emotion,
                                 now.strftime('%H:%M:%S')])
            time.sleep(0.3)

    logger.info(f'押されていたスタンプ: {len(rows)}件')
    if not rows:
        return

    body = json.dumps({'key': gas_key, 'rows': rows}).encode('utf-8')
    req = urllib.request.Request(gas_url, data=body,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as res:
        result = json.loads(res.read().decode('utf-8'))
    if not result.get('ok'):
        logger.error(f'シートへの書き込みに失敗しました: {result}')
        sys.exit(1)
    logger.info(f'シートに新しく{result["added"]}件書き込みました')


if __name__ == '__main__':
    main()
