# Self-hosted-LLM-based-Discord-Bot
# Setup Instructions

## 1. Prerequisites:
  * Python 3.8+ installed on your computer
  * A Discord account and admin access to a server

## 2. Create a Discord Bot:
  * Go to the Discord Developer Portal
  * Click "New Application" and give it a name
  * Go to the "Bot" tab and click "Add Bot"
  * Under "Privileged Gateway Intents", enable "Message Content Intent"
  * Copy your bot token (you'll need this later)

## 3. Install Dependencies:
```
pip install discord.py python-dotenv torch transformers accelerate bitsandbytes
```
## 4. Create a .env file in the same directory as your bot script with:
DISCORD_TOKEN=your_discord_bot_token_here
## 5. Invite the Bot to Your Server:

In the Developer Portal, go to "OAuth2" > "URL Generator"
Select scopes: "bot" and "applications.commands"
Select permissions: "Send Messages", "Read Message History", etc.
Copy the generated URL and open it in your browser to invite the bot

## 6. Run the Bot:
python bot_script.py

# Usage
Once the bot is running, you can interact with it in your Discord server:

Type !ask What is machine learning? to ask it a question
