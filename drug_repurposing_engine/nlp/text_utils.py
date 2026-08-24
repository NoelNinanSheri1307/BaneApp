"""
Text Processing Utilities for Biomedical NLP

Provides sentence splitting and tokenizer-aware chunking helpers.
"""

import re
from typing import List, Tuple


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences while respecting common biomedical abbreviations.
    """
    if not text:
        return []
    parts = re.split(r'(?<=[\.\!\?])\s+(?=[A-Z])', text)
    return [s.strip() for s in parts if s.strip()]


def chunk_text(
    text: str,
    tokenizer=None,
    max_tokens: int = 512,
    overlap: int = 50
) -> List[Tuple[str, int]]:
    """
    Split long text into chunks respecting token limits and sentence boundaries.
    
    Args:
        text: Text to chunk
        tokenizer: HuggingFace tokenizer (optional)
        max_tokens: Maximum tokens allowed per chunk
        overlap: Overlapping tokens
        
    Returns:
        List of (chunk_text, start_char_position) tuples
    """
    if not text:
        return []

    sentences = []
    current_start = 0
    
    for sentence in text.split("."):
        sentence = sentence.strip()
        if not sentence:
            continue
        start = text.find(sentence, current_start)
        sentences.append((sentence, start))
        current_start = start + len(sentence)

    chunks = []
    current_text = ""
    current_start = None

    for sentence, start in sentences:
        candidate = (current_text + " " + sentence).strip()
        
        if tokenizer:
            try:
                token_count = len(tokenizer.encode(candidate, add_special_tokens=True))
            except Exception:
                token_count = len(candidate.split())
        else:
            token_count = len(candidate.split())

        if token_count <= max_tokens - 10:
            if not current_text:
                current_start = start
            current_text = candidate
        else:
            if current_text:
                chunks.append((current_text, current_start))
            current_text = sentence
            current_start = start

    if current_text:
        chunks.append((current_text, current_start))

    return chunks if chunks else [(text, 0)]
