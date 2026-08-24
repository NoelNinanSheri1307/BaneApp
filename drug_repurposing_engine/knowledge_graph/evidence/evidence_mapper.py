class EvidenceMapper:

    def map_relation(self, relation, paper):

        return {
            "subject": relation["subject"],
            "subject_type": relation["subject_type"],
            "relation": relation["relation"],
            "object": relation["object"],
            "object_type": relation["object_type"],
            "relation_confidence": float(
                relation.get("relation_confidence", 0.0)
            ),
            "paper_id": paper.get("paper_id"),
            "title": paper.get("title"),
            "publication_date": paper.get("publication_date"),
            "doi": paper.get("doi"),
            "pmid": paper.get("pmid"),
            "evidence_text": relation.get("sentence", "")
        }

    def map_relations(self, relations, paper):

        return [
            self.map_relation(relation, paper)
            for relation in relations
        ]

    def group_by_relation(self, evidence):

        grouped = {}

        for item in evidence:

            key = (
                item["subject"],
                item["relation"],
                item["object"]
            )

            if key not in grouped:
                grouped[key] = []

            grouped[key].append(item)

        return grouped