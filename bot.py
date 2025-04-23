import os, asyncio, logging
import openai
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from discord import Embed

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

intents = discord.Intents.default()  # slash commands don’t need message intent
bot    = commands.Bot(command_prefix="!", intents=intents)  # prefix unused, but required

@bot.event
async def on_ready():
    # Sync slash commands the first time the bot starts
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

# /ask prompt:"What do you want to ask?"
@bot.tree.command(name="ask", description="Ask GPT-4.1-nano anything")
@app_commands.describe(prompt="Your question")
async def ask(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(thinking=True, ephemeral=False)

    # Run moderation
    try:
        mod_result = openai.moderations.create(input=prompt)
        if mod_result.results[0].flagged:
            return await interaction.followup.send(
                ":no_entry: Your prompt was flagged by moderation filters and wasn't sent to DinoGPT.\n"
                "Please keep it friendly and appropriate. 🦕"
            )
    except openai.OpenAIError as e:
        return await interaction.followup.send(
            f":warning: Could not run moderation check. Error: `{e}`"
        )

    # Call OpenAI
    try:
        response = openai.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.8,
        )
        answer = response.choices[0].message.content.strip()
    except openai.OpenAIError as e:
        answer = f":warning: OpenAI error: `{e}`"

    # Construct embed
    embed = discord.Embed(
        description=f"Prompt: {prompt}\n\n**Response:** {answer}",
        color=0x242429  # DinoGPT dark theme
    )
    embed.set_footer(text=f"{interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

    await interaction.followup.send(embed=embed)

# Draw an image with OpenAI's newest image gen model
@bot.tree.command(name="draw", description="Generate an image using OpenAI's Image-1 model")
@app_commands.describe(prompt="What should DinoGPT draw?")
async def draw(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(thinking=True, ephemeral=False)

    # Step 1: Run moderation
    try:
        mod_result = openai.moderations.create(input=prompt)
        if mod_result.results[0].flagged:
            return await interaction.followup.send(
                ":no_entry: Your prompt was flagged by moderation filters and wasn't sent to DinoGPT.\n"
                "Please keep it friendly and appropriate. 🦕"
            )
    except openai.OpenAIError as e:
        return await interaction.followup.send(
            f":warning: Could not run moderation check. Error: `{e}`"
        )

    # Step 2: Generate image
    try:
        response = openai.images.generate(
            model="dall-e-2",  # Image-1 via DALL·E 3
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="url"
        )
        image_url = response.data[0].url
    except openai.OpenAIError as e:
        return await interaction.followup.send(
            f":warning: Image generation failed: `{e}`"
        )

    # Step 3: Construct embed
    embed = discord.Embed(
        description=f"**Prompt:** {prompt}",
        color=0x242429
    )
    embed.set_image(url=image_url)
    embed.set_footer(text=f"{interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

    await interaction.followup.send(embed=embed)

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))