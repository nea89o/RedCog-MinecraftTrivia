import typing

import discord
from discord.ext.commands import guild_only
from redbot.core import commands, Config, checks
from redbot.core.bot import Red

from . import utils
from .game import OngoingGame, CraftingGame, GamePhase


class TriviaInterfaceCog(commands.Cog, name="MinecraftTrivia"):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.config = Config.get_conf(self, identifier=262200644)
		self.config.register_global(version=0)
		self.config.register_guild(
			join_timeout=30,
			guess_timeout=60,
			round_count=10,
			min_players=2,
			total_scores={},
			high_scores={},
			current_winstreak={},
		)
		self.active_games_per_channel: typing.Dict[int, OngoingGame] = {}

	def get_game(self, channel: discord.TextChannel) -> typing.Optional[OngoingGame]:
		game = channel.id in self.active_games_per_channel and self.active_games_per_channel[channel.id]
		if game and game.phase != GamePhase.FINISHED:
			return game

	def create_game(self, bot: Red, channel: discord.TextChannel) -> OngoingGame:
		game = CraftingGame(bot, self.config, channel)
		self.active_games_per_channel[channel.id] = game
		return game

	@commands.group(aliases=["mctrivia", "mct"], invoke_without_command=True)
	@guild_only()
	async def minecrafttrivia(self, ctx: commands.GuildContext, *, extra=""):
		"""Starts a game of minecraft trivia"""
		if extra:
			await ctx.send("Invalid subcommand.")
		game = self.get_game(ctx.channel)
		if game:
			return await ctx.send("Game already started.")
		game = self.create_game(ctx.bot, ctx.channel)
		await game.start_signup()

	@minecrafttrivia.command(aliases=["now"])
	@guild_only()
	@checks.mod()
	async def startnow(self, ctx: commands.GuildContext):
		game = self.get_game(ctx.channel)
		if not game:
			return await ctx.send("No game running")
		await game.start_game()

	@minecrafttrivia.group(aliases=["config"], invoke_without_command=True)
	@guild_only()
	@checks.admin()
	async def set(self, ctx: commands.GuildContext):
		"""Sets config options. execute without arguments to see all options"""
		await ctx.send("Available config options: join_timeout guess_timeout round_count min_players")

	@set.command(aliases=["join"])
	@guild_only()
	@checks.admin()
	async def join_timeout(self, ctx: commands.GuildContext, to: int = None):
		c = self.config.guild(ctx.guild)
		if to:
			await c.join_timeout.set(to)
			await ctx.send(f"Set `join_timeout` to `{to}`")
		else:
			await ctx.send(f"`join_timeout` is `{await c.join_timeout()}`")

	@set.command(aliases=["players"])
	@guild_only()
	@checks.admin()
	async def min_players(self, ctx: commands.GuildContext, to: int = None):
		c = self.config.guild(ctx.guild)
		if to:
			await c.min_players.set(to)
			await ctx.send(f"Set `min_players` to `{to}`")
		else:
			await ctx.send(f"`min_players` is `{await c.min_players()}`")

	@set.command(aliases=["guess"])
	@guild_only()
	@checks.admin()
	async def guess_timeout(self, ctx: commands.GuildContext, to: int = None):
		c = self.config.guild(ctx.guild)
		if to:
			await c.guess_timeout.set(to)
			await ctx.send(f"Set `guess_timeout` to `{to}`")
		else:
			await ctx.send(f"`guess_timeout` is `{await c.guess_timeout()}`")

	@set.command(aliases=["rounds"])
	@guild_only()
	@checks.admin()
	async def round_count(self, ctx: commands.GuildContext, to: int = None):
		c = self.config.guild(ctx.guild)
		if to:
			await c.round_count.set(to)
			await ctx.send(f"Set `round_count` to `{to}`")
		else:
			await ctx.send(f"`round_count` is `{await c.round_count()}`")

	@minecrafttrivia.command(aliases=["high"])
	@guild_only()
	async def highscore(self, ctx: commands.GuildContext):
		"""Show single-round highscore leaderboard"""
		high_scores = await self.config.guild(ctx.guild).high_scores()
		await ctx.send(embed=discord.Embed(
			title=f"MC Trivia Highscores for {ctx.guild.name}",
			description=utils.format_leaderboard(utils.create_leaderboard(high_scores))))

	@minecrafttrivia.command(aliases=["lead", "total"])
	@guild_only()
	async def leaderboard(self, ctx: commands.GuildContext):
		"""Show total summed up highscore leaderboard"""
		total_scores = await self.config.guild(ctx.guild).total_scores()
		await ctx.send(embed=discord.Embed(
			title=f"MC Trivia Leaderboard for {ctx.guild.name}",
			description=utils.format_leaderboard(utils.create_leaderboard(total_scores))
		))

	@minecrafttrivia.command(aliases=["win"])
	@guild_only()
	async def winstreak(self, ctx: commands.GuildContext):
		winstreaks = await self.config.guild(ctx.guild).current_winstreak()
		await ctx.send(embed=discord.Embed(
			title=f"MC Trivia Current Winstreaks in {ctx.guild.name}",
			description=utils.format_leaderboard(utils.create_leaderboard(winstreaks))
		))

	@minecrafttrivia.command()
	async def info(self, ctx: commands.Context):
		"""Show info about this cog"""
		embed = discord.Embed(
			title="MC Trivia Cog by romangraef89",
			description="This cog allows you to compete against your friends in a race to guess minecraft crafting recipes the fastest"
		)
		embed.add_field(name="Github / Source", value="[romangraef89/RedCog-MinecraftTrivia](https://github.com/romangraef/RedCog-MinecraftTrivia)", inline=False)
		embed.add_field(name="Issue Tracker", value="[Click here](https://github.com/romangraef/RedCog-MinecraftTrivia/issues)", inline=False)
		embed.add_field(name="Minecraft Version", value="1.16 (Open an issue if a newer version exists)", inline=False)
		await ctx.send(embed=embed)
