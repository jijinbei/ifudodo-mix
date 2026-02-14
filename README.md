# ifudodo-mix

威風堂々の音楽ミックスを生成する Discord bot。[ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5) を使い、ユーザーが指定したスタイルで威風堂々をリミックスした音声（日本語歌詞付き）を生成します。

## 必要環境

- [pixi](https://pixi.sh/) (パッケージマネージャ)
- CUDA 対応 GPU (VRAM 10GB 以上推奨)
- Discord Bot トークン
- [Ollama](https://ollama.com/) (スタイル調査用、省略可)

## セットアップ

### 1. 依存関係のインストール

```bash
pixi install
```

初回はモデルのダウンロード含め時間がかかります。

### 2. Discord Bot の作成

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリケーションを作成
2. **Bot** セクションでトークンを取得
3. **OAuth2 > URL Generator** で以下を選択:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Attach Files`
4. 生成された URL でサーバーに招待

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集して `DISCORD_TOKEN` を設定:

```
DISCORD_TOKEN=your_token_here
GUILD_ID=123456789              # 省略可: 開発時はサーバーIDを指定するとコマンド反映が即座
OLLAMA_HOST=http://localhost:11434  # 省略可: Ollamaサーバーのアドレス
OLLAMA_MODEL=gemma3                 # 省略可: スタイル調査に使うモデル
```

### 4. 起動

```bash
pixi run start
```

初回起動時に ACE-Step 1.5 リポジトリが `vendor/ace-step-15/` にクローンされます。

## 使い方

Discord で `/ifudodo` コマンドを使います:

```
/ifudodo lo-fi hip hop
/ifudodo heavy metal
/ifudodo jazz piano
/ifudodo 8bit chiptune
/ifudodo orchestral epic
```

スタイルを記述すると、威風堂々の原曲をベースに repaint モードでリミックスした音声ファイル（MP3）が返されます。

## 設定項目

`.env` で以下を変更できます:

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `DISCORD_TOKEN` | (必須) | Discord Bot トークン |
| `GUILD_ID` | (なし) | 開発用サーバーID（設定するとコマンド反映が即座） |
| `REFERENCE_MELODY_PATH` | `assets/ifudodo_source.wav` | リファレンス楽曲のパス |
| `ACESTEP_AUDIO_DURATION` | `180` | 生成する音声の長さ (秒) |
| `ACESTEP_INFER_STEP` | `60` | 推論ステップ数（多いほど高品質・低速） |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama サーバーのアドレス |
| `OLLAMA_MODEL` | `gemma3` | スタイル調査に使うモデル |
| `MAX_FILE_SIZE_MB` | `24` | Discord アップロード上限 (MB) |

## 仕組み

1. `/ifudodo <スタイル>` コマンドを受信
2. 威風堂々の音楽特徴 + ユーザー指定スタイルでプロンプトを構築
3. ACE-Step 1.5 の **repaint モード** で原曲音声をソースに、指定スタイルで再生成
4. WAV → MP3 に変換して Discord に送信
