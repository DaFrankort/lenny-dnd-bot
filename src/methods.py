def when(condition: bool, value_on_true: any, value_on_false: any) -> any:
    """Wrapper method for a ternary statement, for readability"""
    return value_on_true if condition else value_on_false
