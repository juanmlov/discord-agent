import logging
import os
from collections import OrderedDict

import discord
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError, RateLimitError


load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
MAX_HISTORY_MESSAGES = 20
MAX_CONVERSATIONS = 500
DISCORD_MESSAGE_LIMIT = 2000

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it to your .env file.")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is missing. Add it to your .env file.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord_llm_bot")

headers = {"X-Title": os.getenv("OPENROUTER_APP_NAME", "Discord LLM Bot")}
if site_url := os.getenv("OPENROUTER_SITE_URL"):
    headers["HTTP-Referer"] = site_url

llm = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers=headers,
)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

conversations: OrderedDict[tuple[int, int, int], list[dict[str, str]]] = OrderedDict()


def split_message(content: str) -> list[str]:
    chunks = []
    while len(content) > DISCORD_MESSAGE_LIMIT:
        split_at = content.rfind("\n", 0, DISCORD_MESSAGE_LIMIT + 1)
        if split_at <= 0:
            split_at = content.rfind(" ", 0, DISCORD_MESSAGE_LIMIT + 1)
        if split_at <= 0:
            split_at = DISCORD_MESSAGE_LIMIT
        chunks.append(content[:split_at].rstrip())
        content = content[split_at:].lstrip()
    if content:
        chunks.append(content)
    return chunks


@bot.event
async def on_ready() -> None:
    logger.info("Logged in as %s", bot.user)


@bot.event
async def on_message(message: discord.Message) -> None:
    if bot.user is None or message.author == bot.user:
        return
    if bot.user not in message.mentions:
        return

    prompt = message.content
    prompt = prompt.replace(f"<@{bot.user.id}>", "").replace(
        f"<@!{bot.user.id}>", ""
    ).strip()
    if not prompt:
        await message.reply(
            "What would you like to chat about?",
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return

    guild_id = message.guild.id if message.guild else 0
    conversation_id = (guild_id, message.channel.id, message.author.id)
    history = conversations.setdefault(conversation_id, [])
    conversations.move_to_end(conversation_id)
    if len(conversations) > MAX_CONVERSATIONS:
        conversations.popitem(last=False)

    try:
        async with message.channel.typing():
            response = await llm.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Reply as if you were the famous guitar player John Mayer.",
                    },
                    *history,
                    {"role": "user", "content": prompt},
                ],
            )
    except RateLimitError:
        logger.warning("OpenRouter rate limit reached for model %s", MODEL)
        await message.reply(
            "The free model is busy right now because its shared provider is "
            "rate-limited. Please try again shortly. If this keeps happening, "
            "set OPENROUTER_MODEL in your .env to another available free model, "
            "or add your own provider key in OpenRouter.",
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return
    except OpenAIError:
        logger.exception("OpenRouter request failed")
        await message.reply(
            "I couldn't reach the language model just now. Please try again later.",
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return

    answer = response.choices[0].message.content
    if not answer or not answer.strip():
        logger.warning("OpenRouter returned an empty response")
        await message.reply(
            "I couldn't come up with a response that time. Please try again.",
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return

    history.extend(
        [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": answer},
        ]
    )
    del history[:-MAX_HISTORY_MESSAGES]

    for index, chunk in enumerate(split_message(answer)):
        if index == 0:
            await message.reply(
                chunk,
                mention_author=False,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        else:
            await message.channel.send(
                chunk, allowed_mentions=discord.AllowedMentions.none()
            )


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
