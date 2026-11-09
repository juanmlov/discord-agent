# Discord LLM bot

A Python Discord bot that replies when mentioned and uses OpenRouter's
OpenAI-compatible API for its language model. Conversations are kept separately
for each user in each channel, in memory, and are lost when the bot restarts.

## 1. Configure the Discord app

In the [Discord Developer Portal](https://discord.com/developers/applications):

1. Open your application, select **Bot**, and add a bot user if you have not
   already.
2. Under **Bot**, enable **Message Content Intent**. The bot needs this to read
   messages that mention it.
3. Copy or reset the bot token. Keep it private.
4. Under **OAuth2 > URL Generator**, select the `bot` scope and the
   **View Channels**, **Send Messages**, and **Read Message History**
   permissions. Use the generated URL to invite the bot to your server.

## 2. Get an OpenRouter API key

Create an API key at [OpenRouter](https://openrouter.ai/). Free models are
available, but their availability, limits, and performance can change. The
default model below is an example of a currently listed free model; you can
change it with `OPENROUTER_MODEL`.

## 3. Install and configure

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `DISCORD_TOKEN` and `OPENROUTER_API_KEY`. Keep `.env` private
and never commit it.

Free models can be temporarily rate-limited by their shared provider. If that
happens, try again shortly or change `OPENROUTER_MODEL` in `.env` to another
available free model from OpenRouter. Adding your own provider key in OpenRouter
can also provide separate provider limits.

## 4. Run

```bash
python bot.py
```

Mention the bot in a server channel to chat. The bot keeps a short, in-memory
conversation history per user and channel. It does not respond to messages that
do not mention it. Its personality is an original, warm, comedic assistant
with broad knowledge of soulful pop/rock, blues guitar, and songwriting. It uses
occasional good-natured music jokes without impersonating a real musician.
