import asyncio
import json
import os


_LOCK = asyncio.Lock()
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_DATA_FILE = os.path.join(_DATA_DIR, "channels.json")


def _default_data():
    return {"servers": {}}


def _ensure_data_file():
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(_DATA_FILE):
        with open(_DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(_default_data(), file, indent=2)


def _read_data():
    _ensure_data_file()
    try:
        with open(_DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return _default_data()


def _write_data(data):
    os.makedirs(_DATA_DIR, exist_ok=True)
    temp_path = f"{_DATA_FILE}.tmp"
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
    os.replace(temp_path, _DATA_FILE)


async def init_storage():
    async with _LOCK:
        await asyncio.to_thread(_ensure_data_file)


async def upsert_server_channel(server_id, channel_id, crypto_id, server_name, previous_price):
    async with _LOCK:
        data = await asyncio.to_thread(_read_data)
        servers = data.setdefault("servers", {})
        server_key = str(server_id)
        server_entry = servers.setdefault(server_key, {"name": server_name, "channels": {}})
        server_entry["name"] = server_name
        channels = server_entry.setdefault("channels", {})
        channels[str(channel_id)] = {
            "crypto_id": crypto_id,
            "previous_price": str(previous_price) if previous_price is not None else None,
        }
        await asyncio.to_thread(_write_data, data)


async def list_channels():
    async with _LOCK:
        data = await asyncio.to_thread(_read_data)
        channels = []
        for server_id, server_entry in data.get("servers", {}).items():
            server_name = server_entry.get("name")
            for channel_id, channel_entry in server_entry.get("channels", {}).items():
                channels.append({
                    "channel_id": int(channel_id),
                    "crypto_id": channel_entry.get("crypto_id"),
                    "previous_price": channel_entry.get("previous_price"),
                    "discord_id": int(server_id),
                    "name": server_name,
                })
        return channels


async def delete_channel(channel_id):
    async with _LOCK:
        data = await asyncio.to_thread(_read_data)
        removed = False
        channel_key = str(channel_id)
        for server_entry in data.get("servers", {}).values():
            channels = server_entry.get("channels", {})
            if channel_key in channels:
                del channels[channel_key]
                removed = True
                break
        if removed:
            await asyncio.to_thread(_write_data, data)
        return removed


async def update_previous_price(channel_id, new_price):
    async with _LOCK:
        data = await asyncio.to_thread(_read_data)
        updated = False
        channel_key = str(channel_id)
        for server_entry in data.get("servers", {}).values():
            channels = server_entry.get("channels", {})
            if channel_key in channels:
                channels[channel_key]["previous_price"] = (
                    str(new_price) if new_price is not None else None
                )
                updated = True
                break
        if updated:
            await asyncio.to_thread(_write_data, data)
        return updated
