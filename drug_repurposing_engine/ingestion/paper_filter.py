"""
Paper Filtering & Relevance Scoring Module

Provides query keyword extraction and relevance scoring to prioritize
and filter papers retrieved from biomedical literature APIs.
"""

import re
import logging
from typing import List
import pandas as pd

logger = logging.getLogger(__name__)

# Common stopwords to exclude when parsing user queries
STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "of", "for", "to",
    "with", "by", "is", "are", "was", "were", "be", "been", "has",
    "have", "had", "do", "does", "did", "at", "from", "as", "but",
    "not", "this", "that", "it", "its", "can", "will", "may",
    "drug", "drugs", "new", "novel", "study", "research", "using",
}


def parse_query_keywords(query: str) -> List[str]:
    """
    Extract meaningful biomedical keywords from the user query (lowercased).
    """
    tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def text_contains_keyword(text: str, keywords: List[str]) -> bool:
    """
    Check if text contains at least one of the given keywords.
    """
    if not text or not keywords:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def score_paper_relevance(text: str, keywords: List[str]) -> int:
    """
    Count how many distinct query keywords appear in the given text.
    """
    if not text or not keywords:
        return 0
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def filter_papers_by_relevance(
    papers_df: pd.DataFrame,
    query: str,
    top_n: int = 20
) -> pd.DataFrame:
    """
    Rank & filter papers by relevance to the user query.
    
    Keeps only papers whose title+abstract contain at least one query
    keyword, sorted by number of keyword hits (descending), capped at top_n.
    """
    logger.info(f"\n{'='*80}")
    logger.info("STEP 1b: Filtering papers by query relevance")
    logger.info(f"{'='*80}\n")

    keywords = parse_query_keywords(query)
    logger.info(f"Query keywords: {keywords}")

    if not keywords:
        logger.warning("No meaningful keywords parsed - keeping all retrieved papers")
        return papers_df.head(top_n).reset_index(drop=True)

    scored_rows = []
    for idx, paper in papers_df.iterrows():
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        score = score_paper_relevance(text, keywords)
        if score > 0:
            scored_rows.append((score, idx))

    scored_rows.sort(key=lambda x: x[0], reverse=True)
    keep_indices = [idx for _, idx in scored_rows[:top_n]]
    filtered_df = papers_df.loc[keep_indices].reset_index(drop=True)

    logger.info(
        f"Papers: {len(papers_df)} retrieved -> {len(filtered_df)} relevant "
        f"(dropped {len(papers_df) - len(filtered_df)})"
    )

    if len(filtered_df) == 0:
        logger.warning("All papers filtered out - falling back to top 10 by API order")
        return papers_df.head(10).reset_index(drop=True)

    return filtered_df
