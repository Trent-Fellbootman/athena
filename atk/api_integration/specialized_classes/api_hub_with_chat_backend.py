from ..base import AAISAPIHub
from dataclasses import dataclass
from ...core import AAISThinkingLanguageContent
from ...prompting.prompt_lookup_table import AAISPromptLookupTable


class AAISAPIHubWithChatBackend(AAISAPIHub):
    """
    A specialized API hub that achieves its functionality
    intelligently with a chat backend (e.g., ChatGPT).
    """

    @dataclass
    class PromptLookupTable(AAISPromptLookupTable):
        """
        A table of prompts to use for performing
        API hub-related operations with the chat backend.

        Attributes:
            requestSummarizationPromptTemplate:
                This template is used to create a prompt which is then
                fed into the chat API to create a summarization of the request.
        """

        requestSummarizationPromptTemplate: AAISThinkingLanguageContent

    # override
    async def summarizeRequest(self, requestMessage: AAISThinkingLanguageContent) \
            -> AAISThinkingLanguageContent:
        pass
