import discord
from discord import app_commands
from discord.ext import commands
from database import init_db, get_challenges, get_scores, add_solved_challenge
from database import FIRST_BLOOD_BONUS, SECOND_SOLVE_BONUS, THIRD_SOLVE_BONUS
from config import Config
import typing

Server_id=""
Token=""

class AttachmentsButton(discord.ui.View):
    """Class that handles the behaviour of the attachment button."""
    def __init__(self, attachment_url):
        super().__init__()
        button = discord.ui.Button(
            label="📎 Attachment",
            style=discord.ButtonStyle.url,
            url=attachment_url
        )
        self.add_item(button)

class RoleSelect(discord.ui.Select):
    def __init__(self, roles, config):
        filtered_roles = [
            role for role in roles 
            if not role.managed and role.name != "@everyone"
        ]
        
        options = [
            discord.SelectOption(
                label=role.name,
                value=str(role.id),
                description=f"Select {role.name} as CTF participant role"
            ) for role in filtered_roles
        ]
        
        # Ensure we have at least one option
        if not options:
            options = [
                discord.SelectOption(
                    label="No roles available",
                    value="0",
                    description="Please create a role first"
                )
            ]
            
        super().__init__(
            placeholder="Select the CTF participant role...",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )
        self.config = config

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "0":
            await interaction.response.send_message(
                "Please create a role first and run setup again.",
                ephemeral=False
            )
            return
            
        self.config.set("ctf_role", int(self.values[0]))
        await interaction.response.send_message(
            f"Selected Role: <@&{self.values[0]}>",
            ephemeral=False
        )

class ChannelSelect(discord.ui.Select):
    def __init__(self, channels, config):
        filtered_channels = [
            channel for channel in channels
            if isinstance(channel, discord.TextChannel)
        ]
        
        options = [
            discord.SelectOption(
                label=channel.name,
                value=str(channel.id),
                description=f"#{channel.name}"
            ) for channel in filtered_channels
        ]
        
        # Ensure we have at least one option
        if not options:
            options = [
                discord.SelectOption(
                    label="No channels available",
                    value="0",
                    description="Please create a text channel first"
                )
            ]
            
        super().__init__(
            placeholder="Select the announcement channel...",
            min_values=1,
            max_values=1,
            options=options,
            row=1
        )
        self.config = config

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "0":
            await interaction.response.send_message(
                "Please create a text channel first and run setup again.",
                ephemeral=False
            )
            return
            
        self.config.set("announcement_channel", int(self.values[0]))
        await interaction.response.send_message(
            f"Selected Channel: <#{self.values[0]}>",
            ephemeral=False
        )

class SetupView(discord.ui.View):
    def __init__(self, roles, channels, config):
        super().__init__()
        self.add_item(RoleSelect(roles, config))
        self.add_item(ChannelSelect(channels, config))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Add this line

bot = commands.Bot(command_prefix="!", intents=intents)

# Add this function before @bot.event
async def setup_hook():
    bot.tree.copy_global_to(guild=discord.Object(id=Server_id))  # Replace YOUR_SERVER_ID with your server's ID
    await bot.tree.sync()

bot.setup_hook = setup_hook  # Add this line after bot creation

# Load challenges and scores
challenges = {}
scores = {}
config = Config()

@bot.event
async def on_ready():
    global challenges, scores
    print(f'{bot.user} Connected')
    init_db()
    challenges = get_challenges()
    scores = get_scores()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="list_challenges", description="List challenge yang ada")
async def list_challenges(interaction: discord.Interaction):
    embed = discord.Embed(title="CTF Challenges", color=0x00ff00)
    for category in challenges:
        challenge_list = []
        for chall in challenges[category]:
            status = "✅" if str(interaction.user.id) in scores and chall['name'] in scores[str(interaction.user.id)]['solved'] else "❌"
            challenge_list.append(f"{status} {chall['name']} ({chall['points']} pts)")
        embed.add_field(name=category, value='\n'.join(challenge_list) or "No challenges", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="challenge", description="Detail challenge tertentu")
@app_commands.describe(challenge_name="nama challenge yang ingin dilihat")
async def show_challenge(interaction: discord.Interaction, challenge_name: str):
    for category in challenges:
        for chall in challenges[category]:
            if chall['name'].lower() == challenge_name.lower():
                embed = discord.Embed(title=chall['name'], color=0x0000ff)
                embed.add_field(name="Category", value=category, inline=False)
                embed.add_field(name="Description", value=chall['description'], inline=False)
                embed.add_field(name="Points", value=str(chall['points']), inline=False)
                
                # Check if challenge has an attachment
                if chall.get('attachment_url'):
                    view = AttachmentsButton(chall['attachment_url'])
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=False)
                return
    await interaction.response.send_message("Challenge not found!", ephemeral=False)

@bot.tree.command(name="submit", description="Submit flag untuk challenge")
@app_commands.describe(
    challenge_name="Nama challenge yang ingin di-submit",
    flag="Flag yang ingin di-submit"
)
async def submit_flag(interaction: discord.Interaction, challenge_name: str, flag: str):
    # Check if user has required role
    ctf_role = config.get("ctf_role")
    if ctf_role and not interaction.guild.get_role(ctf_role) in interaction.user.roles:
        await interaction.response.send_message(
            "You don't have permission to submit flags!", 
            ephemeral=False
        )
        return

    global scores
    await interaction.response.defer(ephemeral=False)
    
    for category in challenges:
        for chall in challenges[category]:
            if chall['name'].lower() == challenge_name.lower():
                if chall['flag'] == flag:
                    user_id = str(interaction.user.id)
                    if user_id not in scores:
                        scores[user_id] = {"name": interaction.user.name, "points": 0, "solved": []}
                    
                    if challenge_name not in scores[user_id]['solved']:
                        solve_order, bonus_points = add_solved_challenge(user_id, interaction.user.name, chall['id'], chall['points'])
                        scores = get_scores()  # Update local cache
                        
                        # Create blood messages
                        blood_msg = ""
                        if solve_order == 1:
                            blood_msg = f"🩸 **FIRST BLOOD!** +{FIRST_BLOOD_BONUS} bonus points!"
                        elif solve_order == 2:
                            blood_msg = f"🥈 **Second Solve!** +{SECOND_SOLVE_BONUS} bonus points!"
                        elif solve_order == 3:
                            blood_msg = f"🥉 **Third Solve!** +{THIRD_SOLVE_BONUS} bonus points!"
                        
                        # Send private success message
                        await interaction.followup.send(
                            f"🎉 Correct flag! You earned {chall['points']} points!\n{blood_msg}",
                            ephemeral=False
                        )
                        
                        # Announce in channel with blood status
                        announce_msg = f"🎉 {interaction.user.mention} has solved {challenge_name}!"
                        if blood_msg:
                            announce_msg += f"\n{blood_msg}"
                        
                        announcement_channel_id = config.get("announcement_channel")
                        if announcement_channel_id:
                            channel = interaction.guild.get_channel(announcement_channel_id)
                            if channel:
                                await channel.send(announce_msg)
                        else:
                            await interaction.channel.send(announce_msg)
                    else:
                        await interaction.followup.send("You've already solved this challenge!", ephemeral=False)
                    return
                else:
                    await interaction.followup.send("❌ Wrong flag!", ephemeral=False)
                return
    await interaction.followup.send("Challenge not found!", ephemeral=False)

@bot.tree.command(name="scoreboard", description="Show the CTF scoreboard")
async def show_scoreboard(interaction: discord.Interaction):
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]['points'], reverse=True)
    embed = discord.Embed(title="CTF Scoreboard", color=0xff0000)
    
    for i, (user_id, user_data) in enumerate(sorted_scores[:10], 1):
        embed.add_field(
            name=f"{i}. {user_data['name']}",
            value=f"Points: {user_data['points']}\nSolved: {len(user_data['solved'])}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="setup", description="Configure CTF settings")
async def setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need to be an administrator to use this command!", ephemeral=True)
        return
    
    view = SetupView(
        interaction.guild.roles,
        interaction.guild.channels,
        config
    )
    await interaction.response.send_message(
        "Please configure the CTF settings:", 
        view=view,
        ephemeral=True
    )

bot.run(Token)
