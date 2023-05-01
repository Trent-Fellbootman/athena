import asyncio
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from api_server import AAISAPIServer
from atk.core import (
    AAISMessagePacket, AAISThinkingLanguageContent, AAISProcess
)

from collections import deque


class AAISAPIHub(ABC, AAISAPIServer):
    class ErrorType(Enum):
        FAILED_TO_FIND_HANDLER = 0
        EXECUTION_ERROR = 1

    def __init__(self):
        super().__init__()

        # TODO: rename this field so that the name reflects its purpose
        self._requestQueue = deque()

    # override
    async def handleMessage(self, message: AAISMessagePacket):
        """
        Handles a message.
        """

        self._requestQueue.append(asyncio.create_task(self.processMessage(message)))

    async def processMessage(self, receivedMessage: AAISMessagePacket):
        match self.determineMessageType(receivedMessage):
            case AAISAPIServer.APIServerMessageType.request:
                # 1. Update the API call table

                # make new ID and create entry
                new_api_call_entry: AAISAPIServer.APICallTable.Entry = self.apiCallTable.createEntry()
                # set the fields of the entry
                new_api_call_entry.summary = await self.summarizeRequest(receivedMessage.content)
                new_api_call_entry.sender = receivedMessage.header.sender
                new_api_call_entry.status = AAISAPIServer.APICallTable.Entry.APICallStatus.UNHANDLED

                # 2. Forward the request to the correct child API server

                # find the child API server to call
                handler_match_result = await self.selectHandler(receivedMessage.content)

                match handler_match_result.resultType:
                    case AAISAPIHub.APIHubServerHandlerMatchResult.ResultType.SUCCESS:
                        assert handler_match_result.handlerEntry is not None

                        # send the request to the child API server
                        dispatch_message = await self.formatRequestForChildServer(
                            receivedMessage.content, handler_match_result.handlerEntry)

                        dispatch_message_header = AAISMessagePacket.Header(
                            messageType=AAISMessagePacket.Header.MessageType.communication,
                            sender=self)

                        dispatch_packet = AAISMessagePacket(
                            header=dispatch_message_header,
                            content=dispatch_message)

                        # send the packet to the child API server
                        await dispatch_packet.send(handler_match_result.handlerEntry.referee)

                        new_api_call_entry.status = AAISAPIServer.APICallTable.Entry.APICallStatus.RUNNING

                    case AAISAPIHub.APIHubServerHandlerMatchResult.ResultType.FAILURE:
                        # failed to find handler
                        assert handler_match_result.errorMessage is not None

                        # write the error message
                        error_message = await self.formatErrorMessage(
                            errorType=AAISAPIHub.ErrorType.FAILED_TO_FIND_HANDLER,
                            errorMessage=handler_match_result.errorMessage)

                        # make the return packet
                        return_message_header = AAISMessagePacket.Header(
                            messageType=AAISMessagePacket.Header.MessageType.communication,
                            sender=self)

                        return_packet = AAISMessagePacket(
                            header=return_message_header,
                            content=error_message)

                        # send the return message to the parent
                        await return_packet.send(receivedMessage.header.sender)

                        new_api_call_entry.status = AAISAPIServer.APICallTable.Entry.APICallStatus.FAILURE

            case AAISAPIServer.APIServerMessageType.returnMessage:
                # 1. Find the corresponding record in the API call table
                record_match_result = await self.matchReturnMessageWithAPICallRecord(receivedMessage)

                match record_match_result.resultType:
                    case AAISAPIHub.APIHubReturnMessageEntryMatchResult.ResultType.SUCCESS:
                        # successfully found the record
                        # TODO: Add error handling for these. Mismatch is always possible.
                        assert record_match_result.record is not None
                        assert record_match_result.record.status == \
                               AAISAPIServer.APICallTable.Entry.APICallStatus.RUNNING

                        # update the status of the record
                        match await self.determineAPICallReturnResultType(
                                receivedMessage.content, record_match_result.record):
                            case AAISAPIHub.APICallReturnResultType.SUCCESS:
                                record_match_result.record.status = \
                                    AAISAPIServer.APICallTable.Entry.APICallStatus.SUCCESS
                            case AAISAPIHub.APICallReturnResultType.FAILURE:
                                record_match_result.record.status = \
                                    AAISAPIServer.APICallTable.Entry.APICallStatus.FAILURE

                        # send the return message to the parent
                        parent_return_message = await self.formatReturnMessageForParent(
                            returnMessage=receivedMessage.content,
                            context=record_match_result.record)

                        parent_return_header = AAISMessagePacket.Header(
                            messageType=AAISMessagePacket.Header.MessageType.communication,
                            sender=self)

                        parent_return_packet = AAISMessagePacket(
                            header=parent_return_header,
                            content=parent_return_message)

                        await parent_return_packet.send(record_match_result.record.sender)

                        # TODO: should we remove the record from the API call table?

                    case AAISAPIHub.APIHubReturnMessageEntryMatchResult.ResultType.FAILURE:
                        # Failed to find record matching the return message
                        # TODO: what should we do here?
                        assert record_match_result.errorMessage is not None
                        pass

                pass

    @abstractmethod
    async def summarizeRequest(self, requestMessage: AAISThinkingLanguageContent) \
            -> AAISThinkingLanguageContent:
        """
        Summarizes a request.

        This method is used to create a summary of an API call request
        which will be used to set the `summary` field of the record in
        the API call record table.
        """

        pass

    @abstractmethod
    async def determineMessageType(self, message: AAISMessagePacket) \
            -> AAISAPIServer.APIServerMessageType:
        """
        Determines the type of `message`.
        """

        pass

    @dataclass
    class APIHubServerHandlerMatchResult:

        class ResultType(Enum):
            SUCCESS = 0
            FAILURE = 1

        resultType: ResultType
        handlerEntry: AAISProcess.ReferenceTable.Entry | None
        errorMessage: AAISThinkingLanguageContent | None

    @dataclass
    class APIHubReturnMessageEntryMatchResult:

        class ResultType(Enum):
            SUCCESS = 0
            FAILURE = 1

        resultType: ResultType
        record: AAISAPIServer.APICallTable.Entry | None
        errorMessage: AAISThinkingLanguageContent | None

    @abstractmethod
    async def selectHandler(self, request: AAISThinkingLanguageContent) \
            -> APIHubServerHandlerMatchResult:
        """
        Determines the correct child API server to call for `request`.
        """

        pass

    @abstractmethod
    async def matchReturnMessageWithAPICallRecord(
            self, returnMessage: AAISMessagePacket) \
            -> APIHubReturnMessageEntryMatchResult:
        """
        Matches a return message with an API call record.
        """

        pass

    @abstractmethod
    async def formatErrorMessage(self, errorType: ErrorType, errorMessage: AAISThinkingLanguageContent) \
            -> AAISThinkingLanguageContent:
        """
        Formats an error message.

        Value returned by this method is used as the content
        of the message returned to the parent.
        """

        pass

    @abstractmethod
    async def formatRequestForChildServer(
            self, request: AAISThinkingLanguageContent,
            childServerEntry: AAISProcess.ReferenceTable.Entry) \
            -> AAISThinkingLanguageContent:
        """
        Formats a request for the child server.
        """

        pass

    @abstractmethod
    async def formatReturnMessageForParent(
            self, returnMessage: AAISThinkingLanguageContent,
            context: AAISAPIServer.APICallTable.Entry) \
            -> AAISThinkingLanguageContent:
        """
        Formats a return message for the parent.
        """

        pass

    class APICallReturnResultType(Enum):
        SUCCESS = 0
        FAILURE = 1

    @abstractmethod
    async def determineAPICallReturnResultType(
            self, returnMessage: AAISThinkingLanguageContent,
            context: AAISAPIServer.APICallTable.Entry) \
            -> APICallReturnResultType:
        """
        Determines the type of the return message.
        """

        pass
