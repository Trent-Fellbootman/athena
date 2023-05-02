from .api_server import AAISAPIServer
from ...core import (
    AAISThinkingLanguageContent, AAISMessagePacket, AAISSystemServer
)

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class AAISTerminalAPIServer(AAISAPIServer, ABC):

    @dataclass
    class ArgumentParseResult:

        class ResultType(Enum):
            SUCCESS = 0
            FAILURE = 1

        resultType: ResultType
        parsedArguments: Optional[Any]
        errorMessage: Optional[AAISThinkingLanguageContent]

    @abstractmethod
    async def parseArguments(self, requestMessage: AAISThinkingLanguageContent)\
            -> ArgumentParseResult:
        """
        validates and parses the arguments
        """
        pass

    class ErrorType(Enum):
        INVALID_ARGUMENTS = 0
        EXECUTION_ERROR = 1

    @dataclass
    class APICallResult:
        """
        Thinking-language-agnostic result of the API call.
        """

        class ResultType(Enum):
            SUCCESS = 0
            FAILURE = 1

        resultType: ResultType
        # information to be returned on success
        reportInformation: Optional[Any]
        # error message to be returned on failure
        errorMessage: Optional[Any]

    async def handleRequest(self, request: AAISMessagePacket):
        """
        handles the request.
        """

        systemHandle: AAISSystemServer = self.systemHandle

        # create a new entry in the api call table
        new_api_call_entry: AAISAPIServer.APICallRecordTable.Record = self._apiCallRecords.createEntry()
        new_api_call_entry.senderAddress = request.header.senderAddress
        new_api_call_entry.description = await self.summarizeRequest(request)
        new_api_call_entry.status = AAISAPIServer.APICallRecordTable.Record.APICallStatus.UNHANDLED

        # parse the arguments
        parseResult = await self.parseArguments(request.content)

        match parseResult.resultType:
            case AAISTerminalAPIServer.ArgumentParseResult.ResultType.SUCCESS:
                # Successfully parsed the arguments
                assert parseResult.parsedArguments is not None

                call_result = await self.makeAPICall(parseResult.parsedArguments)

                match call_result.resultType:
                    case AAISTerminalAPIServer.APICallResult.ResultType.SUCCESS:
                        # Successfully executed the API call
                        assert call_result.reportInformation is not None

                        new_api_call_entry.status = AAISAPIServer.APICallRecordTable.Record.APICallStatus.SUCCESS

                        # make the packet to send back
                        return_message = await self.formatAPICallReportInformation(call_result.reportInformation)

                        return_header = AAISMessagePacket.Header(
                            messageType=AAISMessagePacket.Header.MessageType.communication,
                            senderAddress=self.address)

                        return_packet = AAISMessagePacket(
                            header=return_header,
                            content=return_message)

                        # send the packet
                        await systemHandle.sendMessage(return_packet, request.header.senderAddress)

                    case AAISTerminalAPIServer.APICallResult.ResultType.FAILURE:
                        # Failed to execute the API call
                        assert call_result.errorMessage is not None

                        new_api_call_entry.status = AAISAPIServer.APICallRecordTable.Record.APICallStatus.FAILURE
                        pass

            case AAISTerminalAPIServer.ArgumentParseResult.ResultType.FAILURE:
                # Failed to parse the arguments

                new_api_call_entry.status = AAISAPIServer.APICallRecordTable.Record.APICallStatus.FAILURE

                report_information = await self.formatErrorMessage(
                    parseResult.errorMessage, AAISTerminalAPIServer.ErrorType.INVALID_ARGUMENTS)

                # make the packet to send back
                return_header = AAISMessagePacket.Header(
                    messageType=AAISMessagePacket.Header.MessageType.communication,
                    senderAddress=self.address)

                return_packet = AAISMessagePacket(
                    header=return_header,
                    content=report_information)

                # send the packet back to the request's sender
                await systemHandle.sendMessage(return_packet, request.header.senderAddress)

    @abstractmethod
    async def makeAPICall(self, arguments: Any) -> APICallResult:
        pass

    @abstractmethod
    async def summarizeRequest(self, request: AAISMessagePacket) -> AAISThinkingLanguageContent:
        """
            summarizes the request.
        """
        pass

    @abstractmethod
    async def formatErrorMessage(self, errorMessage: Any, errorType: ErrorType)\
            -> AAISThinkingLanguageContent:
        """
        translates argument parse error or execution error to ThinkingLanguageContent.
        """
        pass

    @abstractmethod
    async def formatAPICallReportInformation(self, returnInformation: Any)\
            -> AAISThinkingLanguageContent:
        """
        translates the returned information of an API call to ThinkingLanguageContent.
        """
        pass
