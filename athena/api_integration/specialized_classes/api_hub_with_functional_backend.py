from dataclasses import dataclass
from typing import TypeVar, Optional, Generic, Tuple, Collection

from ..base import AAISAPIHub, AAISAPIServer
from ...core import AAISThinkingLanguageContent, AAISProcess, AAISMessagePacket, AAISResult
from ...functional import AAISFunctional


T = TypeVar('T', bound=AAISThinkingLanguageContent)


class AAISAPIHubWithFunctionalBackend(AAISAPIHub, Generic[T]):
    """
    A specialized API hub that achieves its functionality
    intelligently with a set of functionals.

    The generic type `T` is the thinking language used by the API hub internally.
    """

    @dataclass
    class Backend:
        r"""

        The backend of the API hub server consisting of
        a table of functionals that perform the
        API hub-related operations.

        Attributes:
            requestSummarizer:
                A functional that summarizes a request.
                The output of this functional is used to set the
                `summary` field of the record in the API call record table.
                
                This functional MUST NOT fail.

            messageTypeDeterminer:
                A functional that classifies incoming messages as either
                being an API call request or a report message from a child API server.

            handlerSelector:
                A functional that selects the correct child API handler for a request.
                Inputs to this functional are the description of each process
                that the API hub server has reference to (arg 0), as well as
                the request message (arg 1); output is the index of the handler
                (0-based), or -1 if no handler can be matched.

                It is assumed that the return from this functional will always be valid
                (i.e., index is valid), or the functional would return failure instead.

            returnMessageMatcher:
                A functional that matches a return message with an API call record.
                The first argument in the inputs provides a description for each
                API call in progress; the second argument is the return message
                received.
                The output is the index of the API call record that the return message
                matches with (0-based) or -1 if no match can be found.

                It is assumed that the return from this functional will always be valid
                (i.e., index is valid), or the functional would return failure instead.

            errorMessageFormatter:
                A functional that formats an error message.
                The first argument in the inputs is the error type;
                The second argument is the error message (if any).
                The output is the formatted error message that can be
                readily sent.
                
                This functional MUST NOT fail.

            childServerRequestGenerator:
                A functional that takes in a request and generates a request
                for the child server that matches with the request.
                The first argument is the request; the second is the description
                of the child API server.

                There is no need to parse or extract arguments in this functional;
                that will be done by the child server.
                
                This functional MUST NOT fail.

            parentReturnMessageGenerator:
                This functional generates the message to be returned to the issuer
                that sent an API call request to this API hub server previously,
                after a report message associated with this API call
                is received from a child server.
                The first argument to this functional is the return message from
                the child server; the second is the description of this API call.
                
                This functional MUST NOT fail.

            returnResultTypeDeterminer:
                This functional determines the return status of an API call (either success or failure),
                given the report message returned from a child API server.
                The first argument is the return message; the second is the description of the API call.
        """

        requestSummarizer: AAISFunctional[T, T]
        messageTypeDeterminer: AAISFunctional[T, AAISAPIServer.APIServerMessageType]
        handlerSelector: AAISFunctional[Tuple[Collection[T], T], int]
        returnMessageMatcher: AAISFunctional[Tuple[Collection[T], T], int]
        errorMessageFormatter: AAISFunctional[Tuple[AAISAPIHub.ErrorType, Optional[T]], T]
        childServerRequestGenerator: AAISFunctional[Tuple[T, T], T]
        parentReturnMessageGenerator: AAISFunctional[Tuple[T, T], T]
        returnResultTypeDeterminer: AAISFunctional[Tuple[T, T], AAISAPIHub.APICallReturnResultType]

    def __init__(self, backend: Backend):
        super().__init__()

        self._backend = backend

    async def summarizeRequest(self, requestMessage: T) -> T:
        result = await self._backend.requestSummarizer.call(requestMessage)
        assert result.success

        return result.value

    async def determineMessageType(self, message: AAISMessagePacket)\
            -> AAISResult[AAISAPIServer.APIServerMessageType, T]:
        result = await self._backend.messageTypeDeterminer.call(message.content)

        return result

    async def selectHandler(self, request: T)\
            -> AAISResult[AAISProcess.ReferenceTable.Entry, T]:
        result = await self._backend.handlerSelector.call((
            # TODO: should we feed in more contextual information?
            [reference.context.refereeDescription for reference in self._referenceTable.entries],
            request
        ))

        # the return is assumed to be value, as long as `result` is success
        if result.success:
            if result.value == -1:
                return AAISResult(
                    success=False,
                    value=None,
                    # TODO: add error message
                    errorMessage=None
                )
            else:
                return AAISResult(
                    success=True,
                    value=list(self._referenceTable.entries)[result.value],
                    errorMessage=None
                )
        else:
            return AAISResult(
                success=False,
                value=None,
                errorMessage=result.errorMessage
            )

    async def matchReturnMessageWithAPICallRecord(
            self, returnMessage: AAISMessagePacket)\
            -> AAISResult[AAISAPIServer.APICallRecordTable.Record, T]:

        result = await self._backend.returnMessageMatcher.call((
            [record.description for record in self.apiCallRecordTable.records],
            returnMessage.content
        ))

        if result.success:
            if result.value == -1:
                return AAISResult(
                    success=False,
                    value=None,
                    # TODO: add error message
                    errorMessage=None
                )
            else:
                return AAISResult(
                    success=True,
                    value=list(self.apiCallRecordTable.records)[result.value],
                    errorMessage=None
                )
        else:
            return AAISResult(
                success=False,
                value=None,
                errorMessage=result.errorMessage
            )

    async def formatErrorMessage(
            self, errorType: AAISAPIHub.ErrorType, errorMessage: Optional[T]) -> T:
        result = await self._backend.errorMessageFormatter.call((errorType, errorMessage))
        assert result.success

        return result.value

    async def formatRequestForChildServer(
            self, request: T, childServerEntry: AAISProcess.ReferenceTable.Entry) -> T:
        result = await self._backend.childServerRequestGenerator.call((
            request, childServerEntry.context.refereeDescription))
        assert result.success

        return result.value

    async def formatReturnMessageForParent(
            self, returnMessage: T, context: AAISAPIServer.APICallRecordTable.Record) -> T:
        result = await self._backend.parentReturnMessageGenerator.call((
            returnMessage, context.description))
        assert result.success

        return result.value

    async def determineAPICallReturnResultType(
            self, returnMessage: T, context: AAISAPIServer.APICallRecordTable.Record)\
            -> AAISResult[AAISAPIHub.APICallReturnResultType, AAISThinkingLanguageContent]:
        result = await self._backend.returnResultTypeDeterminer.call((returnMessage, context.description))

        return result
