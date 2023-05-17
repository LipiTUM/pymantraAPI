from inspect import signature
from typing import Union, Set, Dict, Tuple, Type, List
from django.conf import settings
from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.decorators import api_view

from .utils import process_function_call

from pymantra.database import NetworkGenerator
from pymantra.statics import Edge


url = settings.NEO4J_DB.get('protocol') + "://" + settings.NEO4J_DB.get(
    'host') + ":" + settings.NEO4J_DB.get('port')
auth = (settings.NEO4J_DB.get('user'), settings.NEO4J_DB.get('password'))


# this selection is somewhat based on
# https://hackmd.io/@Chivato/rkAN7Q9NY
# the current selection should at least be enough to avoid entire
# deletions or additions to the database
FORBIDDEN_KWS = [
    "CREATE", "create", "DELETE", "delete", "REMOVE", "remove",
    "WHERE", "where", "RETURN", "return", "limit", "LIMIT",
    "MATCH", "match", " OR ", " or ", " IN ", "in"
]


ARG_TYPES = Union[
    str, Set[str], Dict[str, Set[str]], Dict[str, Set[Edge]], Tuple[str, str],
    List[str], List[List[str]]
]


def _get_dict_set_element(d: Dict[any, Set[any]]):
    key = list(d.keys())[0]
    return next(iter(d[key]))


def _remove_neo4j_kws(query: str) -> str:
    # FIXME: this is very simplistic way => check if neo4j is good enough at
    #        checking itself
    for kw in FORBIDDEN_KWS:
        query = query.replace(kw, "")
    return query


def _clean_node_set(query: Union[Set[str], List[str]]) -> Set[str]:
    return {_remove_neo4j_kws(node) for node in query}


def _clean_node_dict(query: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    return {
        node_type: _clean_node_set(nodes) for node_type, nodes in query.items()
    }


def _clean_edge_dict(query: Dict[str, Set[Edge]]) -> Dict[str, Set[Edge]]:
    cleaned_edges = {}
    for edge_type, edges in query.items():
        cleaned_edges[edge_type] = set()
        for edge in edges:
            cleaned_edges[edge_type].add(
                Edge(_remove_neo4j_kws(edge[0]), _remove_neo4j_kws(edge[1])))
    return cleaned_edges


def _make_safe(query: ARG_TYPES):
    """Remove neo4j keywords from query objects"""
    if not query:
        return query
    if isinstance(query, str):
        return _remove_neo4j_kws(query)
    if isinstance(query, set):
        return _clean_node_set(query)
    if isinstance(query, list):
        return list(_clean_node_set(query))
    if isinstance(query, tuple):
        return tuple((_remove_neo4j_kws(elem) for elem in query))
    if isinstance(query, dict):
        q_elem = _get_dict_set_element(query)
        if isinstance(q_elem, str):
            return _clean_node_dict(query)
        if isinstance(q_elem, (Edge, list)):
            return _clean_edge_dict(query)
    raise TypeError(
        "Internal Error: unexpected type when parsing request for "
        f"NetworkGenerator function: {query} (class: {type(query)})"
    )


def _get_params(func: callable) -> Tuple[Dict[str, Type], Dict[str, Type]]:
    """Get the function parameter types and defaults"""
    func_sig = signature(func)
    annots = {}
    defaults = {}
    for param, param_sig in func_sig.parameters.items():
        if param != "self":
            annots[param] = param_sig.annotation
            if param_sig.default is not param_sig.empty:
                defaults[param] = param_sig.default
    return annots, defaults


def _extract_contractions(
    cont: Dict[Tuple[str, str], Dict[str, str]]
) -> List[List[str]]:
    return [list(key) for key in cont.keys()]


@api_view(['POST'])
def get_subgraph(request: Request):
    """Query API for `pymantra.NetworkGenerator.get_subgraph`"""
    def func(**kwargs):
        with NetworkGenerator(url, auth) as network_generator:
            return network_generator.get_subgraph(**kwargs)

    return process_function_call(
        request, func, _get_params(NetworkGenerator.get_subgraph),
        "get_subgraph", _make_safe, {"organism", "genes", "metabolites"}
    )


@api_view(['POST'])
def get_reaction_subgraph(request: Request):
    """Query API for `pymantra.NetworkGenerator.get_reaction_subgraph`"""
    def func(**kwargs):
        with NetworkGenerator(url, auth) as network_generator:
            return network_generator.get_reaction_subgraph(**kwargs)

    return process_function_call(
        request, func, _get_params(NetworkGenerator.get_reaction_subgraph),
        "get_reaction_subgraph", _make_safe,
        {"organism", "genes", "metabolites", "reaction_organisms"}
    )


@api_view(['POST'])
def as_networkx(request: Request):
    """Query API for `pymantra.NetworkGenerator.as_networkx`"""
    def func(**kwargs):
        if not kwargs.get("nodes") and not kwargs.get("edges"):
            return HttpResponse(
                "Either 'nodes' or 'edges' must be given to run 'as-networkx",
                status=422
            )

        with NetworkGenerator(url, auth) as network_generator:
            graph = network_generator.as_networkx(**kwargs)
            # make edge dict json serializable
            edge_split_str = "___"
            edge_data = {
                f"{src}{edge_split_str}{tgt}": data
                for src, tgt, data in graph.edges(data=True)
            }
            for src, tgt, data in graph.edges(data=True):
                edge_data[f"{src}___{tgt}"] = {
                    k: v if k != "contraction" else _extract_contractions(v)
                    for k, v in data.items()
                }
            # return graph data => conversion into networkx in API-query module
            return {
                "nodes": dict(graph.nodes(data=True)),
                "edges": edge_data,
                "split_str": edge_split_str
            }

    return process_function_call(
        request, func, _get_params(NetworkGenerator.as_networkx),
        "as_networkx", _make_safe, {"nodes", "edges"}
    )
