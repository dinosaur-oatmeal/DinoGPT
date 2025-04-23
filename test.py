import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")  # or paste it directly

try:
    response = openai.images.generate(
        model="dall-e-3",
        prompt="A cartoon dinosaur reading a book",
        n=1,
        size="1024x1024",
        response_format="url"
    )
    print("✅ You have access to DALL·E 3 / Image-1!")
    print("Image URL:", response.data[0].url)
except openai.OpenAIError as e:
    print("❌ You do NOT have access.")
    print(f"Error: {e}")
