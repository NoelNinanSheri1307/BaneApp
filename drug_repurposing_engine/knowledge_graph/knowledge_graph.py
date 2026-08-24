import networkx as nx
from knowledge_graph.html_generator import generate_knowledge_graph_html


class BiomedicalKnowledgeGraph:

    def __init__(self):

        self.graph = nx.MultiDiGraph()

    def add_relation(self, relation):

        subject = relation["subject"]
        object_ = relation["object"]

        subject_type = relation.get(
            "subject_type",
            "Unknown"
        )

        object_type = relation.get(
            "object_type",
            "Unknown"
        )

        relationship = relation["relation"]

        confidence = float(
            relation.get(
                "relation_confidence",
                0.0
            )
        )

        self.graph.add_node(
            subject,
            type=subject_type
        )

        self.graph.add_node(
            object_,
            type=object_type
        )

        self.graph.add_edge(
            subject,
            object_,
            relation=relationship,
            confidence=confidence
        )

    def add_relations(self, relations):

        for relation in relations:

            self.add_relation(
                relation
            )

    def get_nodes(self):

        nodes = []

        for node, data in self.graph.nodes(
            data=True
        ):

            nodes.append({
                "name": node,
                "type": data.get(
                    "type",
                    "Unknown"
                )
            })

        return nodes

    def get_edges(self):

        edges = []

        for source, target, data in self.graph.edges(
            data=True
        ):

            edges.append({
                "source": source,
                "target": target,
                "relation": data.get(
                    "relation"
                ),
                "confidence": data.get(
                    "confidence",
                    0.0
                )
            })

        return edges

    def export_graph(
        self,
        output_file="knowledge_graph.html",
        query=None,
        evidence=None,
        stats=None,
        title=None,
        opportunities=None,
        drug_profile=None
    ):
        nodes = self.get_nodes()
        edges = self.get_edges()

        html_content = generate_knowledge_graph_html(
            nodes=nodes,
            edges=edges,
            evidence=evidence,
            stats=stats,
            query=query,
            title=title,
            opportunities=opportunities,
            drug_profile=drug_profile
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_file