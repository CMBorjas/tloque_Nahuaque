"""
Discord ↔ Tloque Nahuaque orchestrator bridge.

Forwards allowed messages to ORCHESTRATOR_API_URL /api/chat (same contract as the web UI).

Environment:
  DISCORD_BOT_TOKEN            — required; Discord bot token
  ORCHESTRATOR_API_URL        — optional; default http://127.0.0.1:8000
  DISCORD_ALLOWED_USER_IDS    — optional; comma-separated numeric user IDs
  DISCORD_ALLOWED_CHANNEL_IDS — optional; comma-separated numeric channel IDs (guild)

At least one of DISCORD_ALLOWED_USER_IDS or DISCORD_ALLOWED_CHANNEL_IDS must be set.

Guild channels: the user must @mention the bot in the message.
Direct messages: only if DISCORD_ALLOWED_USER_IDS is set (at least one user allowed).

Run (with the API already listening):
  python -m orchestrator.discord_bot

Environment variables may be placed in a ``.env`` file at the project root (same folder as
``orchestrator/``); ``python-dotenv`` loads it on startup.

Developer Portal: enable the Message Content Intent for the bot if you use message text.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional, Set

import discord
import requests
from dotenv import load_dotenv


def _parse_id_set(raw: Optional[str]) -> Optional[Set[int]]:
    if not raw or not str(raw).strip():
        return None
    out: Set[int] = set()
    for part in str(raw).split(","):
        part = part.strip()
        if part:
            out.add(int(part))
    return out if out else None


def _chunk_text(text: str, limit: int = 1900) -> List[str]:
    if len(text) <= limit:
        return [text]
    return [text[i : i + limit] for i in range(0, len(text), limit)]


async def _call_chat_api(base_url: str, message: str) -> str:
    url = f"{base_url.rstrip('/')}/api/chat"

    def _post() -> str:
        r = requests.post(url, json={"message": message}, timeout=120)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "success":
            return f"API error: {data}"
        return str(data.get("agent_reply", "(no reply)"))

    return await asyncio.to_thread(_post)


def _strip_bot_mention(content: str, bot_user: discord.ClientUser) -> str:
    mention = bot_user.mention.replace("@", "@!")
    variants = (
        bot_user.mention,
        mention,
        f"<@{bot_user.id}>",
        f"<@!{bot_user.id}>",
    )
    s = content
    for v in variants:
        s = s.replace(v, "")
    return s.strip()


def main() -> None:
    # Repo-root .env, then cwd .env (later does not override existing vars by default)
    _repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(_repo_root / ".env")
    load_dotenv()

    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("Set DISCORD_BOT_TOKEN in the environment.", file=sys.stderr)
        sys.exit(1)

    base_url = os.environ.get("ORCHESTRATOR_API_URL", "http://127.0.0.1:8900")
    allowed_users = _parse_id_set(os.environ.get("DISCORD_ALLOWED_USER_IDS"))
    allowed_channels = _parse_id_set(os.environ.get("DISCORD_ALLOWED_CHANNEL_IDS"))

    if allowed_users is None and allowed_channels is None:
        print(
            "Set DISCORD_ALLOWED_USER_IDS and/or DISCORD_ALLOWED_CHANNEL_IDS "
            "(comma-separated Discord snowflake IDs).",
            file=sys.stderr,
        )
        sys.exit(1)

    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        assert client.user is not None
        print(f"Discord bridge online as {client.user} (API: {base_url})")

    @client.event
    async def on_message(message: discord.Message) -> None:
        if message.author.bot:
            return

        if allowed_users is not None and message.author.id not in allowed_users:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)

        if is_dm:
            if allowed_users is None:
                # Channel-only allowlist: do not accept DMs from arbitrary users
                return
        else:
            if not isinstance(message.channel, discord.abc.Messageable):
                return
            if allowed_channels is not None and message.channel.id not in allowed_channels:
                return
            assert client.user is not None
            if client.user not in message.mentions:
                return

        assert client.user is not None
        text = message.content if is_dm else _strip_bot_mention(message.content, client.user)
        if not text:
            return

        async with message.channel.typing():
            try:
                reply = await _call_chat_api(base_url, text)
            except requests.HTTPError as e:
                body = ""
                if e.response is not None:
                    try:
                        body = e.response.text[:500]
                    except Exception:
                        body = ""
                reply = f"HTTP {e.response.status_code if e.response else '?'}: {e} {body}".strip()
            except Exception as e:
                reply = f"Request failed: {e}"

        chunks = _chunk_text(reply)
        first, rest = chunks[0], chunks[1:]
        await message.reply(first, mention_author=False)
        for part in rest:
            await message.channel.send(part)

    client.run(token)


if __name__ == "__main__":
    main()
