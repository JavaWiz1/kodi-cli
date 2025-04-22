# === Validation routines =================================================
def is_integer(token: str) -> bool:
    """Return true if string is an integer"""
    is_int = True
    try:
        int(token)
    except (ValueError, TypeError):
        is_int = False
    return is_int

def is_boolean(token: str) -> bool:
    """Return true if string is a boolean"""
    is_bool_str = False
    if token in ["True", "true", "False", "false"]:
        is_bool_str = True
    return is_bool_str

def is_list(token: str) -> bool:
    """Return true if string represents a list"""
    if token.startswith("[") and token.endswith("]"):
        return True
    return False

def is_dict(token: str) -> bool:
    """Return true if string represents a dictionary"""
    if token.startswith("{") and token.endswith("}"):
        return True
    return False

def make_list_from_string(token: str) -> list:
    """Translate list formatted string to a list obj"""
    text = token[1:-1]
    return text.split(",")

def make_dict_from_string(token: str) -> dict:
    """Translate dict formatted string to a dict obj"""
    text = token[1:-1]
    entry_list = text.split(",")
    result_dict = {}
    for entry in entry_list:
        key_val = entry.split(":", 1)
        key = key_val[0].strip()
        value = key_val[1].strip()
        if is_integer(value):
            value=int(value)
        elif is_boolean(value):
            value = value in ['True', 'true']
        result_dict[key] = value

    return result_dict
