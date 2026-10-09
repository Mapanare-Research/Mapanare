"""Type-directed ownership policies shared by lowering and emission."""

from mapanare.types import TypeKind


def map_copies_inputs(key: TypeKind, value: TypeKind) -> bool:
    """Only supported keys and resource-free/String values have a built-in policy."""
    return key in (TypeKind.INT, TypeKind.FLOAT, TypeKind.STRING) and value in (
        TypeKind.INT,
        TypeKind.FLOAT,
        TypeKind.BOOL,
        TypeKind.CHAR,
        TypeKind.STRING,
    )


def list_copies_inputs(elem: TypeKind) -> bool:
    """Element types with a built-in owned-list copy/drop policy.

    String elements get independent copies; List elements retain/release the
    inner COW buffer, which carries its own element policy.
    """
    return elem in (TypeKind.STRING, TypeKind.LIST)


def list_owned_constructor(elem: TypeKind) -> str | None:
    """Runtime constructor for owned lists, or None for the raw contract."""
    if elem == TypeKind.STRING:
        return "__mn_list_str_new_owned"
    if elem == TypeKind.LIST:
        return "__mn_list_list_new_owned"
    return None
