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
