from ..functional import AAISFunctional
from ...core import AAISThinkingLanguageContent, AAISResult

from typing import TypeVar, Collection


T = TypeVar('T')
U = TypeVar('U')


class AAISSequentialFunctional(AAISFunctional[T, U]):
    """
    A functional that applies a series of functionals to transform
    the input to the output in a sequential manner.

    The output of the previous functional is the input of the next functional,
    and their types must match.

    The operation is considered to be successful if and only if
    all the functionals are successfully applied.
    If one functional fails, operation stops immediately and
    the result returned by that functional is returned as the
    result of the sequential functional.

    The input type should be T; the output type should be U.
    """

    def __init__(self, functionals: Collection[AAISFunctional]):
        """
        Initialize this sequential functional with the given functionals.

        Args:
            functionals: The functionals to apply to the input.
        """

        self._functionals = functionals

    # override
    async def call(self, inputs: T) -> AAISResult[U, AAISThinkingLanguageContent]:
        """
        Apply the functionals in sequence to the input.

        Args:
            inputs: The input to the first functional.

        Returns:
            The result of the last functional.
        """

        x = inputs

        for functional in self._functionals:
            result = await functional.call(x)

            if not result.success:
                return result

            x = result.output

        return AAISResult(
            success=True, output=x, errorMessage=None)
