from ..functional import AAISFunctional
from ...core import AAISResult, AAISThinkingLanguageContent, AAISException
from typing import TypeVar


T = TypeVar('T')
U = TypeVar('U')


class AAISLambda(AAISFunctional[T, U]):
    """
    Represents a lambda function that can be called.

    Notice that this is a fast functional that should return immediately.

    This functional returns failure only when the calling the underlying function
    raises an AAISException.
    """

    def __init__(self, function: callable):
        """
        Initialize this lambda function with the given function.

        Args:
            function: The function to use for this lambda functional.
                The function should take in `T` and output `U`.
                This argument should be fast, non-blocking and non-awaitable.
        """

        self._function = function

    async def call(self, inputs: T) -> AAISResult[U, AAISThinkingLanguageContent]:
        try:
            return AAISResult(
                success=True,
                value=self._function(inputs),
                errorMessage=None
            )
        except AAISException:
            return AAISResult(
                success=False,
                value=None,
                # TODO: allow error message from the exception to be passed through
                errorMessage=None
            )
