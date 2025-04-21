import discord
from redbot.core import commands
import aiohttp
from urllib.parse import urlparse, parse_qs
import re


class emojiutil(commands.Cog):
    """Cog to do stuff with emojis."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_emojis=True)
    async def steal(self, ctx, *, arg: str):
        """Steal an emoji from a URL and upload it to the server."""

        # Extract actual URL if Markdown-style link is given
        markdown_link = re.match(r'\[.*?\]\((.*?)\)', arg)
        url = markdown_link.group(1) if markdown_link else arg

        parsed = urlparse(url)

        # Ensure this is a proper Discord CDN emoji URL
        if not parsed.netloc.endswith("discordapp.com") and not parsed.netloc.endswith("cdn.discordapp.com"):
            return await ctx.send("Invalid URL. Please provide a direct Discord emoji URL.")

        # Remove query string and get name from it
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        qs = parse_qs(parsed.query)
        name = qs.get("name", [None])[0]

        if not name:
            return await ctx.send("Could not extract emoji name from URL.")

        if base_url.endswith(".webp"):
            if "animated" in qs and qs["animated"][0] == "true":
                base_url = base_url.replace(".webp", ".gif")
            else:
                base_url = base_url.replace(".webp", ".png")

        # Get the image
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url) as resp:
                    if resp.status != 200:
                        return await ctx.send("Failed to download emoji image.")
                    image_data = await resp.read()
        except Exception as e:
            return await ctx.send(f"An error occurred while downloading the image: {e}")

        # Upload as custom emoji
        try:
            emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data)
            await ctx.send(f"Emoji added: <:{emoji.name}:{emoji.id}>")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to add emoji: {e}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage emojis.")
