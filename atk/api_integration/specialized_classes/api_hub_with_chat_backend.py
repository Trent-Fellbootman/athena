from dataclasses import dataclass
from typing import TypeVar

from ..base import AAISAPIHub, AAISAPIServer
from ...core import AAISThinkingLanguageContent, AAISProcess, AAISMessagePacket
from ...functional import AAISFunctional


T = TypeVar('T', bound=AAISThinkingLanguageContent)


class AAISAPIHubWithFunctionalBackend(AAISAPIHub):
    """
    A specialized API hub that achieves its functionality
    intelligently with a set of functionals.
    """

    @dataclass
    class FunctionalTable:
        """
        A table of functionals to use for performing
        API hub-related operations with the chat backend.

        Attributes:
            summarizer: The summarizer to use for summarizing requests.
        """

        summarizer: AAISFunctional[T, T]
        messageTypeDeterminer: AAISFunctional[AAISMessagePacket, AAISAPIServer.APIServerMessageType]

    # override
    async def determineMessageType(self, message: AAISMessagePacket) -> AAISAPIServer.APIServerMessageType:
        pass

    # override
    async def selectHandler(self, request: AAISThinkingLanguageContent) -> AAISAPIHub.ServerHandlerMatchResult:
        pass

    # override
    async def matchReturnMessageWithAPICallRecord(
            self, returnMessage: AAISMessagePacket) -> AAISAPIHub.ReturnMessageEntryMatchResult:
        pass

    # override
    async def formatErrorMessage(
            self, errorType: AAISAPIHub.ErrorType, errorMessage: AAISThinkingLanguageContent)\
            -> AAISThinkingLanguageContent:
        pass

    # override
    async def formatRequestForChildServer(
            self, request: AAISThinkingLanguageContent, childServerEntry: AAISProcess.ReferenceTable.Entry)\
            -> AAISThinkingLanguageContent:
        pass

    # override
    async def formatReturnMessageForParent(
            self, returnMessage: AAISThinkingLanguageContent, context: AAISAPIServer.APICallTable.Entry)\
            -> AAISThinkingLanguageContent:
        pass

    # override
    async def determineAPICallReturnResultType(
            self, returnMessage: AAISThinkingLanguageContent, context: AAISAPIServer.APICallTable.Entry)\
            -> AAISAPIHub.APICallReturnResultType:
        pass

    # override
    async def summarizeRequest(self, requestMessage: AAISThinkingLanguageContent) \
            -> AAISThinkingLanguageContent:
        pass
