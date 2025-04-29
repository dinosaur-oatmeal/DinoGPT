# 🦖 DinoGPT - A Discord Bot for College Communities

Welcome to **DinoGPT**, the ultimate Discord companion for your college server!  
Built for [ACM @ UTA](https://www.acmuta.com/) and deployed on **Heroku** for 24/7 uptime, DinoGPT brings humor, helpfulness, and a healthy dose of dinosaur energy to over 1400 students.

---

## 📚 Commands Overview

| Command       | Description                               |
| :------------ | :---------------------------------------- |
| `/ask`        | Ask DinoGPT a question.                   |
| `/gentle`     | Toggle between gentle and sarcastic mode. |
| `/resources`  | Access UTA academic resources.            |
| `/dinofact`   | Get a cool dinosaur fact.                 |
| `/roastme`    | Get roasted by a sarcastic dino.           |
| `/draw`       | Generate an image with DALL·E 2.          |

---

## 🚀 Deployment

DinoGPT is designed for **24/7 deployment on Heroku**.  
It uses:
- Python 3.11+
- Discord.py (`discord` package)
- OpenAI API (`openai` package)
- Environment variables via `python-dotenv`

---

## 🔧 Setup

1. **Clone this repo:**

   ```bash
   git clone https://github.com/dinosaur-oatmeal/dinogpt.git
   cd dinogpt
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file:**

   ```env
   DISCORD_TOKEN=your_discord_bot_token
   OPENAI_API_KEY=your_openai_api_key
   OWNER_ID=your_discord_user_id
   ```

4. **Run locally:**

   ```bash
   python bot.py
   ```

---

## 🛡️ Permissions Required

When inviting DinoGPT to a server, ensure it has:
- Read Messages
- Send Messages
- Embed Links
- Use Slash Commands
- Manage Messages (optional but helps with future cleanup features)

---

## 🧠 Technologies

- [Discord.py](https://discordpy.readthedocs.io/)
- [OpenAI API](https://platform.openai.com/)
- [Heroku](https://heroku.com/) (Deployment)
