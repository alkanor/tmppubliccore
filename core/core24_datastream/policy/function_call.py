from functools import wraps
from typing import List, Iterable
import enum


class CallingContractArguments(enum.Enum):
    OneOrNone = enum.auto()  # this case
    One = enum.auto()        # and this case, lead to a unique value at most
    OneOrMore = enum.auto()  # this case lead to a unique value or a list
    ExactlyX = enum.auto()   # this case (0 and 1 forbidden as already represented)
    MoreThanX = enum.auto()  # and this case, lead to a list of values
    LessThanX = enum.auto()  # this case can lead to None, a unique or a list
    List = enum.auto()       # this case is to create a smart list: either a list of X,


def _check_and_format(calling_contract_arguments: CallingContractArguments, values_list: List, type_error: type):
    n = len(values_list)
    error_message = f"Bad condition {calling_contract_arguments} for {n} of type {type_error}"
    match calling_contract_arguments[0]:
        case CallingContractArguments.OneOrNone:
            assert n <= 1, error_message
            return values_list[0] if n == 1 else None
        case CallingContractArguments.One:
            assert n == 1, error_message
            return values_list[0]
        case CallingContractArguments.OneOrMore:
            assert n >= 1, error_message
            if n == 1:
                return values_list[0]
        case CallingContractArguments.ExactlyX:
            assert n == calling_contract_arguments[1], error_message
        case CallingContractArguments.MoreThanX:
            assert n >= calling_contract_arguments[1], error_message
        case CallingContractArguments.LessThanX:
            assert n <= calling_contract_arguments[1], error_message
            return values_list[0] if n == 1 else None if n == 0 else values_list
        case _:
            raise NotImplementedError
    return values_list

def consume_arguments(rules_dict, permit_multiple_types: bool = False, is_method: bool = False):
    per_type = {}
    cannot_be_none = set()
    for key, item in rules_dict.items():
        if item[1] not in [CallingContractArguments.OneOrNone, CallingContractArguments.LessThanX]:
            cannot_be_none.add(item[0])
        if item[1] == CallingContractArguments.ExactlyX:
            assert item[2] > 1, 'CallingContractArguments.ExactlyX cannot be compared to 1 or 0, already in One(orNone)'
        if item[0] not in per_type:
            per_type[item[0]] = [(key, item)]
        else:
            assert permit_multiple_types, f"Multiple types {item[0]} not permitted in consume_arguments" \
                                          f" (permit_multiple_types = False)"
            per_type[item[0]].append((key, item))

    all_types = list(per_type.keys())
    def decorator(f):
        @wraps(f)
        def sub(*args, **argv):
            per_type_when_called = {}
            final_argv = {}
            for arg in args[1:]:  # argument 1 is either instance or class (no static method allowed yet to use this)
                if type(arg) not in per_type:
                    raise Exception(f"Not expecting positional argument with type {type(arg)} (possible: {all_types})")
                else:
                    per_type_when_called.setdefault(type(arg), []).append(arg)
            for k in argv:
                arg = argv[k]
                if type(arg) in per_type:
                    per_type_when_called.setdefault(type(arg), []).append(arg)
                else:
                    final_argv[k] = argv[k]
            for _type, value_list in per_type_when_called.items():
                if len(per_type[_type]) == 1:  # case where there can be many of the same type, as unique
                    name, type_and_constraint = per_type[_type][0]
                    print(name, type_and_constraint)
                    out = _check_and_format(type_and_constraint[1:], value_list, _type)
                    final_argv[name] = out
                else:
                    if len(value_list) > len(per_type[_type]):
                        raise Exception(f"Not expecting more than {len(per_type[_type])} values of type {_type}")
                    for value, name_type_contract in zip(value_list, per_type[_type]):
                        final_argv[name_type_contract[0]] = value
            return f(*[args[0]] if is_method else [], **final_argv)
        return sub
    return decorator


def consume_arguments_method(*args, **argv):
    return consume_arguments(is_method=True, *args, **argv)