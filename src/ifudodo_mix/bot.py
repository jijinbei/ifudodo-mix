import logging

import discord
from discord import app_commands

from .acestep_generator import ACEStepGenerator, GenerationError
from .audio_utils import check_file_size, cleanup_temp_file, convert_to_mp3
from .config import Config
from .prompt_builder import build_prompt

logger = logging.getLogger(__name__)


class IfudodoBot(discord.Client):
    def __init__(self, config: Config):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.config = config
        self.tree = app_commands.CommandTree(self)
        self.generator = ACEStepGenerator(config)

    async def setup_hook(self) -> None:
        await self.generator.setup()
        self._register_commands()

        if self.config.guild_id:
            guild = discord.Object(id=self.config.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info("Synced commands to guild %s", self.config.guild_id)
        else:
            await self.tree.sync()
            logger.info("Synced commands globally")

    def _register_commands(self) -> None:
        @self.tree.command(
            name="ifudodo",
            description="威風堂々のミックスを生成します",
        )
        @app_commands.describe(
            description="ミックスのスタイルを記述してください（例: 'lo-fi hip hop', 'heavy metal', 'jazz piano'）",
        )
        async def ifudodo(
            interaction: discord.Interaction, description: str
        ) -> None:
            await interaction.response.defer(thinking=True)

            audio_path = None
            try:
                prompt = build_prompt(description)
                logger.info(
                    "User %s requested mix: %r -> prompt: %r",
                    interaction.user,
                    description,
                    prompt,
                )

                audio_path = await self.generator.generate(prompt)

                if audio_path.suffix != ".mp3":
                    audio_path = convert_to_mp3(audio_path)

                if not check_file_size(
                    audio_path, self.config.max_file_size_mb
                ):
                    await interaction.followup.send(
                        content="生成された音声ファイルが大きすぎます。短いdurationを試してください。"
                    )
                    return

                filename = "ifudodo_mix.mp3"
                file = discord.File(str(audio_path), filename=filename)
                await interaction.followup.send(
                    content=f"**威風堂々 mix: {description}**",
                    file=file,
                )

            except GenerationError as e:
                logger.warning("Generation error: %s", e)
                await interaction.followup.send(content=f"エラー: {e}")

            except Exception as e:
                logger.exception("Unexpected error during generation")
                await interaction.followup.send(
                    content=f"生成中にエラーが発生しました: {e}"
                )

            finally:
                if audio_path is not None:
                    cleanup_temp_file(audio_path)

    async def on_ready(self) -> None:
        logger.info("Bot is ready: %s (ID: %s)", self.user, self.user.id)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = Config()
    bot = IfudodoBot(config)
    bot.run(config.discord_token)
