"""
Biomedical Named Entity Recognition (NER) Module

Extracts biomedical entities (Chemical, Disease, Gene, Protein, Species)
from scientific abstracts using fine-tuned Hugging Face transformer models.
"""

import os
import logging
from typing import List, Dict, Tuple, Optional, Set
import pandas as pd
from transformers import pipeline

from nlp.text_utils import chunk_text
from ingestion.paper_filter import text_contains_keyword

logger = logging.getLogger(__name__)

DEFAULT_NER_MODEL = os.path.join("models", "ner")
DEFAULT_RELEVANT_TYPES = {"Chemical", "Disease", "Gene", "Protein", "Species"}


class BiomedicalNER:
    """
    Wrapper for Transformer-based Named Entity Recognition on biomedical text.
    """

    def __init__(
        self,
        model_path: str = DEFAULT_NER_MODEL,
        device: int = -1
    ):
        self.model_path = model_path
        self.device = device
        
        logger.info(f"Loading NER model from {self.model_path}...")
        self.pipeline = pipeline(
            "token-classification",
            model=self.model_path,
            tokenizer=self.model_path,
            aggregation_strategy="simple",
            device=self.device
        )
        
        self.tokenizer = self.pipeline.tokenizer
        self.max_tokens = min(
            getattr(self.tokenizer, "model_max_length", 512),
            512
        )
        logger.info("NER model loaded successfully")

    def extract(
        self,
        text: str,
        query_keywords: Optional[List[str]] = None,
        min_confidence: float = 0.70,
        relevant_types: Optional[Set[str]] = None
    ) -> List[Dict]:
        """
        Extract named entities from a single text string.
        """
        if not isinstance(text, str) or not text.strip():
            return []

        types_filter = relevant_types or DEFAULT_RELEVANT_TYPES
        chunks = chunk_text(text, self.tokenizer, self.max_tokens)
        entities = []

        for chunk_text_str, chunk_start in chunks:
            try:
                raw_entities = self.pipeline(chunk_text_str)
                for ent in raw_entities:
                    confidence = float(ent.get("score", 0.0))
                    entity_type = ent.get("entity_group", "")
                    entity_text = ent.get("word", "")

                    if confidence < min_confidence:
                        continue

                    if entity_type not in types_filter and not (
                        query_keywords and text_contains_keyword(entity_text, query_keywords)
                    ):
                        continue

                    entities.append({
                        "text": entity_text,
                        "type": entity_type,
                        "confidence": confidence,
                        "start": int(ent.get("start", 0)) + chunk_start,
                        "end": int(ent.get("end", 0)) + chunk_start
                    })
            except Exception as e:
                logger.warning(f"Error processing text chunk: {e}")
                continue

        return entities

    def extract_entities_from_papers(
        self,
        papers_df: pd.DataFrame,
        query_keywords: Optional[List[str]] = None,
        min_confidence: float = 0.70,
        relevant_types: Optional[Set[str]] = None
    ) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Extract entities across a DataFrame of research papers.
        """
        logger.info(f"\n{'='*80}")
        logger.info("STEP 2: Extracting biomedical entities using NER model")
        logger.info(f"{'='*80}\n")

        types_filter = relevant_types or DEFAULT_RELEVANT_TYPES
        entities_list = []
        results = []

        for idx, paper in papers_df.iterrows():
            paper_id = paper.get("paper_id", f"paper_{idx}")
            title = str(paper.get("title", ""))
            abstract = str(paper.get("abstract", ""))
            text = f"{title}. {abstract}"

            if not text.strip():
                continue

            extracted = self.extract(
                text=text,
                query_keywords=query_keywords,
                min_confidence=min_confidence,
                relevant_types=types_filter
            )

            for entity_data in extracted:
                entities_list.append(entity_data)
                results.append({
                    "paper_id": paper_id,
                    "title": title,
                    "publication_date": paper.get("publication_date", ""),
                    "doi": paper.get("doi", ""),
                    "pmid": paper.get("pmid", ""),
                    "entity": entity_data["text"],
                    "entity_type": entity_data["type"],
                    "confidence": entity_data["confidence"],
                    "start": entity_data["start"],
                    "end": entity_data["end"]
                })

            if (idx + 1) % 10 == 0:
                logger.info(f"Processed {idx + 1}/{len(papers_df)} papers")

        entities_df = pd.DataFrame(results)
        logger.info(
            f"Extracted {len(entities_df)} relevant entities from {len(papers_df)} papers "
            f"(confidence>={min_confidence}, types={types_filter})"
        )

        return entities_df, entities_list