#!/usr/bin/env python3
"""
NBA 2K Discord Bot
Main bot file for handling Discord commands and player data requests
"""

import discord
from discord.ext import commands
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import jina_scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jina_scraper import JinaNBA2KScraper

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Initialize scraper
scraper = JinaNBA2KScraper()

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Set bot status
    await bot.change_presence(activity=discord.Game(name="!player <name> | NBA 2K25"))

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Use `!help` for usage information.")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")

@bot.command(name='player')
async def player_search(ctx, *, player_name: str):
    """
    Search for a player by name
    Usage: !player <player_name>
    Example: !player "Stephen Curry"
    """
    if not player_name.strip():
        await ctx.send("❌ Please provide a player name. Usage: `!player <player_name>`")
        return
    
    # Send initial response
    loading_msg = await ctx.send(f"🔍 Searching for **{player_name}**...")
    
    try:
        # Search for player
        players = scraper.search_player(player_name)
        
        if not players:
            await loading_msg.edit(content=f"❌ No player found for **{player_name}**")
            return
        
        player = players[0]  # Get first result
        
        # Create embed for player data
        embed = create_player_embed(player)
        
        await loading_msg.edit(content="", embed=embed)
        
    except Exception as e:
        await loading_msg.edit(content=f"❌ Error searching for player: {str(e)}")

@bot.command(name='help')
async def help_command(ctx):
    """Show help information"""
    embed = discord.Embed(
        title="🏀 NBA 2K Discord Bot Help",
        description="Get NBA 2K25 player ratings and statistics",
        color=0x00ff00
    )
    
    embed.add_field(
        name="📋 Available Commands",
        value="""
        **!player <name>** - Search for a player
        **!help** - Show this help message
        
        *More commands coming soon!*
        """,
        inline=False
    )
    
    embed.add_field(
        name="📝 Examples",
        value="""
        `!player Stephen Curry`
        `!player LeBron James`
        `!player Nikola Jokic`
        """,
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Information",
        value="Data sourced from 2kratings.com via Jina.ai",
        inline=False
    )
    
    embed.set_footer(text="NBA 2K Discord Bot")
    
    await ctx.send(embed=embed)

def create_player_embed(player):
    """Create a Discord embed for player data"""
    embed = discord.Embed(
        title=f"🏀 {player['name']}",
        description=f"**Overall Rating: {player['overall_rating']}**",
        color=get_rating_color(player['overall_rating'])
    )
    
    # Player details
    if player['player_details']:
        details = player['player_details']
        embed.add_field(
            name="📊 Player Info",
            value=f"""
            **Position:** {details.get('position', 'N/A')}
            **Team:** {details.get('team', 'N/A')}
            **Height:** {details.get('height', 'N/A')}
            **Weight:** {details.get('weight', 'N/A')}
            **Wingspan:** {details.get('wingspan', 'N/A')}
            **Archetype:** {details.get('archetype', 'N/A')}
            """,
            inline=True
        )
    
    # Attributes
    if player['attributes']:
        attr_text = ""
        for attr, attr_data in player['attributes'].items():
            attr_text += f"**{attr}:** {attr_data['rating']}\n"
        
        embed.add_field(
            name="📈 Attributes",
            value=attr_text,
            inline=True
        )
    
    # Badge summary
    if player['badge_info']:
        badge_info = player['badge_info']
        badge_text = f"""
        **Total:** {badge_info['total_badges']}
        **HOF:** {badge_info['hof_badges']} | **Gold:** {badge_info['gold_badges']}
        **Silver:** {badge_info['silver_badges']} | **Bronze:** {badge_info['bronze_badges']}
        """
        
        embed.add_field(
            name="🏆 Badges",
            value=badge_text,
            inline=True
        )
    
    embed.set_footer(text="Data from 2kratings.com")
    
    return embed

def get_rating_color(rating):
    """Get color based on overall rating"""
    if rating >= 95:
        return 0xFFD700  # Gold
    elif rating >= 90:
        return 0xC0C0C0  # Silver
    elif rating >= 85:
        return 0xCD7F32  # Bronze
    else:
        return 0x808080  # Gray

def main():
    """Main function to run the bot"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ DISCORD_TOKEN not found in environment variables")
        return
    
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Error running bot: {e}")

if __name__ == "__main__":
    main() 