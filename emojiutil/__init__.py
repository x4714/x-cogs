from .emojiutil import emojiutil


async def setup(bot):
    await bot.add_cog(emojiutil(bot))