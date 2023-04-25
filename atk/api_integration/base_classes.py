import asyncio

from ..core.core import *
from dataclasses import dataclass
from abc import ABC, abstractmethod


class AAISAPIRequestMessage(AAISMessage):

    """
    Represents a request message sent from the caller
    to the API server.

    Note that `sender` (attribute of `AAISMessage` base class)
    is not the same as `caller` (attribute of this class).

    In nested API servers, `sender` denotes the upstream
    API server from which the message is dispatched;
    `caller` denotes the actual process that requested
    the API call.
    """

    caller: AAISProcess


class AAISAPIServerCallArguments(ABC):
    """
    Represents the PARSED arguments of an API call, arguments
    that are passed to the API server's underlying, typically
    non-intelligent API interface.
    """
    pass


@dataclass
class AAISAPIServerArgumentParseResult:
    """
    Represents the result of parsing an API call's arguments
    from a request written in thinking language.
    """

    # whether parsing was successful
    success: bool
    # the parsed arguments, if parsing was successful
    arguments: AAISAPIServerCallArguments | None
    # the error message, if parsing was unsuccessful
    errorMessage: Any | None


class AAISAPIServerAPICallResult:
    """
    Represents the result of an API call made by the API server,
    after validating and parsing the arguments.
    """

    # whether the API call was successful
    success: bool
    # the report of the API call, if successful
    report: Any | None
    # the error message, if unsuccessful
    errorMessage: Any | None


@dataclass
class AAISAPIServerReportMessage(AAISMessage):
    """
    Represents a report message sent from the API server.

    This message is sent after the pre-report stage of the API call
    has finished, but before the post-report stage starts.

    The API server begins the post-report stage of an API call
    only after awaiting and making sure that the caller has received
    this message.

    Pre-report stage means the portion of the API call that does not
    tamper with the caller and can thus happen before notifying the caller.

    Post-report stage means the portion of the API call that can only
    happen after notifying the caller.
    E.g., setting up a new communication channel for the caller
    by modifying its reference table.
    """

    @dataclass
    class Metadata:
        success: bool

    metadata: Metadata


class AAISAPIServerProcess(AAISProcess, ABC):
    """
    Represents an API server.

    Note that the API server does not need to use the AAIS system's
    thinking language internally;
    it only needs to communicate in the thinking language of the system.
    """

    def __init__(self):
        super().__init__()
        self._runningTasks = []

    # override
    async def handleMessage(self, message: AAISMessage):
        # schedule the processing of request in the event loop
        if isinstance(message, AAISAPIRequestMessage):
            self._runningTasks.append(asyncio.create_task(self.processRequest(message)))
        else:
            # TODO: customize error class
            raise Exception("Invalid message type: {}".format(type(message)))

        # `handleMessage` returns here, to avoid deadlocks

    async def processRequest(self, request: AAISAPIRequestMessage):
        """
        Processes an API call request.
        This includes:

        1. Parse the request message with `validateAndParseArguments`.
        2. Make the pre-report API call (the portion of the API call
        that does not tamper with the caller and can thus happen
        before notifying the caller).
        3. Report the status of the API call to the caller and wait
        until the caller receives the message.
        4. Make the post-report API call (the portion of the API call
        that can only happen after notifying the caller).

        The above components are run in a serial manner.
        That is, the next component is run after awaiting the previous.
        """

        # TODO
        # parse the arguments
        parse_result = await self.validateAndParseArguments(request)

        if not parse_result.success:
            # parse failed, send back the error message
            # make the return message
            return_message = self.makeArgumentParseErrorReturnMessage(parse_result.errorMessage)
            # send back the message.
            # note that the error message is sent back to the parent; not the caller
            # also wait until the message is received.
            await return_message.send(request.sender)

            return

        # parse succeeded, make the API call
        call_result = await self.makeAPICall(parse_result.arguments)

        if call_result.success:
            # API call succeeded, make the return message
            return_message = self.makeAPICallSuccessReportReturnMessage(call_result.report)
            # send back the message.
            # note that the report is sent back to the parent; not the caller
            # also wait until the message is received.
            await return_message.send(request.sender)
        else:
            # API call failed, make the return message
            return_message = self.makeAPICallErrorReturnMessage(call_result.errorMessage)
            # send back the message.
            # note that the error message is sent back to the parent; not the caller
            # also wait until the message is received.
            await return_message.send(request.sender)

        # API call request processing finishes here.

    @abstractmethod
    def makeArgumentParseErrorReturnMessage(self, errorMessage: Any) \
            -> AAISAPIServerReportMessage:
        """
        Makes the return message for an API call
        from argument parse error returned by `validateAndParseArguments`.
        """

        pass

    @abstractmethod
    def makeAPICallErrorReturnMessage(self, errorMessage: Any) \
            -> AAISAPIServerReportMessage:
        """
        Makes the return message for an API call
        from the error message of an unsuccessful API call, returned by `makeAPICall`.

        Note that when this method is called, it is
        assumed that the argument parsing stage is successful.
        """

        pass

    @abstractmethod
    def makeAPICallSuccessReportReturnMessage(self, report: Any) \
            -> AAISAPIServerReportMessage:
        """
        Makes the return message for an API call
        from the report of a successful API call, returned by `makeAPICall`.
        """

        pass

    @abstractmethod
    async def validateAndParseArguments(self, request: AAISAPIRequestMessage) \
            -> AAISAPIServerArgumentParseResult:
        """
        Validates and parses the arguments of an API call
        from a request written in thinking language.
        """

        pass

    @abstractmethod
    async def makeAPICall(self, arguments: AAISAPIServerCallArguments) -> AAISAPIServerAPICallResult:
        """
        Makes the API call to the underlying API interface.
        """

        pass
