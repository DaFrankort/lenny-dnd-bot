def listify(value: any) -> list[any]:
    if isinstance(value, list):
        return value
    return [value]