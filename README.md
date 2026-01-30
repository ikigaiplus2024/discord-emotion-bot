# Discord 感情記録Bot セットアップガイド

このBotは、毎日決まった時間にDiscordチャンネルに投稿し、子どもたちの感情をスタンプで記録してGoogle Sheetsに自動保存します。

## 機能

- **朝9:00**: 「朝、夕方の会の部屋」に感情チェック投稿
- **昼12:00**: 「今日の出来事共有＆休憩部屋」に感情チェック投稿
- **自動記録**: 子どもたちがスタンプで反応すると、自動的にGoogle Sheetsに記録

## セットアップ手順

### ステップ 1: Discord Bot の作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリックして新しいアプリケーションを作成
3. 左メニューから「Bot」を選択
4. 「Add Bot」をクリック
5. 「Token」セクションで「Reset Token」→「Copy」でトークンをコピー（後で使用）

#### Bot権限の設定

「Bot」ページの下部「Privileged Gateway Intents」で以下を有効化：
- ✅ MESSAGE CONTENT INTENT
- ✅ SERVER MEMBERS INTENT

「OAuth2」→「URL Generator」で以下の権限を選択：
- ✅ bot
- ✅ applications.commands

Bot Permissions:
- ✅ Read Messages/View Channels
- ✅ Send Messages
- ✅ Add Reactions
- ✅ Read Message History

生成されたURLをコピーして、ブラウザで開き、Botをサーバーに招待します。

### ステップ 2: Google Cloud の設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
3. 「APIとサービス」→「ライブラリ」から「Google Sheets API」を検索して有効化
4. 「APIとサービス」→「認証情報」→「認証情報を作成」→「サービスアカウント」
5. サービスアカウント名を入力（例：emotion-bot）→「作成」
6. ロールは特に設定不要 →「完了」
7. 作成したサービスアカウントをクリック
8. 「キー」タブ →「鍵を追加」→「新しい鍵を作成」→「JSON」→「作成」
9. ダウンロードされたJSONファイルを `service_account.json` という名前に変更

### ステップ 3: Google Sheets の権限設定

1. スプレッドシート（https://docs.google.com/spreadsheets/d/1-y3HMW_ET23363riQbn-DHx1Thd82Lt-Xf-C48ARaFs/edit）を開く
2. 右上の「共有」をクリック
3. `service_account.json` 内の `client_email` の値（例：emotion-bot@project-id.iam.gserviceaccount.com）をコピー
4. このメールアドレスに「編集者」権限で共有
5. 「通知しない」にチェック →「共有」

### ステップ 4: スプレッドシートの準備

スプレッドシートに以下の2つのシートを作成：

#### シート1: 「感情記録」
1行目（ヘッダー）:
```
日付 | 時間帯 | Discord ユーザーネーム | 選んだスタンプ | 感情ラベル | 記録時刻
```

#### シート2: 「マスターデータ」
1行目（ヘッダー）:
```
スタンプ絵文字 | 感情ラベル | 分類
```

2行目以降:
```
😄 | 最高 | ポジティブ
😊 | 楽しい | ポジティブ
😌 | 良い感じ | ポジティブ
💪 | 頑張ってる | ポジティブ
😐 | 普通 | ニュートラル
😴 | 眠い | ニュートラル
😤 | イライラ | ネガティブ
😔 | モヤモヤ | ネガティブ
😟 | 不安 | ネガティブ
😞 | つらい | ネガティブ
```

### ステップ 5: Render.com でのデプロイ（無料）

1. [Render.com](https://render.com/) にアクセスしてアカウント作成（GitHubアカウントで簡単登録）
2. 「New」→「Web Service」を選択
3. GitHubリポジトリを接続（または「Public Git Repository」でコードをアップロード）

#### リポジトリの準備

GitHubに以下のファイルをアップロード：
- bot.py
- requirements.txt
- start.sh
- service_account.json

#### Render.com の設定

- **Name**: emotion-discord-bot（任意）
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `bash start.sh`
- **Plan**: Free

#### 環境変数の設定

Renderのダッシュボードで「Environment」タブ：
- Key: `DISCORD_BOT_TOKEN`
- Value: （Discord Botのトークンを貼り付け）

「Save Changes」→「Deploy」

### ステップ 6: 動作確認

デプロイ完了後：

1. Discordサーバーで管理者として以下のコマンドを実行（テスト用）：
   - `!test_morning` → 朝の投稿をテスト
   - `!test_noon` → 昼の投稿をテスト

2. 投稿されたメッセージにスタンプが自動で付与されることを確認

3. スタンプをクリックして、Google Sheetsに記録されることを確認

## トラブルシューティング

### Botがオンラインにならない
- Render.comのログを確認
- Discord Botトークンが正しいか確認
- Privileged Gateway Intentsが有効か確認

### スプレッドシートに記録されない
- service_account.jsonが正しくアップロードされているか確認
- スプレッドシートの共有設定を確認
- シート名が「感情記録」になっているか確認

### 投稿が来ない
- Render.comで「Free」プランは非アクティブ時にスリープします
- 「Cron Jobs」への移行を検討（無料プランでも定期実行可能）

## Render.com の注意点

- **無料プランの制限**: 15分間アクティビティがないとスリープ
- **解決策**: 「Background Worker」または「Cron Job」として設定すると、スケジュール実行のみに最適化できます

### Cron Job として設定する方法（推奨）

Render.comで「New」→「Cron Job」を選択：
- **Schedule**: 毎日9:00と12:00に実行
- 9:00用と12:00用で2つのCron Jobを作成

この場合、bot.pyを以下のように修正：
```python
# スケジューラーを削除して、即座に実行
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "morning":
            asyncio.run(schedule_morning_post())
        elif sys.argv[1] == "noon":
            asyncio.run(schedule_noon_post())
```

## サポート

問題が発生した場合は、以下を確認してください：
- Render.comのログ
- Discordのサーバー設定
- Google Sheetsの権限

## ライセンス

このプロジェクトは教育目的で作成されています。
