import asyncio
from enum import Enum
from abc import ABC, abstractmethod
from collections import deque
from typing import Optional

from .api_server import AAISAPIServer
from .messages import AAISAPIServerReportPacket, AAISAPIServerAPIRequestRoutePacket
from ...core import (
    AAISMessagePacket, AAISThinkingLanguageContent, AAISProcess,
    AAISSystemServer, AAISResult
)


class AAISAPIHub(AAISAPIServer, ABC):
    class ErrorType(Enum):
        FAILED_TO_DETERMINE_MESSAGE_TYPE = 0
        FAILED_TO_FIND_HANDLER = 1
        FAILED_TO_MATCH_API_CALL_RECORD = 2
        EXECUTION_ERROR = 3
        FAILED_TO_DETERMINE_CHILD_SERVER_RETURN_RESULT_TYPE = 4

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
            match message_type_result.value:
                case AAISAPIServer.APIServerMessageType.REQUEST:
                    # 1. Update the API call table

                    # make new ID and create entry
                    new_api_call_record: AAISAPIServer.APICallRecordTable.Record = self._apiCallRecords.createEntry()
                    # set the fields of the entry
                    new_api_call_record.description = await self.summarizeRequest(receivedMessage.content)
                    new_api_call_record.senderAddress = receivedMessage.header.senderAddress
                    new_api_call_record.status = AAISAPIServer.APICallRecordTable.Record.APICallStatus.UNHANDLED
                    new_api_call_record.parentIdentifier = \
                        receivedMessage.routeMetadata.upstreamApiCallRecordIdentifier \
                        if isinstance(receivedMessage, AAISAPIServerAPIRequestRoutePacket) \
                        else None

                    # 2. Forward the request to the correct child API server

                    # find the child API server to call
                    handler_match_result = await self.selectHandler(receivedMessage.content)

                    if handler_match_result.success:
                        assert handler_match_result.value is not None

                        handler_entry = handler_match_result.value

                        # send the request to the child API server
                        dispatch_message = await self.formatRequestForChildServer(
                            receivedMessage.content, handler_entry)

                        dispatch_packet = AAISAPIServerAPIRequestRoutePacket(
                            header=AAISMessagePacket.Header(
                                messageType=AAISMessagePacket.Header.MessageType.communication,
                                senderAddress=self.address),
                            content=dispatch_message,
                            routeMetadata=AAISAPIServerAPIRequestRoutePacket.RouteMetadata(
                                upstreamApiCallRecordIdentifier=new_api_call_record.identifier
                            )
                        )

                        # send the packet to the child API server
                        await systemHandle.sendMessage(
                            dispatch_packet, handler_entry.refereeAddress)

                        new_api_call_record.status = AAISAPIServer.APICallRecordTable.Record.APICallStatus.RUNNING

                    else:
                        # failed to find handler
                        # write the error message
                        error_message = await self.formatErrorMessage(
                            errorType=AAISAPIHub.ErrorType.FAILED_TO_FIND_HANDLER,
                            errorMessage=handler_match_result.errorMessage)

                        # make the return packet
                        return_packet = AAISAPIServerReportPacket(
                            header=AAISMessagePacket.Header(
                                messageType=AAISMessagePacket.Header.MessageType.communication,
                                senderAddress=self.address),
                            content=error_message,
                            reportMetadata=AAISAPIServerReportPacket.ReportMetadata(
                                upstreamApiCallRecordIdentifier=new_api_call_record.parentIdentifier
                            )
                        )

                        # send the return message to the parent
                        await systemHandle.sendMessage(return_packet, receivedMessage.header.senderAddress)

                        new_api_call_record.status = AAISAPIServer.APICallRecordTable.Record.APICallStatus.FAILURE

                case AAISAPIServer.APIServerMessageType.RETURN_MESSAGE:
                    # since the message is returned to this server, which is an API hub,
                    # we can assume that the message contains api call record identifier,
                    # which is passed to the child server when dispatching the API call request.
                    assert isinstance(receivedMessage, AAISAPIServerReportPacket) and \
                           receivedMessage.reportMetadata.upstreamApiCallRecordIdentifier is not None

                    # 1. Find the corresponding record in the API call table
                    record_match_result = self.apiCallRecordTable.findRecordWithID(
                        receivedMessage.reportMetadata.upstreamApiCallRecordIdentifier)

                    if record_match_result.success:
                        # successfully found the record
                        assert record_match_result.value is not None
                        record = record_match_result.value

                        assert record.status == \
                               AAISAPIServer.APICallRecordTable.Record.APICallStatus.RUNNING

                        # update the status of the record
                        return_result_type_result = await self.determineAPICallReturnResultType(
                            receivedMessage.content, record)

                        if return_result_type_result.success:
                            match return_result_type_result.value:
                                case AAISAPIHub.APICallReturnResultType.SUCCESS:
                                    record.status = \
                                        AAISAPIServer.APICallRecordTable.Record.APICallStatus.SUCCESS
                                case AAISAPIHub.APICallReturnResultType.FAILURE:
                                    record.status = \
                                        AAISAPIServer.APICallRecordTable.Record.APICallStatus.FAILURE

                            # send the return message to the parent
                            parent_return_message = await self.formatReturnMessageForParent(
                                returnMessage=receivedMessage.content,
                                context=record)

                            parent_return_packet = AAISAPIServerReportPacket(
                                header=AAISMessagePacket.Header(
                                    messageType=AAISMessagePacket.Header.MessageType.communication,
                                    senderAddress=self.address),
                                content=parent_return_message,
                                reportMetadata=AAISAPIServerReportPacket.ReportMetadata(
                                    upstreamApiCallRecordIdentifier=record.parentIdentifier
                                )
                            )

                            await systemHandle.sendMessage(parent_return_packet, record.senderAddress)

                            # TODO: should we remove the record from the API call table?

                        else:
                            # failed to determine the return result type.
                            # send an error message to the sender of the message.
                            return_message = await self.formatErrorMessage(
                                errorType=AAISAPIHub.ErrorType.FAILED_TO_DETERMINE_CHILD_SERVER_RETURN_RESULT_TYPE,
                                errorMessage=return_result_type_result.errorMessage)

                            return_packet = AAISMessagePacket(
                                header=AAISMessagePacket.Header(
                                    messageType=AAISMessagePacket.Header.MessageType.communication,
                                    senderAddress=self.address),
                                content=return_message)

                            await systemHandle.sendMessage(return_packet, receivedMessage.header.senderAddress)

                    else:
                        # Failed to find record matching the return message
                        # send the error back to the sender of the message

                        # TODO: include the identifier of the record in the error message
                        return_message = await self.formatErrorMessage(
                            errorType=AAISAPIHub.ErrorType.FAILED_TO_MATCH_API_CALL_RECORD,
                            errorMessage=record_match_result.errorMessage)

                        return_header = AAISMessagePacket.Header(
                            messageType=AAISMessagePacket.Header.MessageType.communication,
                            senderAddress=self.address)

                        return_packet = AAISMessagePacket(
                            header=return_header,
                            content=return_message)

                        await systemHandle.sendMessage(return_packet, receivedMessage.header.senderAddress)

        else:
            # failed to determine message's type;
            # send an error message to sender of the message

            return_message = await self.formatErrorMessage(
                errorType=AAISAPIHub.ErrorType.FAILED_TO_DETERMINE_MESSAGE_TYPE,
                errorMessage=None
            )

            return_packet = AAISAPIServerReportPacket(
                header=AAISMessagePacket.Header(
                    messageType=AAISMessagePacket.Header.MessageType.communication,
                    senderAddress=self.address),
                content=return_message,
                reportMetadata=AAISAPIServerReportPacket.ReportMetadata(
                    upstreamApiCallRecordIdentifier=
                    receivedMessage.routeMetadata.upstreamApiCallRecordIdentifier
                    if isinstance(receivedMessage, AAISAPIServerAPIRequestRoutePacket)
                    else None
                )
            )

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
            -> AAISResult[AAISAPIServer.APICallRecordTable.Record, AAISThinkingLanguageContent]:
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
            context: AAISAPIServer.APICallRecordTable.Record) \
            -> AAISThinkingLanguageContent:
        """
        Formats a return message for the parent.

        The input to this method is the message returned from
        a child API server;
        The output of this method is used as the content of the message
        returned to the parent.
        """

        pass

    class APICallReturnResultType(Enum):
        SUCCESS = 0
        FAILURE = 1

    @abstractmethod
    async def determineAPICallReturnResultType(
            self, returnMessage: AAISThinkingLanguageContent,
            context: AAISAPIServer.APICallRecordTable.Record) \
            -> AAISResult[APICallReturnResultType, AAISThinkingLanguageContent]:
        """
        Determines the type of the return message.
        """

        pass
