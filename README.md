# ifudodo-mix

威風堂々の音楽ミックスを生成する Discord bot。Meta の [MusicGen](https://github.com/facebookresearch/audiocraft) をローカルで動かし、ユーザーが指定したスタイルでリミックスを生成します。

## 必要環境

- [pixi](https://pixi.sh/) (パッケージマネージャ)
- CUDA 対応 GPU (VRAM 10GB 以上推奨)
- Discord Bot トークン

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
```

### 4. 起動

```bash
pixi run start
```

## 使い方

Discord で `/ifudodo` コマンドを使います:

```
/ifudodo lo-fi hip hop
/ifudodo heavy metal
/ifudodo jazz piano
/ifudodo 8bit chiptune
/ifudodo orchestral epic
```

スタイルを記述すると、威風堂々のメロディをベースにそのスタイルでリミックスした音声ファイルが返されます。

## 設定項目

`.env` で以下を変更できます:

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `DISCORD_TOKEN` | (必須) | Discord Bot トークン |
| `GUILD_ID` | (なし) | 開発用サーバーID |
| `MUSICGEN_MODEL` | `facebook/musicgen-melody` | MusicGen モデル名 |
| `DEVICE` | `cuda` | 推論デバイス (`cuda` / `cpu`) |
| `DURATION` | `15` | 生成する音声の長さ (秒) |
| `REFERENCE_MELODY_PATH` | `assets/ifudodo_source.mp4` | リファレンス楽曲のパス |
| `OUTPUT_FORMAT` | `wav` | 出力フォーマット |

## 仕組み

1. `/ifudodo <スタイル>` コマンドを受信
2. 威風堂々の音楽特徴 + ユーザー指定スタイルでプロンプトを構築
3. MusicGen の **メロディコンディショニング** でリファレンス楽曲のメロディを保ちつつ、指定スタイルで音声を生成
4. 生成された音声ファイルを Discord に送信
