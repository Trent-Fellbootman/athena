from ..base import AAISAPIHub
from dataclasses import dataclass
from ...core import AAISThinkingLanguageContent


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
