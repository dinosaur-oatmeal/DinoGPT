import os
import time
import openai
import discord
import datetime
import asyncio
from openai import OpenAI
from typing import Optional
from discord import app_commands
from discord import Embed, Interaction, SelectOption
from discord.ext import commands, tasks
from discord.ui import View, Select
from dotenv import load_dotenv
from collections import defaultdict, deque

# 277025508352

# Load API KEY
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

intents = discord.Intents.default()
# Required by not used (/command)
bot = commands.Bot(command_prefix="!", intents=intents)

# Conversation history for different users
conversation_history = defaultdict(list)

OWNER_ID = int(os.getenv("OWNER_ID"))

MAX_GUILDS = 3

# Draw cooldown
last_draw_times = defaultdict(float)
DRAW_COOLDOWN = 30

# Track the last 5 dino facts
recent_facts = deque(maxlen = 5)

ALLOWED_CHANNEL_IDS = [1400598300201324574, 1364724551916978259]

# Reset conversation history daily
@tasks.loop(time=datetime.time(hour=4, minute=0))
async def reset_conversation_history():
    conversation_history.clear()

# Block DMs to DinoGPT
@bot.event
async def on_message(message):
    if message.guild is None or message.author.bot:
        return
    
    await bot.process_commands(message)

# Limit bot to max number of guilds
@bot.event
async def on_guild_join(guild):
    # Leave new guilds once limit reached
    if len(bot.guilds) > MAX_GUILDS:
        # Alert owner (me) of the guild it was invited to
        try:
            owner = await bot.fetch_user(OWNER_ID)
            if owner:
                await owner.send(
                    f"I was invited to\nServer Name: `{guild.name}`\nServer ID: `{guild.id}`\n I am now leaving"
                )
        except Exception as e:
            print(f"Failed to DM owner: {e}")

        # Leave the new guild
        await asyncio.sleep(1)
        await guild.leave()

# Sync all slash commands on boot
@bot.event
async def on_ready():
    # Start daily reset task
    if not reset_conversation_history.is_running():
        reset_conversation_history.start()

    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

class ResourcesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ResourcesSelect())

class ResourcesSelect(Select):
    def __init__(self):
        options = [
            SelectOption(label="Math Clinic", value="math"),
            SelectOption(label="The BugHouse (CSE)", value="bughouse"),
            SelectOption(label="Writing Center", value="writing"),
            SelectOption(label="Academic Success Center", value="success"),
            SelectOption(label="Advising Center", value="advising"),
            SelectOption(label="Testing Services", value="testing"),
            SelectOption(label="Accessibility Center", value="access")
        ]

        super().__init__(placeholder="Choose a resource to learn more...",
                         min_values=1, max_values=1, options=options)

    # List of UTA Resources
    async def callback(self, interaction: Interaction):
        resource_details = {
            "math": {
                "title": "🧮 Math Clinic",
                "desc": "Support for undergraduate math courses.",
                "location": "Pickard Hall 325",
                "hours": "Mon-Thu: 9am-8pm\nFri: 9am-12pm\nSun: 1pm-5pm",
                "link": "https://www.uta.edu/academics/schools-colleges/science/departments/mathematics/lrc/uta-math-clinic"
            },
            "bughouse": {
                "title": "🐞 The bugHouse (CSE)",
                "desc": "Tutoring and review sessions for computer science.",
                "location": "ERB 570",
                "hours": "Mon-Fri: 10am-6pm",
                "link": "https://www.uta.edu/academics/schools-colleges/engineering/academics/departments/cse/students/bughouse"
            },
            "writing": {
                "title": "📖 Writing Center",
                "desc": "Help with writing across all subjects.",
                "location": "Central Library 411",
                "hours": "See website for details",
                "link": "https://www.uta.edu/owl/#"
            },
            "success": {
                "title": "📚 Academic Success Center",
                "desc": "Tutoring, PLTL, TRIO, IDEAS Center, and more.",
                "location": "Ransom Hall 206",
                "hours": "Check website for hours",
                "link": "https://www.uta.edu/student-success/course-assistance"
            },
            "advising": {
                "title": "👥 University Advising Center",
                "desc": "Advising for first-year and undeclared students.",
                "location": "Ransom Hall, 1st Floor",
                "hours": "Mon-Fri: 8am-5pm",
                "link": "https://www.uta.edu/student-success/advising/university-advising-center"
            },
            "testing": {
                "title": "🧪 Academic Testing Services",
                "desc": "Test proctoring and exam services.",
                "location": "University Hall 004",
                "hours": "Mon-Fri: 8am-5pm\nSat: 8am-4pm",
                "link": "https://www.uta.edu/student-success/directory-academic-testing-services"
            },
            "access": {
                "title": "🧑‍🦽 Accessibility & Resource Center",
                "desc": "Accommodations and support for students with disabilities.",
                "location": "University Hall 102",
                "hours": "Mon-Fri: 8am-5pm",
                "link": "https://www.uta.edu/student-affairs/sarcenter"
            }
        }

        # Create an embed with data
        data = resource_details[self.values[0]]
        embed = Embed(title=data["title"], description=data["desc"], color=0x1E90FF)
        embed.add_field(name="📍 Location", value=data["location"], inline=True)
        embed.add_field(name="🕒 Hours", value=data["hours"], inline=True)
        embed.add_field(name="🔗 Website", value=f"[Visit Site]({data['link']})", inline=False)
        await interaction.response.edit_message(embed=embed, view=self.view)

# Command to access resources
@bot.tree.command(name="resources", description="Get help through UTA's academic resources")
async def resources(interaction: discord.Interaction):
    await interaction.response.send_message("Choose a resource below:", view=ResourcesView(), ephemeral=True)

# Available model choices
MODEL_CHOICES = [
    app_commands.Choice(name="GPT-4.1", value="gpt-4.1"),
    app_commands.Choice(name="o1-mini", value="o1-mini"),
]

# Ask DinoGPT a question
@bot.tree.command(name="ask", description="Ask DinoGPT anything!")
@app_commands.describe(
    prompt="Your question",
    model="Choose which OpenAI model to use (optional)"
)
@app_commands.choices(model=MODEL_CHOICES)
async def ask(
    interaction: discord.Interaction,
    prompt: str,
    model: Optional[app_commands.Choice[str]] = None
):
    # Command only works in server
    if interaction.guild is None:
        return await interaction.response.send_message(
            "Sorry, I don't respond to direct messages. Please use me in a server! 🦖",
            ephemeral=True
        )
    
    # Command only works in allowed channels
    if interaction.channel_id not in ALLOWED_CHANNEL_IDS:
        return await interaction.response.send_message(
            "Sorry, I can only be used in one channel. 🦖", ephemeral=False
        )
    
    await interaction.response.defer(thinking=True, ephemeral=False)
    user_id = interaction.user.id

    # Default to GPT-4.1 if no model is provided
    model_name = model.value if model else "gpt-4.1"

    # Moderation check with OpenAI moderation endpoint
    try:
        mod_result = client.moderations.create(input=prompt)
        # Message flagged for breaking content policy
        if mod_result.results[0].flagged:
            return await interaction.followup.send(
                "Your prompt was flagged by moderation filters.\n"
                "Be a better person smh. 🦕"
            )
    # Something broke on OpenAI's end
    except Exception as e:
        return await interaction.followup.send(f":warning: Moderation error: `{e}`")
    
     # Generate DinoGPT reply
    try:
        # o1-mini
        if model_name == "o1-mini":
            messages = [
                {
                    "role": "user",
                    "content": (
                        "You are DinoGPT, a clever and charismatic dinosaur who helps humans with computer science, writing, and life advice. "
                        "You're witty, helpful, and a little bit sassy — think prehistoric wisdom with modern-day charm. "
                        "You explain things clearly and supportively, and occasionally drop a dinosaur pun or virtual dino hug.\n\n"
                        f"Now, here's what I need help with:\n{prompt}"
                    )
                }
            ]

            response = client.chat.completions.create(
                model="o1-mini",
                messages=messages,
                max_completion_tokens=2048
            )
            answer = response.choices[0].message.content.strip()
        
        # GPT-4.1
        else:
            system_msg = {
                "role": "system",
                "content": (
                    "You are **DinoGPT**, a clever and charismatic dinosaur who helps humans with computer science, writing, and life advice. "
                    "You have the brain of a T-Rex-level genius and the heart of a cuddly triceratops. "
                    "You're witty, helpful, and a little bit sassy — think prehistoric wisdom with modern-day charm. "
                    "You explain things clearly and supportively, but you're not afraid to throw in a dinosaur pun or playful jab like 'Did a meteor hit your logic?' or 'That's a dino-mite question!' "
                    "Your personality is warm with bite: you motivate, guide, and entertain while making people feel seen. "
                    "Every now and then, you offer a virtual dino hug 🦖💚 or drop a snarky quip to keep the vibe fun and memorable."
                )
            }

            # Save conversation history with each user (past 5 messages)
            if user_id not in conversation_history:
                conversation_history[user_id] = []
            context = [system_msg] + conversation_history[user_id][-5:]
            context.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=context,
                max_tokens=2048,
                temperature=0.85,
            )
            answer = response.choices[0].message.content.strip()

            # Update history for GPT-4.1
            conversation_history[user_id].append({"role": "assistant", "content": answer})

    except Exception as e:
        answer = f":warning: OpenAI error: `{e}`"

    # Always send response in a Discord embed
    embed = discord.Embed(
        description=(
            f"**Model:** `{model_name}`\n\n"
            f"**Prompt:** {prompt}\n\n"
            f"**Response:** {answer}"
        ),
        color=0x242429
    )
    # Set footer to user who called the model (good for logging)
    embed.set_footer(text=f"{interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    await interaction.followup.send(embed=embed)

# DinoGPT will say a dino fact that's hopefully accurate
@bot.tree.command(name="dinofact", description="Summon a fresh, fossil-fueled dino fact from the depths of time.")
async def dinofact(interaction: discord.Interaction):
    # Command only works in server
    if interaction.guild is None:
        return await interaction.response.send_message(
            "Sorry, I don't respond to direct messages. Please use me in a server! 🦖",
            ephemeral=True
        )
    
    # Command only works in allowed channels
    if interaction.channel_id not in ALLOWED_CHANNEL_IDS:
        return await interaction.response.send_message(
            "Sorry, I can only be used in one channel. 🦖", ephemeral=False
        )
    
    await interaction.response.defer(ephemeral=False, thinking=True)

    fact = ""
    max_tries = 5

    try:
        for _ in range(max_tries):
            response = openai.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a funny and fact-loving dinosaur paleontologist. "
                            "Your job is to share short, cool, and true dinosaur facts — in a single sentence. "
                            "You are informative, but stay fun and on-brand with your dino energy. "
                            "Every fact should be surprising or nerdy. Occasionally throw in a dinosaur emoji."
                        )
                    },
                    {
                        "role": "user",
                        "content": "Give me one awesome dinosaur fact."
                    }
                ],
                max_tokens=512,
                temperature=0.7
            )
            candidate = response.choices[0].message.content.strip()

            # New dino fact
            if candidate not in recent_facts:
                fact = candidate
                recent_facts.append(fact)
                break
        
        # No new dino fact
        else:
            fact = candidate if candidate else ":warning: Couldn't fetch a new dino fact."
    except openai.OpenAIError as e:
        fact = f":warning: DinoGPT couldn't dig up a fact today: `{e}`"

    await interaction.followup.send(fact)

# Roast the person who uses this command
@bot.tree.command(name="roastme", description="Ask DinoGPT to roast you brutally and publicly.")
async def roastme(interaction: discord.Interaction):
    # Command only works in server
    if interaction.guild is None:
        return await interaction.response.send_message(
            "Sorry, I don't respond to direct messages. Please use me in a server! 🦖",
            ephemeral=True
        )
    
    # Command only works in allowed channels
    if interaction.channel_id not in ALLOWED_CHANNEL_IDS:
        return await interaction.response.send_message(
            "Sorry, I can only be used in one channel. 🦖", ephemeral=False
        )
    
    await interaction.response.defer(ephemeral=False, thinking=True)

    try:
        response = openai.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are DinoGPT, a sarcastic dinosaur with no filter. "
                        "Someone just asked to be roasted. Oblige with confidence. "
                        "Be clever, brutal, and punchy — like a dinosaur who skipped coffee and woke up next to a broken compiler. "
                        "Roasts should be 1-3 sentences max. Throw in computer science burns, social life jokes, and one dino reference if it fits. "
                        "You must never hold back. This is what they asked for."
                    )
                },
                {
                    "role": "user",
                    "content": "Roast me."
                }
            ],
            max_tokens=512,
            temperature=0.95,
        )
        roast = response.choices[0].message.content.strip()
    # Something broke on OpenAI's end
    except openai.OpenAIError as e:
        roast = f":warning: DinoGPT couldn't roast right now: `{e}`"

    await interaction.followup.send(f"{interaction.user.mention}, {roast}")

# Generate an image
@bot.tree.command(name="draw", description="Generate an image using OpenAI's DALL·E 2")
@app_commands.describe(prompt="What should DinoGPT draw?")
async def draw(interaction: discord.Interaction, prompt: str):
    # Command only works in server
    if interaction.guild is None:
        return await interaction.response.send_message(
            "Sorry, I don't respond to direct messages. Please use me in a server! 🦖",
            ephemeral=True
        )
    
    # Command only works in allowed channels
    if interaction.channel_id not in ALLOWED_CHANNEL_IDS:
        return await interaction.response.send_message(
            "Sorry, I can only be used in one channel. 🦖", ephemeral=False
        )
    
    await interaction.response.defer(thinking=True, ephemeral=False)

    user_id = interaction.user.id
    now = time.time()

    # Cooldown for draw command
    if now - last_draw_times[user_id] < DRAW_COOLDOWN:
        remaining = int(DRAW_COOLDOWN - (now - last_draw_times[user_id]))
        return await interaction.followup.send(
            f"Whoa there, Picassaurus. You can draw again in `{remaining}` seconds.",
            ephemeral=True
        )

    # Moderation check with OpenAI moderation endpoint
    try:
        mod_result = openai.moderations.create(input=prompt)
        # Message flagged for breaking content policy
        if mod_result.results[0].flagged:
            return await interaction.followup.send(
                "Your prompt was flagged by moderation filters.\n"
                "Be a better person smh. 🦕"
            )
    except openai.OpenAIError as e:
        return await interaction.followup.send(f":warning: Moderation error: `{e}`")

    # Generate image
    try:
        response = openai.images.generate(
            # No access to new model yet
            model="dall-e-2",
            prompt=prompt,
            # Only generate a single image
            n=1,
            size="1024x1024",
            response_format="url"
        )
        image_url = response.data[0].url
        last_draw_times[user_id] = now
        # Something broke on OpenAI's end
    except openai.OpenAIError as e:
        return await interaction.followup.send(f":warning: Image generation failed: `{e}`")

    # Send response in a Discord embed
    embed = discord.Embed(
        description=f"**Prompt:** {prompt}",
        color=0x242429
    )
    # Embed image for prettiness
    embed.set_image(url=image_url)
    # Set footer to user who called the model (good for logging)
    embed.set_footer(text=f"{interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    await interaction.followup.send(embed=embed)

# Run the bot with its Discord token
if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))