import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OLLAMA_BASE_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
MODEL_NAME = os.getenv('OLLAMA_MODEL', 'deepseek-r1:1.5b')

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Fixed async generator function - without return statement
async def stream_ollama(prompt, model=MODEL_NAME):
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }
    
    full_response = ""
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_message = f"Error: {response.status} - {await response.text()}"
                full_response = error_message
                yield "", error_message, True
                return  # Proper way to exit an async generator
            
            async for line in response.content:
                if not line:
                    continue
                
                try:
                    decoded_line = line.decode('utf-8').strip()
                    if decoded_line:
                        data = json.loads(decoded_line)
                        if "response" in data:
                            chunk = data["response"]
                            full_response += chunk
                            yield chunk, full_response, data.get("done", False)
                except Exception as e:
                    print(f"Error processing stream: {str(e)}")
                    continue

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    # Verify Ollama is running
    try:
        models_url = f"{OLLAMA_BASE_URL}/api/tags"
        async with aiohttp.ClientSession() as session:
            async with session.get(models_url) as response:
                if response.status == 200:
                    models = await response.json()
                    print(f"Available Ollama models: {', '.join([model['name'] for model in models.get('models', [])])}")
                else:
                    print(f"Warning: Could not fetch Ollama models. Status: {response.status}")
    except Exception as e:
        print(f"Warning: Ollama might not be running. Error: {str(e)}")

@bot.command(name='ask')
async def ask(ctx, *, question):
    """Ask a question to the LLM through Ollama with streaming response"""
    try:
        # Create an initial response message
        response_message = await ctx.send("Thinking...")
        current_content = ""
        buffer = ""
        last_update_time = asyncio.get_event_loop().time()
        update_interval = 1.0  # Update message every 1 second
        
        async for chunk, full_response, done in stream_ollama(question):
            buffer += chunk
            current_time = asyncio.get_event_loop().time()
            
            # Update the message at regular intervals or when done
            if done or (current_time - last_update_time) >= update_interval:
                # Check if content has changed enough to justify an update
                if len(buffer) > 0:
                    current_content = full_response
                    
                    # Handle Discord's 2000 character limit
                    if len(current_content) <= 2000:
                        await response_message.edit(content=current_content)
                    else:
                        # If we exceed the limit, we need to split into multiple messages
                        if len(response_message.content) < 2000:
                            # Update the original message with the first 2000 chars
                            await response_message.edit(content=current_content[:1990] + "...")
                        
                        # Check if we need to send a new message for the overflow
                        if len(current_content) > len(response_message.content) + 1000:  # Only send a new message if significant new content
                            response_message = await ctx.send(current_content[-1990:])
                    
                    buffer = ""
                    last_update_time = current_time
                
                # If done, make sure we send any remaining content
                if done and buffer:
                    if len(current_content) <= 2000:
                        await response_message.edit(content=current_content)
                    else:
                        await ctx.send(current_content[-1990:])
                    break
    
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command(name='models')
async def list_models(ctx):
    """List available Ollama models"""
    async with ctx.typing():
        try:
            models_url = f"{OLLAMA_BASE_URL}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(models_url) as response:
                    if response.status == 200:
                        models_data = await response.json()
                        models = models_data.get('models', [])
                        if models:
                            model_names = [f"• {model['name']}" for model in models]
                            await ctx.send(f"Available models:\n{chr(10).join(model_names)}")
                        else:
                            await ctx.send("No models found in Ollama.")
                    else:
                        await ctx.send(f"Error fetching models: {response.status}")
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

@bot.command(name='using')
async def change_model(ctx, model_name):
    """Change the model being used"""
    global MODEL_NAME
    old_model = MODEL_NAME
    MODEL_NAME = model_name
    await ctx.send(f"Changed model from {old_model} to {MODEL_NAME}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"An error occurred: {str(error)}")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide a question. Usage: !ask <your question>")

# Run the bot
bot.run(TOKEN)
