from typing import Union, List, Dict, Type, Set, Tuple
import json
import urllib
from django.http import JsonResponse, HttpResponse
from rest_framework.request import Request


def _parse_bool(
    request: Request, arg_name: str, func_name: str, default: bool = None
) -> bool:
    try:
        arg_val = request.data.get(arg_name)
        if arg_val is None:
            return default
        else:
            res = arg_val == "True"
        print(f'Processing {func_name}() request')
        return res
    except:
        raise ValueError(
            f'An Error occured while processing func_name() request: Could '
            f'not parse "{arg_name}" input variables.')


def _parse_string(
    request: Request, arg_name: str, func_name: str, check_func: callable
) -> str:
    try:
        res = str(request.data.get(arg_name))
        print(f'Processing {func_name}() request')
        return check_func(res)
    except:
        raise ValueError(
            f'An Error occured while processing {func_name}() request: Could '
            f'not parse "{arg_name}" input variables.')


def _parse_list_or_string(
    request: Request, arg_name: str, func_name: str, check_func: callable
) -> Union[str, List[str]]:
    try:
        results = list(json.loads(
            request.data.getlist(arg_name)[0].replace('\'',
                                                              '\"')).items())
        if len(results) == 1:
            results = results[0]
        print(f'Processing {arg_name}() request')
        return check_func(results)
    except:
        raise ValueError(
            f'An Error occured while processing {func_name}() request: Could '
            f'not parse "{arg_name}" input variables.')


def _parse_dict(
    request: Request, arg_name: str, func_name: str, check_func: callable
) -> Dict[str, List[str]]:
    try:
        res = {}
        for x in request.data.getlist(arg_name):
            res.update(json.loads(x.replace('\'', '\"')))
        print(f'Processing {func_name}() request')
        print(res)
        return check_func(res)
    except:
        raise ValueError(
            f'An Error occured while processing {func_name}() request: Could '
            f'not parse "{arg_name}" input variables.'
        )


def _parse_iterable(
    request: Request, arg_name: str, func_name: str, check_func: callable,
    default: any = None, is_optional: bool = False
):
    try:
        results = request.data.getlist(arg_name, None)
        if not results and is_optional:
            return default

        print(f'Processing {func_name}() request')
        return check_func(results)
    except:
        raise ValueError(
            f'An Error occured while processing {func_name}() request: Could '
            f'not parse "{arg_name}" input variables.')


def parse_parameters(
    request: Request, parameters: Tuple[Dict[str, Type], Dict[str, Type]],
    view_name: str, check_func: callable, check_vars: Set[str]
) -> Dict[str, any]:
    def empty_check(q):
        return q
    # parsing parameters
    # this function needs to be adapted if there are new types added
    parsed_params = {}
    for param, param_type in parameters[0].items():
        print(f"Parsing {param} as {param_type}")
        if param in check_vars:
            param_check = check_func
        else:
            param_check = empty_check
        try:
            match param_type.__name__:
                case "bool":
                    parsed_params[param] = _parse_bool(
                        request, param, view_name, parameters[1].get(param))
                case "str":
                    parsed_params[param] = _parse_string(
                        request, param, view_name, param_check)
                case "Union":
                    parsed_params[param] = _parse_list_or_string(
                        request, param, view_name, param_check)
                case "Dict":
                    parsed_params[param] = _parse_dict(
                        request, param, view_name, param_check)
                case _:
                    # this defaults to iterables => add more case if anything
                    # changes
                    parsed_params[param] = _parse_iterable(
                        request, param, view_name, param_check,
                        parameters[1].get(param), param in parameters[1].keys()
                    )
        except:
            raise ValueError(
                f'An Error occured while processing {view_name}() request: '
                f'Could not parse "{param}" input variable.'
            )
    return parsed_params


def process_function_call(
    request: Request, func: callable,
    parameters: Tuple[Dict[str, Type], Dict[str, Type]], name: str,
    check_func: callable, check_vars: Set[str]
):
    print(f'New {name}() request received.')
    print(f'Processing {name}() request...')
    print(f'Processing {name}() request: Parsing input values...')

    # TODO: check for parameter constraints and raise meaningful errors and
    #       status codes
    # TODO: check pymantra source code for parametrized queries only to protect
    #       from injections
    params = parse_parameters(
        request, parameters, name, check_func, check_vars)

    print(
        f'Processing {name}() request: Parsing input values successful.')

    # calculate results
    print(
        f'Processing {name}() request: Calculating subgraph with pymantra...')

    results = func(**params)
    # this means an error occurred
    if isinstance(results, HttpResponse):
        return results

    print(
        f'Processing {name}() request: Calculating results with pymantra '
        'successful.'
    )
    print(f'Processing {name}() request: Calculated results.')

    print(
        f'Processing {name}() request: Encoded calculated results as JSON'
    )
    print(f'Processing {name}() request finished.')
    return JsonResponse(serialize_to_dict(results))


def decode_url_params(params: str) -> dict:
    return urllib.parse.parse_qs(params, keep_blank_values=True)


def encode_url_params(params: dict) -> str:
    return urllib.parse.urlencode(params, doseq=True)


def serialize_to_json(obj: any) -> str:
    return json.dumps(serialize_to_dict(obj))


def serialize_to_dict(obj: any) -> dict:
    match obj:
        case dict():
            data = {}
            for key, value in obj.items():
                data[key] = serialize_to_dict(value)
            return data
        case list() | tuple():
            return [serialize_to_dict(x) for x in obj]
        case set():
            return serialize_to_dict(list(obj))
        case object(__dict__=_):
            data = {}
            for key, value in obj.__dict__.items():
                if not key.startswith("_"):
                    data[key] = serialize_to_dict(value)
            return data
        case _:
            return obj
