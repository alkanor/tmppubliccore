from typing import Dict, Any, List


# quick & simple replacement for the pyjq basics of attribute chained together to search in a dict
# because pyjq does not install properly on Windows
def check_dict_against_attributes(dict_or_final: Dict[str, Any] | Any, parts: List[str]):
    if not parts:
        return True, dict_or_final
    else:
        if not isinstance(dict_or_final, dict) or parts[0] not in dict_or_final:
            return False, parts[0]
        else:
            return check_dict_against_attributes(dict_or_final[parts[0]], parts[1:])


def check_dict_against_attributes_string(dict_or_final: Dict[str, Any] | Any, attributes_string: str):
    split = attributes_string.split('.')
    return check_dict_against_attributes(dict_or_final, split[1:] if split[0] == '' else split)

def set_dict_against_attributes_string(dict_or_final: Dict[str, Any] | Any, attributes_string: str, value: Any):
    split = attributes_string.split('.')
    it = dict_or_final
    for s in (split[1:] if split[0] == '' else split)[:-1]:  # the latest one is the value to set
        it = it.setdefault(s, {})
    it[split[-1]] = value
