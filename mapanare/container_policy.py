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
