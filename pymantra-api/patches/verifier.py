import warnings
from typing import Union, Tuple, Set, Dict
from neo4j.graph import Node
from base import Neo4jBaseConnector
from statics import (
    Edge,
    NODE_TYPES, EDGE_TYPES,
    NODE_TYPES_BY_EDGE
)


class Verifier(Neo4jBaseConnector):
    """
    Auxiliary class to verify the correctness of the database.
    Currently, the requirements for correctness are:

    * only one label per node/relationship specifying the node/relationship
      type
    * node labels need to be given as property named 'nodeLabel'
    * every node label and id is unique across all node types
    * every relationship is unique **per type**
    * relationship types must contain the correct source and target node types
      as specified by `utils.NODE_TYPES_BY_EDGE`
    """

    _nodes_passed_: bool

    def __init__(
        self, uri: str, auth: Union[Tuple[str, str], None] = None, **kwargs
    ):
        """
        Parameters
        ----------
        uri: str
            URI to connect to. Usually something like 'bolt://127.0.0.7:7687'

        auth: 2-tuple, Optional
            User credentials for the database. First element is the username,
            second the corresponding password. For more details see the
            neo4j.GraphDatabase.driver API documentation

        kwargs:
            Keyword arguments to pass to neo4j.GraphDatabase.driver

        Raises
        ------
        ConnectionError
            If database is not reachable with the given parameters
        """
        super(Verifier, self).__init__(uri, auth, **kwargs)
        self._nodes_passed_ = False

    def _report_false(self, message: str, nodes: bool = False) -> bool:
        print("\033[91m============ ", message, " ============\033[0m")
        if nodes:
            self._nodes_passed_ = False
        return False

    @staticmethod
    def _get_node_elements(node: Node) -> Tuple[int, str, str]:
        return node.id, next(iter(node.labels)), node['nodeLabel']

    def _get_node_by_id(self, id_: int) -> Node:
        return self.session.run(
            f"MATCH (n) WHERE ID(n) = {id_} RETURN n").value()[0]

    def verify_nodes(self) -> \
            Tuple[bool, Union[Set[int], None], Union[Dict[int, str], None]]:
        """
        Verifying correctness of all relationships in the database.
        This function requires

        Returns
        -------
        Tuple[bool, Union[Set[int], None], Union[Dict[int, str], None]]

            3-Tuple where:

            * The first element is a :obj:`bool` indicating whether all nodes
              passed (True) of whether any node failed (False)

            * The second element is a :obj:`set` containing all node ids found
              in the database as :obj:`int`.

            * The third element :obj:`dict` mapping each node id (:obj:`int`)
              to its corresponding node label (:obj:`str`)

            The second and third elements serve as input to
            `verify_relationships`
        """
        nodes = [
            node for node_list in
            self.session.run("MATCH (n) RETURN n").values()
            for node in node_list
        ]
        node_ids = set()
        node_labels = set()
        node_types = set()
        id_label_map = {}
        for neo4j_node in nodes:
            labels = neo4j_node.labels
            node_id = neo4j_node.id
            node_label = neo4j_node.get('nodeLabel')
            if not node_label:
                return self._report_false(
                    f"Node with ID {node_id} does not have a node label "
                    "specified with 'nodeLabel'"
                ), None, None
            # checking if node has more than one type (i.e. label)
            if len(labels) != 1:
                return self._report_false(
                    f"{node_label} (ID: {node_id}) has {len(labels)} "
                    "types (neo4j 'labels'), but only 1 is allowed"
                ), None, None
            # checking if node type is known
            else:
                node_type = next(iter(labels))
                if node_type not in NODE_TYPES:
                    return self._report_false(
                        f"{node_type} is not a valid node type. "
                        f"Please use only these types: {NODE_TYPES}"
                    ), None, None
                node_types.add(node_type)
            # checking node id uniqueness
            if node_id in node_ids:
                return self._report_false(
                    f"ID {node_id} found multiple times, while unique IDs "
                    f"are required"
                ), None, None
            node_ids.add(node_id)
            # checking node label uniqueness
            if node_label in node_labels:
                return self._report_false(
                    f"nodeLabel {node_label} found multiple times, while "
                    f"unique nodeLabels are required"
                ), None, None
            node_labels.add(node_label)
            id_label_map[node_id] = node_label
        # checking if all node types are present if not a warning will be
        # printed since this is not a hard requirement
        missing_node_types = {node_type for node_type in NODE_TYPES
                              if node_type not in node_types}
        if missing_node_types:
            warnings.warn(
                f"Not all node types are presented in the database. "
                f"Missing node types: {missing_node_types}"
            )
        self._nodes_passed_ = True
        return True, node_ids, id_label_map

    def verify_relationships(
        self, node_ids: Set[int], id_label_map: Dict[int, str]
    ) -> bool:
        """
        Verifying correctness of all relationships in the database.
        This function requires

        Parameters
        ----------
        node_ids : Set[int]
            Set of all node ids in the database

        id_label_map: Dict[int, str]
            Map from node id to node label for all nodes in the database

        Returns
        -------
        bool
            True if every relationship meets the required conditions,
            else False.
        """
        if not self._nodes_passed_:
            raise ValueError(
                "Nodes need to pass verification before. "
                "Please call `verify_nodes` first or correct any errors "
                "found by it."
            )
        relations = [
            edge for edge_list in
            self.session.run("MATCH (s)-[n]-(t) RETURN n").values()
            for edge in edge_list
        ]
        edge_types = set()
        edges = {edge_type: set() for edge_type in EDGE_TYPES}
        for edge in relations:
            edge_type = edge.type
            # edge_id = edge.id
            src, tgt = edge.nodes
            src_id, src_type, src_label = self._get_node_elements(
                self._get_node_by_id(src.id))
            tgt_id, tgt_type, tgt_label = self._get_node_elements(
                self._get_node_by_id(tgt.id))
            # === properties === #
            # edge type correctness
            if edge_type not in EDGE_TYPES:
                return self._report_false(
                    f"{edge_type} is not a valid edge type. "
                    f"Please use only these types: {EDGE_TYPES}"
                )
            edge_types.add(edge_type)
            # edge uniqueness per type
            edge_ = Edge(src_label, tgt_label)
            if edge_ in edges[edge_type]:
                return self._report_false(
                    f"{edge_} found multiple times for {edge_type} relations, "
                    f"while uniqueness is required"
                )
            # === edge nodes === #
            if src_id not in node_ids:
                return self._report_false(
                    f"Source node id {src_id} not found in node ids"
                )
            if id_label_map[src_id] != src_label:
                return self._report_false(
                    "Incorrect source node label, expected "
                    f"{id_label_map[src]} but got {src_label}"
                )
            if tgt_id not in node_ids:
                return self._report_false(
                    f"Target node id {tgt_id} not found in node ids"
                )
            if id_label_map[tgt_id] != tgt_label:
                return self._report_false(
                    "Incorrect target node label, expected "
                    f"{id_label_map[tgt]} but got {tgt_label}"
                )
            # === edge type vs node types === #
            if NODE_TYPES_BY_EDGE[edge_type] != (src_type, tgt_type):
                return self._report_false(
                    f"Incorrect node types for edge type found. "
                    f"Expected {NODE_TYPES_BY_EDGE[edge_type]}, bot got "
                    f"{(src_type, tgt_type)}"
                )
        missing_edge_types = {edge_type for edge_type in EDGE_TYPES
                              if edge_type not in edge_types}
        if missing_edge_types:
            warnings.warn(
                f"Not all edge types are presented in the database. "
                f"Missing edge types: {missing_edge_types}"
            )
        return True

    def verify_correctness(self) -> bool:
        """
        Checking whether the graph fulfills all requirements of correctness.
        For the list of requirements see `Verifier` class documentation.

        Returns
        -------
        bool
            True if all conditions are met. Otherwise, a message is printed
            stating the type and position of the error before returning False.
        """
        print("Verifying nodes...")
        # nodes
        node_verification, node_ids, id_label_map = self.verify_nodes()
        if not node_verification:
            print("\n\033[91m============ database Node Verification Failed "
                  "============\033[0m\n")
            return node_verification
        print("\033[92m=== Nodes passed ===\033[0m\n")
        # edges
        print("Verifying edges...")
        edge_verification = self.verify_relationships(node_ids, id_label_map)
        if not edge_verification:
            print("\n\033[91m============ database Relationship Verification "
                  "Failed ============\033[0m\n")
            return edge_verification
        print("\033[92m=== Edges passed ===\033[0m\n")
        print("\033[92m============ database Graph Verification Successful "
              "============\033[0m\n")
        return True
