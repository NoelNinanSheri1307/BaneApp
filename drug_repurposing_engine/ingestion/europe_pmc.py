"""
Literature Ingestion Client (Europe PMC + NCBI PubMed E-Utilities Dual Engine)

Retrieves biomedical literature abstracts and metadata from Europe PMC REST API
with automatic fallback to NCBI PubMed (E-Utilities) and multi-term query expansion.
"""

import logging
import re
import os
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

EUROPE_PMC_URL = os.getenv("EUROPE_PMC_URL", "https://www.ebi.ac.uk/europepmc/webservices/rest/search")
PUBMED_SEARCH_URL = os.getenv("PUBMED_SEARCH_URL", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi")
PUBMED_FETCH_URL = os.getenv("PUBMED_FETCH_URL", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi")


class EuropePMCClient:
    """
    Biomedical literature ingestion client with dual-engine retrieval
    (Europe PMC + NCBI PubMed fallback).
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "DrugRepurposingEngine/2.0 (Biomedical-NLP; mailto:support@drugrepurposing.org)",
            "Accept": "application/json"
        })
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def clean_abstract(self, value: Optional[str]) -> str:
        if value is None:
            return ""
        text = str(value)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def search(
        self,
        query: str,
        page_size: int = 100,
        result_type: str = "core"
    ) -> pd.DataFrame:
        """
        Search biomedical literature for a query.
        Tries Europe PMC first; if 0 results or error, queries NCBI PubMed.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")

        clean_q = query.strip()
        logger.info(f"Ingesting literature for query: '{clean_q}' (Target: {page_size} papers)")

        # 1. Try Europe PMC
        df_epmc = self._search_europe_pmc(clean_q, page_size=page_size, result_type=result_type)
        if len(df_epmc) > 0:
            logger.info(f"Retrieved {len(df_epmc)} papers from Europe PMC.")
            return df_epmc

        # 2. Fallback to NCBI PubMed E-Utilities
        logger.info("Europe PMC returned 0 papers or was unreachable. Falling back to NCBI PubMed E-Utilities...")
        df_pubmed = self._search_pubmed(clean_q, max_papers=page_size)
        if len(df_pubmed) > 0:
            logger.info(f"Retrieved {len(df_pubmed)} papers from NCBI PubMed.")
            return df_pubmed

        # 3. If combined query returned 0 (e.g. "Bosutinib and paracetamol"), search each term independently
        sub_terms = [t.strip() for t in re.split(r"\s+(?:and|or|,|\+)\s+", clean_q, flags=re.IGNORECASE) if len(t.strip()) > 2]
        if len(sub_terms) > 1:
            logger.info(f"Splitting multi-term query into independent searches: {sub_terms}")
            all_dfs = []
            per_term = max(10, page_size // len(sub_terms))
            for term in sub_terms:
                sub_df = self._search_pubmed(term, max_papers=per_term)
                if len(sub_df) > 0:
                    all_dfs.append(sub_df)
            
            if all_dfs:
                combined_df = pd.concat(all_dfs, ignore_index=True).drop_duplicates(subset=["title"]).head(page_size)
                logger.info(f"Retrieved {len(combined_df)} papers across multi-term query.")
                return combined_df

        logger.warning(f"No papers found for query: '{clean_q}'.")
        return pd.DataFrame(columns=[
            "paper_id", "source", "pmid", "pmcid", "doi",
            "title", "abstract", "publication_date", "journal",
            "authors", "article_type", "is_open_access"
        ])

    def _search_europe_pmc(
        self,
        query: str,
        page_size: int = 100,
        result_type: str = "core"
    ) -> pd.DataFrame:
        """Query Europe PMC REST API."""
        try:
            params = {
                "query": query,
                "format": "json",
                "pageSize": page_size,
                "resultType": result_type
            }
            response = self.session.get(EUROPE_PMC_URL, params=params, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                results = data.get("resultList", {}).get("result", [])
                if results:
                    rows = []
                    for paper in results:
                        abstract = self.clean_abstract(paper.get("abstractText"))
                        title = paper.get("title", "")
                        if title and (abstract or len(title) > 20):
                            rows.append({
                                "paper_id": paper.get("id", ""),
                                "source": paper.get("source", "EPMC"),
                                "pmid": paper.get("pmid", ""),
                                "pmcid": paper.get("pmcid", ""),
                                "doi": paper.get("doi", ""),
                                "title": title,
                                "abstract": abstract or title,
                                "publication_date": paper.get("firstPublicationDate", ""),
                                "journal": paper.get("journalTitle", ""),
                                "authors": paper.get("authorString", ""),
                                "article_type": paper.get("pubType", ""),
                                "is_open_access": paper.get("isOpenAccess", "N")
                            })
                    if rows:
                        return pd.DataFrame(rows)
        except Exception as e:
            logger.debug(f"Europe PMC query exception: {e}")
        return pd.DataFrame()

    def _search_pubmed(self, term: str, max_papers: int = 100) -> pd.DataFrame:
        """Query NCBI PubMed via E-Utilities (esearch + efetch)."""
        try:
            # 1. ESearch for PMIDs
            s_params = {
                "db": "pubmed",
                "term": term,
                "retmode": "json",
                "retmax": min(max_papers, 200),
                "sort": "relevance"
            }
            r_search = self.session.get(PUBMED_SEARCH_URL, params=s_params, timeout=self.timeout)
            if r_search.status_code != 200:
                return pd.DataFrame()

            id_list = r_search.json().get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return pd.DataFrame()

            # 2. EFetch XML metadata
            f_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml"
            }
            r_fetch = self.session.get(PUBMED_FETCH_URL, params=f_params, timeout=self.timeout)
            if r_fetch.status_code != 200:
                return pd.DataFrame()

            root = ET.fromstring(r_fetch.content)
            rows = []
            for article in root.findall(".//PubmedArticle"):
                pmid = article.findtext(".//MedlineCitation/PMID") or ""
                title = article.findtext(".//ArticleTitle") or ""
                abstract_parts = article.findall(".//Abstract/AbstractText")
                abstract = " ".join([p.text or "" for p in abstract_parts if p.text])
                
                journal = article.findtext(".//Journal/Title") or article.findtext(".//Journal/ISOAbbreviation") or ""
                pub_date = article.findtext(".//JournalIssue/PubDate/Year") or ""
                
                doi = ""
                for el in article.findall(".//ArticleId"):
                    if el.get("IdType") == "doi":
                        doi = el.text or ""

                author_names = []
                for author in article.findall(".//AuthorList/Author"):
                    last = author.findtext("LastName") or ""
                    fore = author.findtext("ForeName") or ""
                    if last:
                        author_names.append(f"{fore} {last}".strip())

                if title:
                    rows.append({
                        "paper_id": f"MED-{pmid}" if pmid else f"PUB-{len(rows)}",
                        "source": "MED",
                        "pmid": pmid,
                        "pmcid": "",
                        "doi": doi,
                        "title": title,
                        "abstract": abstract or title,
                        "publication_date": pub_date,
                        "journal": journal,
                        "authors": ", ".join(author_names[:4]),
                        "article_type": "Journal Article",
                        "is_open_access": "Y"
                    })

            if rows:
                return pd.DataFrame(rows)
        except Exception as e:
            logger.warning(f"NCBI PubMed retrieval error for '{term}': {e}")

        return pd.DataFrame()