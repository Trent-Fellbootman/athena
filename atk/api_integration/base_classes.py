from ..core.core import AAISProcess, AAISMessage, AAISMessageType, AAISThinkingLanguageContent
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple


class AAISProcessAPIHubServer(AAISProcess, ABC):
    """The API hub server process.

    # I/O format

    The "API hub" expects to receive a request
    in the form of the AAIS system's thinking language,
    and send messages in the thinking language as well.

    # Role

    The API hub is essentially a manager of multiple available
    "extensions" to an AAIS system's capabilities beyond thinking in
    its thinking language. Examples of such "extensions" may include:

    - "OS-only privileged functionalities" (e.g., spawning
    processes to do lower-level jobs; similar to sys calls.)
    - Multimedia read/write functionalities (e.g., DALL E 2, Gen 2, GPT 4)
    - Internet search & content retrieval (i.e., browser)
    - Operating system access (e.g., disk, sys calls, etc.)
    - Access to non-process components of this AAIS system (e.g., memory)

    The API hub is in charge of spawning worker processes ONLY;
    when it receives a request and checks that the request is valid,
    it just spawns a worker process, sets up the communication
    channel between the requestor and the worker (by modifying their
    reference tables), and what happens next is none of its business.

    The API hub is designed to be disentangled with concrete
    implementations of the various APIs themselves; each API
    is a separate module that can be "inserted" to or "removed" from
    the API hub dynamically.

    For each API, the API hub
    only has access to a brief description regarding what it does,
    in order to determine the particular API that a request is trying
    to access. It does NOT handle the potential API-specific invalidity
    of a request, and neither does it parse the arguments contained
    in the request; validity check and thinking-language-to-argument parsing
    are the APIs' job.

    When an API hub receives a request, it does the following:

    1. Determine the particular API to access.
    2. Forward the request to a specific API (i.e., the "module").
    3. When the API module reports success or failure, the API hub
    tells the requesting process about this and forwards the API module
    server's output to the requesting process. The module server's output
    may be an info message (e.g., "image have been saved to `/tmp/image.png`")
    or an error message (e.g., "list index out of range").
    """

    def __init__(self):
        super().__init__()

    # override
    def handleMessage(self, message: AAISMessage):
        """For an API hub, the message passed in to this callback
        is always assumed to be a request.

        Args:
            message (AAISMessage): The request.
        """

        # TODO


class AAISAPICallRequestMessageMetadata:
    """Metadata for an API request.

    Fields:
        caller: A handle to AAIS process that sent the request.
    """

    caller: AAISProcess


class AAISAPICallResultType(Enum):
    success = 0
    failure = 1


@dataclass
class AAISAPICallResult:
    """Represents the result of an API call.

    Fields:
        resultType: Whether the call succeeded or failed.
        result: The result of the call.
    """

    resultType: AAISAPICallResultType
    result: Any


@dataclass
class AAISAPICallReturnMessageMetadata:
    callStatus: AAISAPICallResultType


class AAISAPICallReturnMessage(AAISMessage):
    """Represents the return message of an API call.

    Fields:
        result: The result of the call.
    """

    metadata: AAISAPICallReturnMessageMetadata

    def __init__(self, content: AAISThinkingLanguageContent, metadata: AAISAPICallReturnMessageMetadata):
        super().__init__(messageType=AAISMessageType.communication, content=content)

        self.metadata = metadata


class AAISProcessAPIModuleServer(AAISProcess, ABC):
    """Represents an API module registered at the API hub.
    
    # I/O Format
    
    An API module server expects requests written in the
    AAIS system's thinking language, and sends messages in
    that language as well.
    
    # Role
    
    An API module server handles API requests. When it receives
    a request, it does the following:
    
    1. Parse the arguments and check for validity. Checking that
    the request is appropriate the API is not mandatory,
    since it is already done by the API hub server.
    2. Do what it should and report success or failure to the API
    hub server.
        1. Failure should be reported as soon as possible (e.g.,
        report arguments invalidity immediately after the argument parsing
        stage). For non-interactive API calls, such as image-text conversion,
        success should be reported after the entire API call has finished,
        and the message to be sent should contain all information expressible
        in the AAIS's thinking language.
        2. For interactive API calls, such as initiating a chatbot session,
        success should be reported **AFTER** it is certain that the API call will be
        successful (which is basically after arguments have been proven valid),
        and the interactive session should be started **AFTER** acknowledging that
        the requesting process has received the success message, to avoid
        the interactive session process sending messages to the requesting process
        before it knows that the interactive session has been spawned.

    The API module server itself should be thinking language agnostic.
    """

    @dataclass
    class AAISAPICallResult:
        """
        Represents the result of an API call.

        Fields:
            resultType: Whether the API call succeeded or failed.
            resultMessage: The message to sent back.
        """

        resultType: AAISAPICallResultType
        resultMessage: Any

    @abstractmethod
    async def validateAndParseArguments(self, request: AAISMessage) \
            -> Tuple[bool, Dict[str, Any] | Any]:
        """Validates a request,
        and parses the arguments into a format that is more convenient
        for the API module server to use. The parsed arguments are "machine-intelligible"
        (i.e, suitable for use with non-intelligent APIs).

        Args:
            request (AAISMessage): The request.

        Returns:
            Tuple[bool, Dict[str, Any] | Any]: A tuple of two elements,
                with the first being the parsing result type (True if success, False if failure),
                and the second being the parsed arguments (if success) or the error message (if failure).
        """

        pass

    @abstractmethod
    async def callAPI(self, args: Dict[str, Any]) -> AAISAPICallResult:
        """Calls the API with the parsed arguments. When calling
        this method, it is assumed that the arguments are valid.

        Args:
            args (Dict[str, Any]): The parsed arguments.
        """

        pass

    # override
    async def handleMessage(self, message: AAISMessage):
        """
        Take in a request, try to parse arguments and call the API

        Args:
            message (AAISMessage): The request.
        """

        success, result = self.validateAndParseArguments(message)

        if success:
            # success parsing arguments
            # call actual API
            call_result = await self.callAPI(result)
            assert type(call_result) is AAISAPICallResult

            if call_result == AAISAPICallResultType.success:
                # success calling API
                # send success message to API hub
                return_message = AAISAPICallReturnMessage(
                    content=await self.systemHandle
                    .thinkingLanguageServer
                    .convertToThinkingLanguage(call_result.resultMessage),
                    metadata=AAISAPICallReturnMessageMetadata(callStatus=AAISAPICallResultType.success))

            else:
                # failure calling API
                # send failure message to API hub
                return_message = AAISAPICallReturnMessage(
                    content=await self.systemHandle
                    .thinkingLanguageServer
                    .convertToThinkingLanguage(call_result.resultMessage),
                    metadata=AAISAPICallReturnMessageMetadata(callStatus=AAISAPICallResultType.failure))
        else:
            # failure parsing arguments
            # send error message to API hub
            return_message = AAISAPICallReturnMessage(
                content=await self.systemHandle
                .thinkingLanguageServer
                .convertToThinkingLanguage(result),
                metadata=AAISAPICallReturnMessageMetadata(callStatus=AAISAPICallResultType.failure))

        # send back the message
