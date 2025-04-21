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
    async def steal(self, ctx, *, args: str):
        """Steal an emoji from a URL and upload it to the server."""

        # Split the input by space to handle multiple URLs
        urls = args.split()
        for url in urls:
            # Extract actual URL if Markdown-style link is given
            markdown_link = re.match(r'\[.*?\]\((.*?)\)', url)
            url = markdown_link.group(1) if markdown_link else url

            parsed = urlparse(url)

            # Ensure this is a proper Discord CDN emoji URL
            if not parsed.netloc.endswith("discordapp.com") and not parsed.netloc.endswith("cdn.discordapp.com"):
                await ctx.send(f"Invalid URL: {url}. Please provide a direct Discord emoji URL.")
                continue

            # Remove query string and get name from it
            base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            qs = parse_qs(parsed.query)
            name = qs.get("name", [None])[0]

            # If no 'name' is provided in the URL, attempt to derive the name from the filename
            if not name:
                name = parsed.path.split("/")[-1].split(".")[0]

            if not name:
                await ctx.send(f"Could not extract emoji name from URL: {url}.")
                continue

            # Check if URL has `.webp` and replace it with `.gif` or `.png`
            animated = False
            if base_url.endswith(".webp"):
                if "animated" in qs and qs["animated"][0] == "true":
                    base_url = base_url.replace(".webp", ".gif")
                    animated = True
                else:
                    base_url = base_url.replace(".webp", ".png")

            # Get the image
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(base_url) as resp:
                        if resp.status != 200:
                            await ctx.send(f"Failed to download emoji image from {url}.")
                            continue
                        image_data = await resp.read()
            except Exception as e:
                await ctx.send(f"An error occurred while downloading the image from {url}: {e}")
                continue

            # Upload as custom emoji
            try:
                emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data)
                if animated:
                    await ctx.send(f"Animated emoji added: <a:{emoji.name}:{emoji.id}>")
                else:
                    await ctx.send(f"Emoji added: <:{emoji.name}:{emoji.id}>")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to add emoji from {url}: {e}")
            except discord.Forbidden:
                await ctx.send("I don't have permission to manage emojis.")
