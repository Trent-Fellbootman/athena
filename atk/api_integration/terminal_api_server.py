from ..core.core import (
    AAISThinkingLanguageContent, AAISMessagePacket,
    AAISMessageHeader, AAISMessageType
)

from base import AAISAPIServer
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class AAISTerminalAPIServer(ABC, AAISAPIServer):

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

        # create a new entry in the api call table
        new_api_call_entry: AAISAPIServer.APICallTable.Entry = self.apiCallTable.createEntry()
        new_api_call_entry.sender = request.header.sender
        new_api_call_entry.summary = await self.summarizeRequest(request)
        new_api_call_entry.status = AAISAPIServer.APICallTable.Entry.APICallStatus.UNHANDLED

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

                        new_api_call_entry.status = AAISAPIServer.APICallTable.Entry.APICallStatus.SUCCESS

                        # make the packet to send back
                        return_message = await self.formatAPICallReportInformation(call_result.reportInformation)

                        return_header = AAISMessageHeader(
                            messageType=AAISMessageType.communication,
                            sender=self)

                        return_packet = AAISMessagePacket(
                            header=return_header,
                            content=return_message)

                        # send the packet
                        await return_packet.send(request.header.sender)

                    case AAISTerminalAPIServer.APICallResult.ResultType.FAILURE:
                        # Failed to execute the API call
                        assert call_result.errorMessage is not None

                        new_api_call_entry.status = AAISAPIServer.APICallTable.Entry.APICallStatus.FAILURE
                        pass

            case AAISTerminalAPIServer.ArgumentParseResult.ResultType.FAILURE:
                # Failed to parse the arguments

                new_api_call_entry.status = AAISAPIServer.APICallTable.Entry.APICallStatus.FAILURE

                report_information = await self.formatErrorMessage(
                    parseResult.errorMessage, AAISTerminalAPIServer.ErrorType.INVALID_ARGUMENTS)

                # make the packet to send back
                return_header = AAISMessageHeader(
                    messageType=AAISMessageType.communication,
                    sender=self)

                return_packet = AAISMessagePacket(
                    header=return_header,
                    content=report_information)

                # send the packet back to the request's sender
                await return_packet.send(request.header.sender)

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