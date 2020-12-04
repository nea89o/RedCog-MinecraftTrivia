import asyncio
import random
import typing
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum, auto

import discord
from redbot.core.bot import Red

from . import constants, utils
from .recipe_provider import DEFAULT_RECIPE_PROVIDER


class GamePhase(Enum):
	INACTIVE = auto()
	SIGNUP = auto()
	RUNNING = auto()
	FINISHED = auto()


class OngoingGame(ABC):
	participants: typing.List[discord.User]
	channel: discord.TextChannel
	phase: GamePhase
	signup_message: discord.Message

	def __init__(self, bot: Red, channel: discord.TextChannel):
		self.participants = []
		self.bot = bot
		self.channel = channel
		self.phase = GamePhase.INACTIVE

	async def start_signup(self):
		self.phase = GamePhase.SIGNUP
		embed = discord.Embed(
			title="Signups opened for new game of Minecraft trivia",
			description="React to this message in order to join. You have 30 seconds to signup.",
		)
		embed.timestamp = datetime.now() + timedelta(seconds=30)
		self.signup_message = await self.channel.send(embed=embed)
		await self.signup_message.add_reaction(constants.POSITIVE_REACTION)
		await asyncio.sleep(30)
		embed.description = "Signups are now closed. Wait for the game to finish to start a new one."
		await self.signup_message.edit(embed=embed)
		self.participants = await utils.get_participants((await self.channel.fetch_message(self.signup_message.id)).reactions)
		await self.start_game()

	async def start_game(self):
		self.phase = GamePhase.RUNNING
		await self.gameloop()

	async def conclude_game(self):
		self.phase = GamePhase.FINISHED
		embed = discord.Embed(
			title="Minecraft Trivia Finished",
			description=self.leaderboard(),
		)
		await self.channel.send(embed=embed)

	async def gameloop(self):
		for i in range(5):
			await self.single_round(i)
		await self.conclude_game()

	async def wait_for_participant_messages(self, consumer: typing.Callable[[discord.Message], typing.Awaitable[bool]]):
		"""
		Calls consumer for all participant messages in this channel. consumer(mes) should return True if this is the final accepted message. Consumer is a callable
		"""

		def check(mes: discord.Message):
			if mes.channel.id != self.channel.id:
				return False
			if mes.author.id not in map(lambda x: x.id, self.participants):
				return False
			return True

		until = datetime.now() + timedelta(seconds=60)
		while True:
			try:
				mes = await self.bot.wait_for('message', check=check, timeout=(until - datetime.now()).total_seconds())
				if await consumer(mes):
					return
			except asyncio.TimeoutError:
				return

	async def wait_for_correct_answer(self, answer_filter: typing.Callable[[str], bool]) -> typing.Optional[discord.User]:
		u = None

		async def check(mes: discord.Message):
			nonlocal u
			if answer_filter(mes.content):
				u = mes.author
				return True

		await self.wait_for_participant_messages(check)
		return u

	@abstractmethod
	def leaderboard(self) -> str:
		pass

	@abstractmethod
	async def single_round(self, round_number: int):
		pass


class PointBasedGame(OngoingGame, ABC):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.points = {}

	@property
	def ranks(self) -> typing.List[typing.Tuple[int, typing.Tuple[discord.User, int]]]:
		return list(enumerate(reversed(sorted(self.points.items(), key=lambda x: x[1]))))

	async def start_game(self):
		for u in self.participants:
			self.points[u] = 0
		return await super().start_game()

	def leaderboard(self) -> str:
		return "\n".join(f"**{rank + 1}.** {user.mention} - {points}" for rank, (user, points) in self.ranks)


class XDGame(PointBasedGame):

	async def single_round(self, round_number: int):
		await self.channel.send("xd?")

		def answer_filter(msg: str) -> bool:
			return msg.casefold() == "xd".casefold()

		round_winner = await self.wait_for_correct_answer(answer_filter)
		self.points[round_winner] += 1
		await self.channel.send(f"{round_winner.mention} won this round")


class CraftingGame(PointBasedGame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.used_recipes: typing.List[int] = []

	def random_recipe(self):
		index = -1
		while index in self.used_recipes or index < 0:
			index = random.randint(0, len(DEFAULT_RECIPE_PROVIDER.recipes) - 1)
		self.used_recipes.append(index)
		return DEFAULT_RECIPE_PROVIDER.recipes[index]

	@staticmethod
	def get_name(obj: str) -> str:
		return DEFAULT_RECIPE_PROVIDER.get_all_names(obj)[-1]

	async def single_round(self, round_number: int):
		recipe = self.random_recipe()
		items_left_to_find = recipe.ingredients.copy()

		embed = discord.Embed(title=f"RECIPE REQUIRED: {self.get_name(recipe.result)}")
		embed.description = "Items found so far:"
		message = await self.channel.send(embed=embed)

		async def check(msg: discord.Message):
			inp = msg.content.casefold().replace(' ', '')

			for ingredient in items_left_to_find:
				found = False
				for item in ingredient.allowed_items:
					names = DEFAULT_RECIPE_PROVIDER.get_all_names(item)
					name_correct = False
					for name in names:
						if inp == name.casefold().replace(' ', ''):
							name_correct = True
					if not name_correct:
						continue
					embed.description += f"\n{names[-1]} ({ingredient.count}) found by {msg.author.mention}"
					await message.edit(embed=embed)
					self.points[msg.author] += 1
					items_left_to_find.remove(ingredient)
					found = True
					break
				if found:
					break
			return len(items_left_to_find) == 0

		await self.wait_for_participant_messages(check)
		embed.description += "\n\nAll items found"
		await self.channel.edit(embed=embed)
