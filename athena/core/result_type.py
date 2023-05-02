from dataclasses import dataclass
from typing import TypeVar, Generic, Optional

T = TypeVar('T')
U = TypeVar('U')


@dataclass
class AAISResult(Generic[T, U]):
    """
    Represents the result of an operation.

    Generic type `T` is the type of the returned output of the operation.
    It is possible for the operation to have side effects in addition to
    returning an output of type `T`.
    """

    success: bool
    value: Optional[T]
    errorMessage: Optional[U]
