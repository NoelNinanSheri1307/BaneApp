#!/usr/bin/env python3
"""
Unified Data Flow Pipeline for Drug Repurposing Engine

This orchestrator coordinates the modular stages:
1. Literature Retrieval (Europe PMC)
2. Relevance Filtering (Query Keywords)
3. Named Entity Recognition (BiomedicalNER)
4. Relation Extraction (RelationExtractor)
5. Knowledge Graph & Evidence Mapping (BiomedicalKnowledgeGraph + EvidenceMapper)
6. Results Export (JSON, CSV, HTML, TXT)
"""

import os
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd

# Modular component imports
from ingestion.europe_pmc import EuropePMCClient
from ingestion.paper_filter import (
    parse_query_keywords,
    filter_papers_by_relevance,
    text_contains_keyword
)
from nlp.ner import BiomedicalNER
from nlp.relation_extraction import RelationExtractor
from knowledge_graph.knowledge_graph import BiomedicalKnowledgeGraph
from knowledge_graph.evidence.evidence_mapper import EvidenceMapper
from knowledge_graph.exporter import export_pipeline_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DrugRepurposingPipeline:
    """
    Main orchestration class for the complete biomedical NLP pipeline.
    """

    def __init__(
        self,
        ner_model_path: str = "models/ner",
        relation_model_path: str = "models/relation",
        device: int = -1,
        cache_dir: str = "pipeline_cache",
        output_dir: str = "results"
    ):
        self.device = device
        self.cache_dir = cache_dir or "pipeline_cache"
        self.output_dir = output_dir or "results"

        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info("Initializing Drug Repurposing Pipeline components...")

        # Initialize modular workers
        self.pmc_client = EuropePMCClient()
        self.ner = BiomedicalNER(model_path=ner_model_path, device=device)
        self.relation_extractor = RelationExtractor(model_name=relation_model_path, device=device)
        self.knowledge_graph = BiomedicalKnowledgeGraph()
        self.evidence_mapper = EvidenceMapper()

        self._query_keywords: List[str] = []
        logger.info("Pipeline initialized successfully.")

    def step_1_retrieve_papers(self, query: str, max_results: int = 50) -> pd.DataFrame:
        """STEP 1: Retrieve research papers from Europe PMC API."""
        logger.info(f"\n{'='*80}\nSTEP 1: Retrieving papers from Europe PMC API (Query: '{query}')\n{'='*80}\n")
        papers_df = self.pmc_client.search(query=query, page_size=min(max_results, 1000))
        logger.info(f"Retrieved {len(papers_df)} papers")
        
        papers_file = os.path.join(self.cache_dir, "papers.csv")
        papers_df.to_csv(papers_file, index=False)
        return papers_df

    def step_1b_filter_papers(self, papers_df: pd.DataFrame, query: str, top_n: int = 20) -> pd.DataFrame:
        """STEP 1b: Rank and filter retrieved papers by query keyword relevance."""
        return filter_papers_by_relevance(papers_df, query=query, top_n=top_n)

    def step_2_extract_entities(self, papers_df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """STEP 2: Run NER on papers to extract biomedical entities."""
        entities_df, entities_list = self.ner.extract_entities_from_papers(
            papers_df=papers_df,
            query_keywords=self._query_keywords,
            min_confidence=0.70
        )
        entities_file = os.path.join(self.cache_dir, "entities.csv")
        entities_df.to_csv(entities_file, index=False)
        return entities_df, entities_list

    def step_3_extract_relations(
        self,
        papers_df: pd.DataFrame,
        entities_df: pd.DataFrame,
        max_pairs_per_paper: int = 15
    ) -> Tuple[pd.DataFrame, List[Dict]]:
        """STEP 3: Extract relations between cross-type entity pairs in the same sentence."""
        relations_df, relations_list = self.relation_extractor.extract_relations_from_papers(
            papers_df=papers_df,
            entities_df=entities_df,
            query_keywords=self._query_keywords,
            max_pairs_per_paper=max_pairs_per_paper,
            min_confidence=0.60,
            batch_size=32
        )
        relations_file = os.path.join(self.cache_dir, "relations.csv")
        relations_df.to_csv(relations_file, index=False)
        return relations_df, relations_list

    def step_4_build_knowledge_graph(
        self,
        relations_df: pd.DataFrame,
        papers_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """STEP 4: Build Knowledge Graph with query-relevance post-filtering & evidence mapping."""
        logger.info(f"\n{'='*80}\nSTEP 4: Building Knowledge Graph with Evidence Mapping\n{'='*80}\n")

        paper_lookup = {row.get("paper_id"): row for _, row in papers_df.iterrows()}
        evidence_list = []
        skipped_irrelevant = 0

        for idx, relation_row in relations_df.iterrows():
            paper_id = relation_row["paper_id"]
            paper = paper_lookup.get(paper_id)
            if paper is None or (isinstance(paper, pd.Series) and paper.empty):
                continue

            relation = {
                "subject": relation_row.get("subject", ""),
                "subject_type": relation_row.get("subject_type", ""),
                "subject_confidence": float(relation_row.get("subject_confidence", 0.0)),
                "relation": relation_row.get("relation", ""),
                "relation_confidence": float(relation_row.get("relation_confidence", 0.0)),
                "object": relation_row.get("object", ""),
                "object_type": relation_row.get("object_type", ""),
                "object_confidence": float(relation_row.get("object_confidence", 0.0)),
                "sentence": relation_row.get("sentence", "")
            }

            # Post-filter: keep relation if subject or object matches a query keyword
            if self._query_keywords:
                subj_match = text_contains_keyword(relation["subject"], self._query_keywords)
                obj_match = text_contains_keyword(relation["object"], self._query_keywords)
                if not (subj_match or obj_match):
                    skipped_irrelevant += 1
                    continue

            evidence = self.evidence_mapper.map_relation(relation, paper)
            evidence_list.append(evidence)
            self.knowledge_graph.add_relation(relation)

        logger.info(
            f"Knowledge Graph: {len(evidence_list)} query-relevant relations mapped "
            f"({skipped_irrelevant} unrelated dropped)."
        )

        evidence_file = os.path.join(self.cache_dir, "evidence_map.csv")
        pd.DataFrame(evidence_list).to_csv(evidence_file, index=False)

        nodes = self.knowledge_graph.get_nodes()
        edges = self.knowledge_graph.get_edges()
        grouped_evidence = self.evidence_mapper.group_by_relation(evidence_list)

        return {
            "nodes": nodes,
            "edges": edges,
            "evidence": evidence_list,
            "grouped_evidence": grouped_evidence
        }

    def export_results(self, query: str, graph_data: Dict[str, Any]) -> Dict[str, str]:
        """Export all pipeline results (CSV, JSON, HTML, Summary)."""
        return export_pipeline_results(
            query=query,
            graph_data=graph_data,
            output_dir=self.output_dir,
            knowledge_graph=self.knowledge_graph
        )

    def run(self, query: str, max_results: int = 50) -> Dict[str, str]:
        """Execute the complete end-to-end modular pipeline."""
        logger.info("\n" + "=" * 80)
        logger.info("STARTING DRUG REPURPOSING PIPELINE")
        logger.info("=" * 80 + "\n")

        self._query_keywords = parse_query_keywords(query)
        logger.info(f"Query keywords: {self._query_keywords}")

        try:
            # 1. Retrieve & Filter
            papers_df = self.step_1_retrieve_papers(query=query, max_results=max_results)
            if len(papers_df) == 0:
                logger.error("No papers retrieved. Pipeline terminated.")
                return {}

            papers_df = self.step_1b_filter_papers(papers_df, query=query)

            # 2. Extract Entities
            entities_df, _ = self.step_2_extract_entities(papers_df)
            if len(entities_df) == 0:
                logger.error("No entities extracted. Pipeline terminated.")
                return {}

            # 3. Extract Relations
            relations_df, _ = self.step_3_extract_relations(papers_df, entities_df)
            if len(relations_df) == 0:
                logger.warning("No relations extracted. Continuing with empty knowledge graph...")

            # 4. Build KG & Map Evidence
            graph_data = self.step_4_build_knowledge_graph(relations_df, papers_df)

            # 5. Export Output Files
            output_files = self.export_results(query, graph_data)

            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
            logger.info("=" * 80 + "\n")

            return output_files

        except Exception as e:
            logger.error(f"\nPIPELINE EXECUTION FAILED: {e}")
            raise


def main():
    """CLI entrypoint for running the pipeline directly."""
    import argparse

    parser = argparse.ArgumentParser(description="Drug Repurposing Engine Pipeline")
    parser.add_argument("query", type=str, help="Biomedical search query")
    parser.add_argument("--max-results", type=int, default=50, help="Max papers to retrieve (default: 50)")
    parser.add_argument("--ner-model", type=str, default="models/ner", help="Path to NER model")
    parser.add_argument("--relation-model", type=str, default="models/relation", help="Path to Relation model")
    parser.add_argument("--output-dir", type=str, default="results", help="Output directory")
    parser.add_argument("--device", type=int, default=-1, help="GPU device ID (-1 for CPU)")

    args = parser.parse_args()

    pipeline = DrugRepurposingPipeline(
        ner_model_path=args.ner_model,
        relation_model_path=args.relation_model,
        device=args.device,
        output_dir=args.output_dir
    )

    output_files = pipeline.run(query=args.query, max_results=args.max_results)
    if output_files:
        print("\n" + "=" * 80 + "\nPIPELINE RESULTS\n" + "=" * 80 + "\n")
        for file_type, file_path in output_files.items():
            print(f"[+] {file_type}: {file_path}")


if __name__ == "__main__":
    main()
