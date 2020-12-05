import typing

import discord

from . import constants


async def get_participants(reactions: typing.List[discord.Reaction]) -> typing.List[discord.User]:
	for r in reactions:
		if r.emoji == constants.POSITIVE_REACTION:
			users = []
			async for u in r.users():
				if not u.bot:
					users.append(u)
			return users
	return []


def format_leaderboard(points: typing.List[typing.Tuple[int, typing.Tuple[typing.Union[discord.User, int], int]]]) -> str:
	return "\n".join(f"**{rank + 1}.** {user.mention if hasattr(user, 'mention') else '<@' + str(user) + '>'} - {points}" for rank, (user, points) in points[:20])


_T = typing.TypeVar("_T", discord.User, int)


def create_leaderboard(points: typing.Dict[_T, int]) -> typing.List[typing.Tuple[int, typing.Tuple[_T, int]]]:
	return list(enumerate(reversed(sorted(points.items(), key=lambda x: x[1]))))
