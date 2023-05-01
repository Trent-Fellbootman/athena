from ..base import AAISAPIHub
import asyncio
from typing import Optional, Union, List, Tuple, Any, Dict
from dataclasses import dataclass
from ...core import AAISThinkingLanguageContent, AAISMessagePacket, AAISProcess


class AAISAPIHubWithChatBackend(AAISAPIHub):

    @dataclass
    class PromptTable:
        """
        A table of prompts to use for performing
        API hub-related operations with the chat backend.
        """

        # this field
        summarizationPrompt: AAISThinkingLanguageContent

    # override
    async def summarizeRequest(self, requestMessage: AAISThinkingLanguageContent) \
            -> AAISThinkingLanguageContent:
        pass
