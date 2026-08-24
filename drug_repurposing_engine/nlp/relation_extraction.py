import os
import logging
from itertools import combinations
from typing import List, Dict, Tuple, Optional
import pandas as pd
from transformers import pipeline

from nlp.text_utils import split_sentences
from ingestion.paper_filter import text_contains_keyword

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.path.join("models", "relation")
REMOTE_FALLBACK_MODEL = "Glasgow-AI4BioMed/synthetic_relex"


class RelationExtractor:

    def __init__(
        self,
        model_name=DEFAULT_MODEL,
        device=-1
    ):
        resolved_model = model_name or DEFAULT_MODEL

        if not os.path.exists(resolved_model):
            if os.path.exists(DEFAULT_MODEL):
                resolved_model = DEFAULT_MODEL
            else:
                resolved_model = REMOTE_FALLBACK_MODEL

        self.model_name = resolved_model

        self.classifier = pipeline(
            "text-classification",
            model=self.model_name,
            tokenizer=self.model_name,
            device=device,
            top_k=None
        )
        
        self.tokenizer = self.classifier.tokenizer
        self.max_tokens = 512

    def mark_entities(
        self,
        text,
        entity1,
        entity2
    ):
        e1 = dict(entity1)
        e2 = dict(entity2)

        if e1["start"] > e2["start"]:
            e1, e2 = e2, e1

        if e1["end"] > e2["start"]:
            raise ValueError("Entities overlap")

        return (
            text[:e1["start"]]
            + "[E1]"
            + text[e1["start"]:e1["end"]]
            + "[/E1]"
            + text[e1["end"]:e2["start"]]
            + "[E2]"
            + text[e2["start"]:e2["end"]]
            + "[/E2]"
            + text[e2["end"]:]
        )

    def _truncate_text_around_entities(
        self,
        text,
        entity1,
        entity2,
        max_length=512,
        context_size=50
    ):
        """
        Truncate text to fit within model limits while keeping entities.
        """
        try:
            e1_start = min(entity1["start"], entity2["start"])
            e2_end = max(entity1["end"], entity2["end"])
            
            reserved_tokens = 20
            available_for_context = max_length - reserved_tokens
            
            if available_for_context < 50:
                context_before = 10
                context_after = 10
            else:
                context_before = min(context_size, available_for_context // 3)
                context_after = min(context_size, available_for_context // 3)
            
            start = max(0, e1_start - context_before)
            end = min(len(text), e2_end + context_after)
            
            truncated_text = text[start:end]
            
            try:
                tokens = self.tokenizer.encode(truncated_text, add_special_tokens=True)
                if len(tokens) > max_length - reserved_tokens:
                    truncated_text = self.tokenizer.decode(
                        tokens[:max_length - reserved_tokens],
                        skip_special_tokens=True
                    )
            except Exception:
                pass
            
            adjusted_entity1 = dict(entity1)
            adjusted_entity2 = dict(entity2)
            
            adjusted_entity1["start"] = max(0, entity1["start"] - start)
            adjusted_entity1["end"] = min(len(truncated_text), max(0, entity1["end"] - start))
            adjusted_entity2["start"] = max(0, entity2["start"] - start)
            adjusted_entity2["end"] = min(len(truncated_text), max(0, entity2["end"] - start))
            
            return truncated_text, adjusted_entity1, adjusted_entity2
        except Exception:
            e_min_start = min(entity1["start"], entity2["start"])
            e_max_end = max(entity1["end"], entity2["end"])
            context = 20
            
            start = max(0, e_min_start - context)
            end = min(len(text), e_max_end + context)
            truncated_text = text[start:end]
            
            adjusted_entity1 = dict(entity1)
            adjusted_entity2 = dict(entity2)
            
            adjusted_entity1["start"] = max(0, entity1["start"] - start)
            adjusted_entity1["end"] = min(len(truncated_text), max(0, entity1["end"] - start))
            adjusted_entity2["start"] = max(0, entity2["start"] - start)
            adjusted_entity2["end"] = min(len(truncated_text), max(0, entity2["end"] - start))
            
            return truncated_text, adjusted_entity1, adjusted_entity2

    def predict_batch(self, marked_texts: List[str], batch_size: int = 32) -> List[List[Dict]]:
        """
        Batched prediction for high-throughput inference across multiple marked pairs.
        """
        if not marked_texts:
            return []

        clean_texts = []
        for text in marked_texts:
            if len(text) > 500:
                text = text[:500]
            clean_texts.append(text)

        try:
            raw_outputs = self.classifier(
                clean_texts,
                batch_size=batch_size,
                truncation=True,
                max_length=self.max_tokens
            )
            # Normalize output structure
            results = []
            for out in raw_outputs:
                if isinstance(out, list):
                    sorted_out = sorted(out, key=lambda x: x.get("score", 0.0), reverse=True)
                    results.append(sorted_out)
                elif isinstance(out, dict):
                    results.append([out])
                else:
                    results.append([])
            return results
        except Exception as e:
            logger.warning(f"Batched prediction error: {e}. Falling back to sequential.")
            # Fallback to single predictions
            results = []
            for t in clean_texts:
                try:
                    out = self.classifier(t, truncation=True, max_length=self.max_tokens)
                    if isinstance(out, list) and out and isinstance(out[0], list):
                        results.append(sorted(out[0], key=lambda x: x.get("score", 0.0), reverse=True))
                    elif isinstance(out, list):
                        results.append(sorted(out, key=lambda x: x.get("score", 0.0), reverse=True))
                    else:
                        results.append([])
                except Exception:
                    results.append([])
            return results

    def extract_relations_from_papers(
        self,
        papers_df: pd.DataFrame,
        entities_df: pd.DataFrame,
        query_keywords: Optional[List[str]] = None,
        max_pairs_per_paper: int = 15,
        min_confidence: float = 0.60,
        batch_size: int = 32
    ) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        STEP 3: Extract relationships using high-speed batched transformer inference.
        """
        logger.info(f"\n{'='*80}")
        logger.info("STEP 3: Extracting relationships (Batched High-Speed Inference)")
        logger.info(f"{'='*80}\n")

        # Group entities by paper
        entities_by_paper = {}
        for _, entity_row in entities_df.iterrows():
            paper_id = entity_row["paper_id"]
            if paper_id not in entities_by_paper:
                entities_by_paper[paper_id] = []
            
            entities_by_paper[paper_id].append({
                "text": entity_row["entity"],
                "type": entity_row["entity_type"],
                "confidence": float(entity_row["confidence"]),
                "start": int(entity_row["start"]),
                "end": int(entity_row["end"])
            })

        # Collect all valid pairs across all papers first
        candidate_items = []
        seen_pairs_per_paper = set()

        for idx, paper in papers_df.iterrows():
            paper_id = paper.get("paper_id", f"paper_{idx}")
            title = str(paper.get("title", ""))
            abstract = str(paper.get("abstract", ""))
            text = f"{title}. {abstract}"

            if not text.strip():
                continue

            paper_entities = entities_by_paper.get(paper_id, [])
            if len(paper_entities) < 2:
                continue

            sentences = split_sentences(text)
            paper_pairs = []

            for sentence in sentences:
                sent_lower = sentence.lower()
                sent_entities = [
                    e for e in paper_entities
                    if e["text"].lower() in sent_lower
                ]

                if len(sent_entities) < 2:
                    continue

                for e1, e2 in combinations(sent_entities, 2):
                    # Cross-type filter (e.g. Chemical <-> Disease)
                    if e1["type"] == e2["type"]:
                        continue
                    # Skip duplicate texts
                    t1, t2 = e1["text"].lower().strip(), e2["text"].lower().strip()
                    if t1 == t2 or len(t1) < 2 or len(t2) < 2:
                        continue

                    # Deduplicate within same paper
                    pair_key = (paper_id, min(t1, t2), max(t1, t2))
                    if pair_key in seen_pairs_per_paper:
                        continue
                    seen_pairs_per_paper.add(pair_key)

                    # Priority score (higher if matches query keywords)
                    priority = 0
                    if query_keywords:
                        if text_contains_keyword(t1, query_keywords) or text_contains_keyword(t2, query_keywords):
                            priority = 1

                    paper_pairs.append((priority, e1, e2, sentence))

            if not paper_pairs:
                continue

            # Prioritize query-relevant pairs, then cap per paper
            paper_pairs.sort(key=lambda x: x[0], reverse=True)
            if len(paper_pairs) > max_pairs_per_paper:
                paper_pairs = paper_pairs[:max_pairs_per_paper]

            for _, e1, e2, sentence_ctx in paper_pairs:
                try:
                    truncated_text, adj_e1, adj_e2 = self._truncate_text_around_entities(text, e1, e2)
                    marked_text = self.mark_entities(truncated_text, adj_e1, adj_e2)
                    candidate_items.append({
                        "paper": paper,
                        "paper_id": paper_id,
                        "title": title,
                        "entity1": e1,
                        "entity2": e2,
                        "sentence": sentence_ctx,
                        "marked_text": marked_text
                    })
                except Exception:
                    continue

        total_pairs = len(candidate_items)
        logger.info(f"Prepared {total_pairs} cross-type candidate pairs across {len(papers_df)} papers for batch inference.")

        if total_pairs == 0:
            return pd.DataFrame(), []

        # Run batched inference across all candidate pairs
        marked_texts = [item["marked_text"] for item in candidate_items]
        batch_predictions = self.predict_batch(marked_texts, batch_size=batch_size)

        relations_list = []
        results = []

        for item, predictions in zip(candidate_items, batch_predictions):
            if not predictions:
                continue

            best = predictions[0]
            label = str(best.get("label", ""))
            confidence = float(best.get("score", 0.0))

            if confidence < min_confidence:
                continue

            if label.lower() in {"none", "no_relation", "no relation"}:
                continue

            e1 = item["entity1"]
            e2 = item["entity2"]
            paper = item["paper"]

            relation = {
                "subject": e1["text"],
                "subject_type": e1["type"],
                "subject_confidence": float(e1.get("confidence", 0.0)),
                "relation": label,
                "relation_confidence": confidence,
                "object": e2["text"],
                "object_type": e2["type"],
                "object_confidence": float(e2.get("confidence", 0.0)),
                "sentence": item["sentence"]
            }

            relations_list.append(relation)
            results.append({
                "paper_id": item["paper_id"],
                "title": item["title"],
                "publication_date": paper.get("publication_date", ""),
                "doi": paper.get("doi", ""),
                "pmid": paper.get("pmid", ""),
                "subject": relation["subject"],
                "subject_type": relation["subject_type"],
                "subject_confidence": relation["subject_confidence"],
                "relation": relation["relation"],
                "relation_confidence": relation["relation_confidence"],
                "object": relation["object"],
                "object_type": relation["object_type"],
                "object_confidence": relation["object_confidence"],
                "sentence": relation["sentence"]
            })

        relations_df = pd.DataFrame(results)
        logger.info(
            f"Extracted {len(relations_df)} relations from {total_pairs} pairs "
            f"in batched pass across {len(papers_df)} papers"
        )

        return relations_df, relations_list