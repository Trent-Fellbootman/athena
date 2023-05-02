from ..functional import AAISFunctional
from ...core import AAISThinkingLanguageContent, AAISResult

from typing import TypeVar


T = TypeVar('T')
U = TypeVar('U')


class AAISSupervisedFunctional(AAISFunctional):
    # TODO: should we implement an asynchronous version?
    """
    A functional that checks the result of another functional.

    This functional consists of two components: a "worker" and
    a "supervisor".

    When the functional is called, the "worker" is called;
    When the worker returns, the "supervisor" is called to
    check the results of the worker.
    If the results are valid, the result of the worker is returned;
    otherwise, the worker is re-called, and this process repeats.
    If the worker fails for a certain number of times, the
    functional will return failure.

    Supervisor should return True for valid results and False otherwise.

    An additional argument is required: the error message to return
    on failure.
    Note that the only way to fail is to exceed the maximum number
    of tries.
    """

    def __init__(self,
                 functional: AAISFunctional[T, U],
                 supervisor: AAISFunctional[U, bool],
                 maxTries: int,
                 errorMessage: AAISThinkingLanguageContent):
        self._functional = functional
        self._supervisor = supervisor
        self._maxTries = maxTries
        self._errorMessage = errorMessage

    async def tryCallAndValidate(self, inputs: T) -> AAISResult[U, AAISThinkingLanguageContent]:
        """
        Try calling the worker and validate its results.

        Args:
            inputs: The inputs to the worker.

        Returns:
            The result of the worker.
        """

        # call the worker
        worker_result = await self._functional.call(inputs)
        if not worker_result.success:
            return worker_result

        # validate the worker's return
        supervisor_result = await self._supervisor.call(worker_result.output)
        if not supervisor_result.success:
            return supervisor_result

        if not supervisor_result.output:
            # worker's return is invalid
            return AAISResult(
                success=False,
                output=None,
                # we don't actually need the error message here;
                # we provide a non-None error message just to avoid
                # potential type checking
                errorMessage=self._errorMessage)

        # worker's return is valid
        return worker_result

    # override
    async def call(self, inputs: T) -> AAISResult[U, AAISThinkingLanguageContent]:
        for i in range(self._maxTries):
            result = await self.tryCallAndValidate(inputs)
            if result.success:
                return result

        return AAISResult(
            success=False,
            output=None,
            errorMessage=self._errorMessage)
