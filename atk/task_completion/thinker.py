from ..core.core import (
    AAISProcess, AAISMessageHeader, AAISMessagePacket,
    AAISThinkingLanguageContent, AAISReferenceTableEntry
)

import asyncio
from typing import List, Dict, Any, Optional, Iterable, Self
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


@dataclass
class AAISMessageSendingOperationResult:
    messagePacket: AAISMessagePacket
    successfulRecipients: Iterable[AAISReferenceTableEntry]
    failedRecipients: Iterable[AAISReferenceTableEntry]


@dataclass
class AAISMessageSendingOperation:
    messagePacket: AAISMessagePacket
    targetProcessEntries: Iterable[AAISReferenceTableEntry]

    async def performOperation(self) -> AAISMessageSendingOperationResult:
        # TODO: is it possible to fail?
        await asyncio.gather(
            *[self.messagePacket.send(target.referee)
              for target in self.targetProcessEntries])

        return AAISMessageSendingOperationResult(
            messagePacket=self.messagePacket,
            successfulRecipients=self.targetProcessEntries,
            failedRecipients=[]
        )


@dataclass
class AAISThoughtExecutionResult:
    messageSendingOperationResults: Iterable[AAISMessageSendingOperationResult]


class AAISMessageBuffer:
    def __init__(self):
        self._buffer = []

    def addMessage(self, message: AAISMessagePacket):
        self._buffer.append(message)

    def popAllMessages(self):
        messages = self._buffer
        self._buffer = []
        return messages


class AAISThinkerProcess(AAISProcess, ABC):

    def __init__(self):
        super().__init__()

        # the buffer for messages received from other processes.
        # there should be only two places to access this buffer:
        # when a message is received, it is added to the message buffer; and
        # when a thinking step completes, all messages in the buffer are
        # processed, and the buffer is cleared.
        self._messageBuffer = AAISMessageBuffer()
        # a future used to mark whether new messages have been added
        self._newMessageMarker = asyncio.Future()

    # override
    async def handleMessage(self, message: AAISMessagePacket):
        # simply add the message to the buffer for later processing
        self._messageBuffer.addMessage(message)

        if not self._newMessageMarker.done():
            # mark that new message have been added
            self._newMessageMarker.set_result(None)

    async def runMainLoop(self):
        while True:
            step_result = await self.step()

            if step_result.terminate:
                break

            if step_result.wait:
                # wait until a new message is received
                await self._newMessageMarker

    @dataclass
    class ThoughtInterpretationResult:
        class ResultType(Enum):
            SUCCESS = 0
            FAILURE = 1

        @dataclass
        class InterpretedThoughts:
            # what messages the thinker process wishes to send, and to whom
            messageSendingOperations: Iterable[AAISMessageSendingOperation]

            # whether the thinker process wishes to wait until receiving
            # a message before continuing to think
            waitForMessage: bool

            # whether the thinker process wishes to terminate itself
            terminate: bool

        resultType: ResultType
        interpretedThoughts: Optional[InterpretedThoughts]
        errorMessage: Optional[AAISThinkingLanguageContent]

    @abstractmethod
    async def handleThoughtInterpretationError(self, errorMessage: AAISThinkingLanguageContent):
        """
        Handles the error that occurred during thought interpretation.
        For thinkers with LLM backends, this usually means
        formatting the error message into a report and adding the report
        to the message history.

        The `think` method will be re-invoked after this method returns.
        """
        pass

    @abstractmethod
    async def handleThoughtExecutionResult(self, result: AAISThoughtExecutionResult):
        """
        Handles the result of thought execution.
        For thinkers with LLM backends, this usually means
        formatting the result into a report and adding the report
        to the message history.

        The `think` method will be re-invoked after this method returns
        (assuming that the process does not intend to wait or to terminate).
        """
        pass

    @staticmethod
    async def executeInterpretedThoughts(
            interpretedThoughts: ThoughtInterpretationResult.InterpretedThoughts) \
            -> AAISThoughtExecutionResult:

        operationResults = await asyncio.gather(
            *[operation.performOperation()
              for operation in interpretedThoughts.messageSendingOperations])

        return AAISThoughtExecutionResult(
            messageSendingOperationResults=operationResults
        )

    @abstractmethod
    async def handleThoughts(self, thoughts: AAISThinkingLanguageContent):
        """
        Handles the thoughts produced in one thinking step.

        For thinkers with LLM backends, this usually means
        adding the thoughts to the message history.
        """
        pass

    @dataclass
    class StepResult:
        wait: bool
        terminate: bool

    async def step(self) -> StepResult:
        """
        Processes unhandled messages, performs one thinking step
        and executes the produced thoughts.
        """

        # first process the unhandled messages
        unhandled_messages = self._messageBuffer.popAllMessages()
        # reset the message receipt marker future so that it can be awaited
        self._newMessageMarker = asyncio.Future()

        await self.processMessages(unhandled_messages)

        # then think
        thoughts = await self.think()
        # handle the produced thoughts
        await self.handleThoughts(thoughts)
        # interpret the thoughts
        thought_interpretation_result = await self.interpretThoughts(thoughts)

        # handle the thought interpretation result
        if thought_interpretation_result.resultType == \
                AAISThinkerProcess.ThoughtInterpretationResult.ResultType.SUCCESS:
            assert thought_interpretation_result.interpretedThoughts is not None

            # execute the thoughts
            thought_execution_result = await self.executeInterpretedThoughts(
                interpretedThoughts=thought_interpretation_result.interpretedThoughts)

            # handle the thought execution result
            await self.handleThoughtExecutionResult(thought_execution_result)

            # return for the next step
            return AAISThinkerProcess.StepResult(
                wait=thought_interpretation_result.interpretedThoughts.waitForMessage,
                terminate=thought_interpretation_result.interpretedThoughts.terminate
            )

        elif thought_interpretation_result.resultType == \
                AAISThinkerProcess.ThoughtInterpretationResult.ResultType.FAILURE:
            assert thought_interpretation_result.errorMessage is not None

            # handle the thought interpretation error
            await self.handleThoughtInterpretationError(
                thought_interpretation_result.errorMessage
            )

            # return for the next step
            return AAISThinkerProcess.StepResult(wait=False, terminate=False)
        else:
            # TODO: In case of an unknown result type, what should we do?
            return AAISThinkerProcess.StepResult(wait=False, terminate=False)

    @abstractmethod
    async def processMessages(self, messages: Iterable[AAISMessagePacket]):
        """
        Processes unhandled messages retrieved from the message buffer,
        after completing one thinking step.

        If there is a message history object associated with this thinker process,
        it should be updated here.
        """
        pass

    @abstractmethod
    async def think(self) -> AAISThinkingLanguageContent:
        """
        Performs one thinking step and produce thoughts.
        For thinking processes with LLM backends, this usually means
        prompting the LLM and retrieving the response.

        Note that this method does not involve processing the unhandled messages,
        or adding the thoughts to the message history; these are handled by
        other methods.
        """
        pass

    @abstractmethod
    async def interpretThoughts(self, thoughts: AAISThinkingLanguageContent) \
            -> ThoughtInterpretationResult:
        """
        Interprets the thoughts produced in one thinking step.
        """
        pass
