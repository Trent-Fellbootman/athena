from ..core.core import *
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List, Any
import asyncio


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

    # the ultimate caller of the API call
    caller: AAISProcess
    # the stack of non-terminal API servers that the request has passed through.
    # the process at the bottom is the caller, while the top is the sender.
    routerStack: List[AAISProcess]


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


@dataclass
class AAISAPIServerAPICallInitiateResult:
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
    # the processes that the request has passed through
    # the bottom of the stack is the caller, while the top of the stack
    # is the receiver of the message
    routerStack: List[AAISProcess]


class AAISAPIServerProcess(AAISProcess, ABC):
    """
    Represents an API server.

    Note that the API server does not need to use the AAIS system's
    thinking language internally;
    it only needs to communicate in the thinking language of the system.

    This is the BASE CLASS of all API servers, including
    API hubs (i.e., API servers that simply direct the
    API calls to the correct sub-servers) and "terminal API servers"
    (i.e., API servers that do the actual work and do not have "child API servers").

    Hub servers and terminal servers may add additional abstract methods.

    Generally, when an API server receives a request, this is what happens:
    1. The API server adds the request to the task queue.
    When this is done, handleMessage` returns.
    2. When the request is taken out of the task queue, the API server
    parses the request and validates the arguments.
    3. The API server initiates the API call.

    If arguments are invalid or API call initiation fails,
    the API server sends back an error message to the sender
    of the request message, and the API call finishes.
    This message will ultimately be forwarded to the caller.

    If the API call is successfully initiated, no message is sent back
    and `processRequest` returns.
    In this case, a message will be sent back when the API call
    actually completes (or when the pre-report stage completes).
    """

    def __init__(self):
        super().__init__()
        self._requestProcessQueue = []

    # override
    async def handleMessage(self, message: AAISMessage):
        """
        For API servers, the `handleMessage` method only
        adds the message to the task queue.

        Awaiting this method is NOT waiting for the API
        call to complete.
        """

        # schedule the processing of request in the event loop
        if isinstance(message, AAISAPIRequestMessage):
            # Message is an API call request from a caller
            self._requestProcessQueue.append(asyncio.create_task(self.processRequest(message)))
        elif isinstance(message, AAISAPIServerReportMessage):
            # Message is a report from another API server.
            # pop the router stack, forward the report to the "parent"
            # and wait for the message to be handled
            parent = message.routerStack.pop()
            await message.send(parent)
        else:
            # TODO: customize error class
            raise Exception("Invalid message type: {}".format(type(message)))

        # `handleMessage` returns here, to avoid deadlocks

    async def processRequest(self, request: AAISAPIRequestMessage):
        """
        Processes an API call request.
        This method only INITIATES the API call.
        The return of this method does NOT mean that the API call
        has completed.
        Instead, when the API call actually completes, another message
        is sent back to the caller.

        Awaiting this method is NOT waiting for the API call to finish.

        For "terminal API servers" (i.e., API servers
        that do the actual work and do not have "child API servers"),
        calling this method does the following:

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

        For "API hubs" (i.e., API servers that simply direct the
        API calls to the correct sub-servers (which can be either
        "terminal API servers" or other API hubs), this method
        simply directs the request to the correct "child API server".
        """

        # parse the arguments
        parse_result = await self.validateAndParseArguments(request)

        if not parse_result.success:
            # parse failed, send back the error message
            # make the return message
            return_message = self.translateArgumentParseError(parse_result.errorMessage)
            routers = request.routerStack.copy()
            return_message = AAISAPIServerReportMessage(
                content=return_message,
                metadata=AAISAPIServerReportMessage.Metadata(success=False),
                sender=self,
                routerStack=routers)
            # send back the message.
            # note that the error message is sent back to the parent; not the caller
            # also wait until the message is received.
            await return_message.send(request.sender)

            return

        # parse succeeded, initiate the API call
        call_initiate_result = await self.initiateAPICall(parse_result.arguments, request.sender)

        if not call_initiate_result.success:
            # API call failed, make the return message
            return_message = self.translateAPICallInitiationError(call_initiate_result.errorMessage)
            return_message = AAISAPIServerReportMessage(
                content=return_message,
                metadata=AAISAPIServerReportMessage.Metadata(success=False),
                sender=self,
                routerStack=request.routerStack.copy())
            # send back the message.
            # note that the error message is sent back to the parent; not the caller
            # also wait until the message is received.
            await return_message.send(request.sender)

        # API call request processing finishes here. What happens next is not the responsibility of this method.

    @abstractmethod
    def translateArgumentParseError(self, errorMessage: Any) \
            -> AAISThinkingLanguageContent:
        """
        Makes the return message for an API call
        from argument parse error returned by `validateAndParseArguments`.
        """

        pass

    @abstractmethod
    def translateAPICallInitiationError(self, errorMessage: Any) \
            -> AAISThinkingLanguageContent:
        """
        Makes the return message for an API call
        from the error message of an unsuccessful API call, returned by `makeAPICall`.

        Note that when this method is called, it is
        assumed that the argument parsing stage is successful.
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
    async def initiateAPICall(self, arguments: AAISAPIServerCallArguments, caller: AAISProcess)\
            -> AAISAPIServerAPICallInitiateResult:
        """
        Initiates the API call to the underlying API interface.

        Note that this method only initiates the API call;
        awaiting this method does NOT wait for the API call to finish.
        """

        pass


@dataclass
class AAISAPIHubServerSubServerTableEntry:
    """
    Represents an entry in the sub-server table of an API hub server.
    """

    # functional description of the sub-server
    functionalDescription: AAISThinkingLanguageContent
    # handle to the sub-server
    server: AAISAPIServerProcess


@dataclass
class AAISAPIHubServerCallArguments(AAISAPIServerCallArguments):
    selectedSubServer: AAISAPIServerProcess
    requestMessage: AAISAPIRequestMessage


class AAISAPIHubServerProcess(AAISAPIServerProcess, ABC):
    """
    Represents an API hub server.

    API hub servers are API servers that simply direct the
    API calls to the correct sub-servers (which can be either
    "terminal API servers" or other API hubs).
    """

    def __init__(self):
        super().__init__()

        # sub-server table
        self._subServerTable: Set[AAISAPIHubServerSubServerTableEntry] = set()

    # override
    async def validateAndParseArguments(self, request: AAISAPIRequestMessage) \
            -> AAISAPIServerArgumentParseResult:
        """
        tries to find a sub-server to direct the API call to.
        """

        match await self.selectSubServer(request):
            case None:
                # no sub-server found, return error
                # TODO: add actual error message?
                return AAISAPIServerArgumentParseResult(
                    success=False, errorMessage=None, arguments=None)
            case subServer:
                # sub-server found, return the arguments
                return AAISAPIServerArgumentParseResult(
                    success=True,
                    errorMessage=None,
                    arguments=AAISAPIHubServerCallArguments(selectedSubServer=subServer, requestMessage=request))

    # override
    async def initiateAPICall(self, arguments: AAISAPIHubServerCallArguments, caller: AAISProcess)\
            -> AAISAPIServerAPICallInitiateResult:
        """
        This method simply directs the request to the correct "child API server".
        """

        # TODO: should we modify the request message?
        request_message = arguments.requestMessage
        request_message.routerStack.append(self)
        await request_message.send(arguments.selectedSubServer)

        return AAISAPIServerAPICallInitiateResult(success=True, errorMessage=None, report=None)

    @abstractmethod
    async def selectSubServer(self, request: AAISAPIRequestMessage)\
            -> AAISAPIServerProcess:
        """
        Selects the sub-server to direct the API call to.
        If the API call cannot be directed to any sub-server,
        return None.
        """

        pass


class AAISTerminalAPIServerProcess(AAISAPIServerProcess, ABC):
    """
    Represents a terminal API server.
    """

    @dataclass
    class AAISTerminalAPICallContext(ABC):
        """
        Represents all information needed
        to determine what an API call does,
        all information needed to perform an API call & report to caller,
        and the current status of the API call operation.
        """

        routerStack: List[AAISProcess]

    class PreReportAPICallReport(ABC):
        pass

    def __init__(self):
        super().__init__()

        # keeps record of all API calls in progress
        self._apiCallsInProgress = []

    # override
    async def initiateAPICall(self, arguments: AAISAPIServerCallArguments, caller: AAISProcess)\
            -> AAISAPIServerAPICallInitiateResult:
        """
        This method starts a coroutine that makes the API call
        from start to finish.

        However, the method itself returns as soon as the API call is initiated.
        """

        # schedule the API call
        self._apiCallsInProgress.append(asyncio.create_task(self.performAPICall(arguments=arguments, caller=caller)))

        # TODO: add actual report & error message
        return AAISAPIServerAPICallInitiateResult(success=True, report=None, errorMessage=None)

    async def performAPICall(self, arguments: AAISAPIServerCallArguments, caller: AAISProcess):
        """
        Performs the API call.
        Call to this method is scheduled by `initiateAPICall`.
        """

        # create context
        context = await self.createInitialAPICallContext(arguments)
        # pre-report API call
        api_report = await self.preReportAPICall(context)
        report_message = await self.translateReport(api_report)
        report_message.routerStack =
        # wait for the caller to receive the report message
        await report_message.send(caller)
        # now it is safe to do the post-report portion of the API call
        # post-report API call
        await self.postReportAPICall(context, caller)

        # all stages of the API call finished, method returns here

    @abstractmethod
    async def createInitialAPICallContext(self, arguments: AAISAPIServerCallArguments) -> AAISTerminalAPICallContext:
        """
        Creates the initial context for an API call, given the parsed arguments.
        """

        pass

    @abstractmethod
    async def preReportAPICall(self, context: AAISTerminalAPICallContext) -> PreReportAPICallReport:
        """
        Performs the pre-report portion of an API call.

        This method returns after the pre-report portion of the API call finishes.
        """

        pass

    @abstractmethod
    async def translateReport(self, report: PreReportAPICallReport) -> AAISAPIServerReportMessage:
        """
        Translates the pre-report report of an API call to a report message.

        There is no need to set the `routerStack` of the report message in this method,
        as that will be done in `performAPICall`.
        """

        pass

    @abstractmethod
    async def postReportAPICall(self, context: AAISTerminalAPICallContext, caller: AAISProcess):
        """
        Performs the post-report portion of an API call
        (typically things that mingles with the caller).
        """

        pass
