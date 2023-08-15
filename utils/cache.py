import discord
from typing import Dict, Optional, Union


class MessageCache:
    def __init__(self) -> None:
        self._cache: Dict[str, discord.Message] = {}

    def get_message(self, key: str) -> Optional[discord.Message]:
        return self._cache.get(key)

    def query_message_id(self, message_id: int) -> Optional[discord.Message]:
        # First lookup
        if f"message-{message_id}" in self._cache:
            return self._cache[f"message-{message_id}"]

        for message in self._cache.values():
            if message.id == message_id:
                return message
        return None

    def add_message(self, message: discord.Message, custom_key: Optional[str]) -> None:
        if custom_key is not None and custom_key.startswith("message-"):
            raise KeyError("'message-' prefix is not allowed as custom key")
        self._cache[custom_key or f"message-{message.id}"] = message

    def remove_message(self, key: Union[str, int]) -> Optional[discord.Message]:
        if isinstance(key, int):
            if f"message-{key}" in self._cache:
                return self._cache.pop(f"message-{key}")

            key_del = None
            for name, message in self._cache.items():
                if message.id == key:
                    key_del = name
                    break
            if key_del is not None:
                return self._cache.pop(key_del)
        else:
            if key in self._cache:
                return self._cache.pop(key)
        
        return None

    def clear(self) -> None:
        self._cache.clear()