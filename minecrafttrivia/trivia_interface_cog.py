import typing

import discord
from discord.ext.commands import guild_only
from redbot.core import commands, Config
from redbot.core.bot import Red

from . import utils
from .game import OngoingGame, CraftingGame, GamePhase


class TriviaInterfaceCog(commands.Cog):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.config = Config.get_conf(self, identifier=262200644)
		self.config.register_global(version=0)
		self.config.register_guild(
			join_timeout=30,
			guess_timeout=60,
			total_scores={},
			high_scores={},
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

	@commands.command(aliases=["mctrivia", "mct"])
	@guild_only()
	async def minecrafttrivia(self, ctx: commands.GuildContext, action: str = "new"):
		"""Starts a game of minecraft trivia"""
		game = self.get_game(ctx.channel)
		if action == "new":
			if game:
				return await ctx.send("Game already started.")
			game = self.create_game(ctx.bot, ctx.channel)
			await game.start_signup()
		elif action[:4] == "high":
			high_scores = await self.config.guild(ctx.guild).high_scores()
			await ctx.send(embed=discord.Embed(
				title=f"MC Trivia Highscores for {ctx.guild.name}",
				description=utils.format_leaderboard(utils.create_leaderboard(high_scores))))
		elif action[:4] == "lead":
			total_scores = await self.config.guild(ctx.guild).total_scores()
			await ctx.send(embed=discord.Embed(
				title=f"MC Trivia Leaderboard for {ctx.guild.name}",
				description=utils.format_leaderboard(utils.create_leaderboard(total_scores))
			))
