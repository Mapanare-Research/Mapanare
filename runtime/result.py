"""Mapanare Result and Option runtime types."""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


class Ok(Generic[T]):
    """Successful Result variant."""

    __match_args__ = ("value",)

    def __init__(self, value: T) -> None:
        self.value = value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def __repr__(self) -> str:
        return f"Ok({self.value!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Ok) and self.value == other.value


class Err(Generic[E]):
    """Error Result variant."""

    __match_args__ = ("value",)

    def __init__(self, value: E) -> None:
        self.value = value

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> E:
        raise RuntimeError(f"Called unwrap on Err: {self.value!r}")

    def __repr__(self) -> str:
        return f"Err({self.value!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Err) and self.value == other.value


# Result type alias
Result = Ok[T] | Err[E]


def unwrap_or_return(result: Ok[T] | Err[E]) -> T:
    """Helper for the ? operator: unwraps Ok or raises _EarlyReturn for Err."""
    if isinstance(result, Ok):
        return result.value
    raise _EarlyReturn(result)


class _EarlyReturn(Exception):
    """Internal exception for error propagation (? operator)."""

    def __init__(self, err: Err[E]) -> None:
        self.err = err
        super().__init__()


class Some(Generic[T]):
    """Some variant for Option pattern matching."""

    __match_args__ = ("value",)

    def __init__(self, value: T) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"Some({self.value!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Some) and self.value == other.value
