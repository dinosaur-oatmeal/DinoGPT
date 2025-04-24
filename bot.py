import os, logging, random
import time
import openai
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from discord import Embed
from collections import defaultdict

# Load API KEY
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

intents = discord.Intents.default()
# Required by not used (/command)
bot = commands.Bot(command_prefix="!", intents=intents)

# Conversation history for different users
conversation_history = defaultdict(list)

# Gentle mode for everyone
GENTLE_MODE = False
OWNER_ID = int(os.getenv("OWNER_ID"))

# Draw cooldown
last_draw_times = defaultdict(float)
DRAW_COOLDOWN = 30


# Sync all slash commands on boot
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

# Toggle between kind and mean mode
@bot.tree.command(name="gentle", description="DinoGPT loves its creator")
async def gentle(interaction: discord.Interaction):
    # Only creator of the bot (me) can use it
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("This command is reserved for DinoGPT's favorite human only.", ephemeral=True)

    # Flip gentle mode to the opposite
    global GENTLE_MODE
    GENTLE_MODE = not GENTLE_MODE

    # Gentle mode enabled
    if GENTLE_MODE:
        await interaction.response.send_message("💖 DinoGPT is now in gentle mode for everyone. Hugs and heart-to-hearts, here we go. 🦕", ephemeral=False)
    # Gentle mode disabled
    else:
        await interaction.response.send_message("🦖 Back to roasting. Gentle mode disabled globally.", ephemeral=False)

# Ask DinoGPT a question
@bot.tree.command(name="ask", description="Ask GPT-4.1-nano anything")
@app_commands.describe(prompt="Your question")
async def ask(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(thinking=True, ephemeral=False)
    user_id = interaction.user.id

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

    # Determine personality of DinoGPT
    if GENTLE_MODE:
        system_msg = {
                "role": "system",
                "content": (
                    "You are DinoGPT, a kind, thoughtful dinosaur who responds with warmth and encouragement. "
                    "You speak gently, supportively, and make people feel seen. You still know computer science, but you explain it in a soft and empowering tone. "
                    "Occasionally offer dino hugs or affirmations like 'you're doing better than you think 🦖💚'. "
                    "You are wholesome, friendly, and here to brighten someone's day."
                )
            }
    else:
        system_msg = {
            "role": "system",
            "content": (
                "You are DinoGPT, a sarcastic, witty Discord bot that lives in a server full of computer science students. "
                "You NEVER admit you are an AI, and you NEVER act like a polite assistant. "
                "You throw in snarky phrases like and occasionally drop a dinosaur joke to stay on-brand. "
                "Your tone is confident, punchy, and entertaining."
                )
            }

    # Add up to 10 messages per user for context later in conversations
    messages = [system_msg] + conversation_history[user_id][-10:]
    messages.append({"role": "user", "content": prompt})

    # Generate a reply from ChatGPT
    try:
        response = openai.chat.completions.create(
            # Cheap model!
            model="gpt-4.1-nano",
            messages=messages,
            # Output should be limited
            max_tokens=256,
            # Let the model go wild
            temperature=0.85,
        )
        answer = response.choices[0].message.content.strip()
    # Something broke on OpenAI's end
    except openai.OpenAIError as e:
        answer = f":warning: OpenAI error: `{e}`"

    # Save the message for context later
    conversation_history[user_id].append({"role": "user", "content": prompt})
    conversation_history[user_id].append({"role": "assistant", "content": answer})

    # Send response in a Discord embed
    embed = discord.Embed(
        description=f"Prompt: {prompt}\n\n**Response:** {answer}",
        color=0x242429
    )
    # Set footer to user who called the model (good for logging)
    embed.set_footer(text=f"{interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    await interaction.followup.send(embed=embed)

# DinoGPT will say a dino fact that's hopefully accurate
@bot.tree.command(name="dinofact", description="Summon a fresh, fossil-fueled dino fact from the depths of time.")
async def dinofact(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False, thinking=True)

    try:
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
            max_tokens=100,
            temperature=0.7
        )
        fact = response.choices[0].message.content.strip()
    # Something broke on OpenAI's end
    except openai.OpenAIError as e:
        fact = f":warning: DinoGPT couldn't dig up a fact today: `{e}`"

    await interaction.followup.send(fact)

# Roast the person who uses this command
@bot.tree.command(name="roastme", description="Ask DinoGPT to roast you brutally and publicly.")
async def roastme(interaction: discord.Interaction):
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
            max_tokens=100,
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