from atk.functional.functional import inputType
from ..functional import AAISFunctional
from typing import TypeVar


T = TypeVar('T')
U = TypeVar('U')


class AAISLambda(AAISFunctional[T, U]):
    """
    Represents a lambda function that can be called.

    Notice that this is a fast functional that should return immediately.
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

    async def call(self, inputs: inputType) -> AAISFunctional.InvocationResult:
        return AAISFunctional.InvocationResult(
            success=True,
            output=self._function(inputs),
            errorMessage=None
        )