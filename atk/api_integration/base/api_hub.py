import asyncio
from enum import Enum
from abc import ABC, abstractmethod
from collections import deque
from typing import Optional

from .api_server import AAISAPIServer
from ...core import (
    AAISMessagePacket, AAISThinkingLanguageContent, AAISProcess,
    AAISSystemServer, AAISResult
)


class AAISAPIHub(AAISAPIServer, ABC):
    class ErrorType(Enum):
        FAILED_TO_DETERMINE_MESSAGE_TYPE = 0
        FAILED_TO_FIND_HANDLER = 1
        EXECUTION_ERROR = 2

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
        systemHandle: AAISSystemServer = self.systemHandle

        message_type_result = await self.determineMessageType(receivedMessage)

        if message_type_result.success:
            match message_type_result.output:
                case AAISAPIServer.APIServerMessageType.request:
                    # 1. Update the API call table

                    # make new ID and create entry
                    new_api_call_entry: AAISAPIServer.APICallTable.Entry = self.apiCallTable.createEntry()
                    # set the fields of the entry
                    new_api_call_entry.summary = await self.summarizeRequest(receivedMessage.content)
                    new_api_call_entry.senderAddress = receivedMessage.header.senderAddress
                    new_api_call_entry.status = AAISAPIServer.APICallTable.Entry.APICallStatus.UNHANDLED

                    # 2. Forward the request to the correct child API server

                    # find the child API server to call
                    handler_match_result = await self.selectHandler(receivedMessage.content)

                    if handler_match_result.success:
                        assert handler_match_result.output is not None

                        handler_entry = handler_match_result.output

                        # send the request to the child API server
                        dispatch_message = await self.formatRequestForChildServer(
                            receivedMessage.content, handler_entry)

                        dispatch_message_header = AAISMessagePacket.Header(
                            messageType=AAISMessagePacket.Header.MessageType.communication,
                            senderAddress=self.address)

                        dispatch_packet = AAISMessagePacket(
                            header=dispatch_message_header,
                            content=dispatch_message)

                        # send the packet to the child API server
                        await systemHandle.sendMessage(
                            dispatch_packet, handler_entry.refereeAddress)

                        new_api_call_entry.status = AAISAPIServer.APICallTable.Entry.APICallStatus.RUNNING

                    else:
                        # failed to find handler
                        assert handler_match_result.errorMessage is not None

                        # write the error message
                        error_message = await self.formatErrorMessage(
                            errorType=AAISAPIHub.ErrorType.FAILED_TO_FIND_HANDLER,
                            errorMessage=handler_match_result.errorMessage)

                        # make the return packet
                        return_message_header = AAISMessagePacket.Header(
                            messageType=AAISMessagePacket.Header.MessageType.communication,
                            senderAddress=self.address)

                        return_packet = AAISMessagePacket(
                            header=return_message_header,
                            content=error_message)

                        # send the return message to the parent
                        await systemHandle.sendMessage(return_packet, receivedMessage.header.senderAddress)

                        new_api_call_entry.status = AAISAPIServer.APICallTable.Entry.APICallStatus.FAILURE

                case AAISAPIServer.APIServerMessageType.returnMessage:
                    # 1. Find the corresponding record in the API call table
                    record_match_result = await self.matchReturnMessageWithAPICallRecord(receivedMessage)

                    if record_match_result.success:
                        # successfully found the record
                        # TODO: Add error handling for these.
                        #  Mismatch is always possible.

                        assert record_match_result.output is not None
                        record = record_match_result.output

                        assert record.status == \
                               AAISAPIServer.APICallTable.Entry.APICallStatus.RUNNING

                        # update the status of the record
                        match await self.determineAPICallReturnResultType(
                                receivedMessage.content, record):
                            case AAISAPIHub.APICallReturnResultType.SUCCESS:
                                record.status = \
                                    AAISAPIServer.APICallTable.Entry.APICallStatus.SUCCESS
                            case AAISAPIHub.APICallReturnResultType.FAILURE:
                                record.status = \
                                    AAISAPIServer.APICallTable.Entry.APICallStatus.FAILURE

                        # send the return message to the parent
                        parent_return_message = await self.formatReturnMessageForParent(
                            returnMessage=receivedMessage.content,
                            context=record)

                        parent_return_header = AAISMessagePacket.Header(
                            messageType=AAISMessagePacket.Header.MessageType.communication,
                            senderAddress=self.address)

                        parent_return_packet = AAISMessagePacket(
                            header=parent_return_header,
                            content=parent_return_message)

                        await systemHandle.sendMessage(parent_return_packet, record.senderAddress)

                        # TODO: should we remove the record from the API call table?

                    else:
                        # Failed to find record matching the return message
                        # TODO: what should we do here?
                        assert record_match_result.errorMessage is not None
                        pass
        else:
            # failed to determine message's type;
            # send an error message to sender of the message
            return_message = await self.formatErrorMessage(
                errorType=AAISAPIHub.ErrorType.FAILED_TO_DETERMINE_MESSAGE_TYPE,
                errorMessage=None
            )

            return_message_header = AAISMessagePacket.Header(
                messageType=AAISMessagePacket.Header.MessageType.communication,
                senderAddress=self.address)

            return_packet = AAISMessagePacket(
                header=return_message_header,
                content=return_message)

            await systemHandle.sendMessage(return_packet, receivedMessage.header.senderAddress)

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
            -> AAISResult[AAISAPIServer.APIServerMessageType, AAISThinkingLanguageContent]:
        """
        Determines the type of `message`.
        """

        pass

    @abstractmethod
    async def selectHandler(self, request: AAISThinkingLanguageContent) \
            -> AAISResult[AAISProcess.ReferenceTable.Entry, AAISThinkingLanguageContent]:
        """
        Determines the correct child API server to call for `request`.
        """

        pass

    @abstractmethod
    async def matchReturnMessageWithAPICallRecord(
            self, returnMessage: AAISMessagePacket) \
            -> AAISResult[AAISAPIServer.APICallTable.Entry, AAISThinkingLanguageContent]:
        """
        Matches a return message with an API call record.
        """

        pass

    @abstractmethod
    async def formatErrorMessage(self, errorType: ErrorType, errorMessage: Optional[AAISThinkingLanguageContent]) \
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
