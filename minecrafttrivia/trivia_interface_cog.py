import typing

import discord
from discord.ext.commands import guild_only
from redbot.core import commands
from redbot.core.bot import Red

from .game import OngoingGame, CraftingGame


class TriviaInterfaceCog(commands.Cog):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.active_games_per_channel: typing.Dict[int,] = {}

	def get_game(self, channel: discord.TextChannel) -> typing.Optional[OngoingGame]:
		return channel.id in self.active_games_per_channel and self.active_games_per_channel[channel.id]

	def create_game(self, bot: Red, channel: discord.TextChannel) -> OngoingGame:
		game = CraftingGame(bot, channel)
		self.active_games_per_channel[channel.id] = game
		return game

	@commands.command(aliases=["mctrivia", "mct"])
	@guild_only()
	async def minecrafttrivia(self, ctx: commands.GuildContext):
		"""Starts a game of minecraft trivia"""
		game = self.get_game(ctx.channel)
		if game:
			return await ctx.send("Game already started.")
		game = self.create_game(ctx.bot, ctx.channel)
		await game.start_signup()
