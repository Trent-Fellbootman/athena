from typing import Iterable, TypeVar, Generic, List, Collection
from dataclasses import dataclass

from ..base.thinker import AAISThinkerProcess, AAISThoughtExecutionResult
from ...core import AAISThinkingLanguageContent, AAISMessagePacket
from ...backend_abstractions import AAISChatAPI
from ...functional import AAISFunctional


T = TypeVar('T', bound=AAISThinkingLanguageContent)


class AAISThinkerWithChatBackend(AAISThinkerProcess, Generic[T]):

    @dataclass
    class FunctionalEngine:
        thoughtInterpretationErrorFormatter: AAISFunctional[T, T]
        thoughtExecutionResultFormatter: AAISFunctional[AAISThoughtExecutionResult, T]
        unhandledMessagesFormatter: AAISFunctional[Collection[AAISMessagePacket], T]

        @dataclass
        class ThoughtInterpreter:
            waitDeterminer: AAISFunctional[T, bool]
            messageSendingOperationsExtractor

    def __init__(self, backend: AAISChatAPI[T, T], functionalEngine: FunctionalEngine):
        super().__init__()

        assert isinstance(backend, AAISChatAPI)

        self._backend = backend

        self._functionalEngine = functionalEngine

        # initialize message history
        self._messageHistory: List[AAISChatAPI.Message] = []

    # override
    async def handleThoughtInterpretationError(self, errorMessage: T):
        self._messageHistory.append(AAISChatAPI.Message(
            senderType=AAISChatAPI.Message.SenderType.PROMPTER,
            content=await self._functionalEngine.thoughtInterpretationErrorFormatter.call(errorMessage)
        ))

    # override
    async def handleThoughtExecutionResult(self, result: AAISThoughtExecutionResult):
        self._messageHistory.append(AAISChatAPI.Message(
            senderType=AAISChatAPI.Message.SenderType.PROMPTER,
            content=await self._functionalEngine.thoughtExecutionResultFormatter.call(result)
        ))

    # override
    async def handleThoughts(self, thoughts: T):
        self._messageHistory.append(
            AAISChatAPI.Message(
                senderType=AAISChatAPI.Message.SenderType.AI,
                content=thoughts))

    # override
    async def processMessages(self, messages: Iterable[AAISMessagePacket]):
        self._messageHistory.append(
            AAISChatAPI.Message(
                senderType=AAISChatAPI.Message.SenderType.PROMPTER,
                content=await self._functionalEngine.unhandledMessagesFormatter.call(messages)))

    # override
    async def think(self) -> T:
        return await self._backend.generateResponse(messages=self._messageHistory)

    # override
    async def interpretThoughts(self, thoughts: T) -> AAISThinkerProcess.ThoughtInterpretationResult:
        pass
