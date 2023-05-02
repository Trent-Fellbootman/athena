from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Generic, TypeVar

from ..core import AAISThinkingLanguageContent


inputType = TypeVar('inputType')
outputType = TypeVar('outputType')


class AAISFunctional(ABC, Generic[inputType, outputType]):
    """
    A pure function that takes in some input and generates some output.

    The two generic types denote the input & output types.

    Note that because of the nature of AIs with deep learning backends
    (e.g., LLMs), this function is only pure in the sense that it does not
    produce side effects, but it is not actually a function in the mathematical
    sense, as its output is not deterministic (i.e., calling this "function"
    multiple times with the same input may yield different outputs.)
    """

    @dataclass
    class InvocationResult:
        success: bool
        output: Optional[outputType]
        errorMessage: Optional[AAISThinkingLanguageContent]

    @abstractmethod
    async def call(self, inputs: inputType) -> InvocationResult:
        """
        Call this function with the given arguments on the given backend.
        """
        pass
