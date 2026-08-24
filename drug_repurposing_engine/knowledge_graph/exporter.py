"""
Knowledge Graph & Pipeline Results Exporter

Handles exporting all generated artifacts:
- evidence_mapping.csv
- graph_statistics.json
- graph_data.json
- PIPELINE_SUMMARY.txt
- knowledge_graph.html
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)


def export_pipeline_results(
    query: str,
    graph_data: Dict[str, Any],
    output_dir: str = "results",
    knowledge_graph=None
) -> Dict[str, str]:
    """
    Export all pipeline results into standardized structured files.
    
    Args:
        query: Original user search query
        graph_data: Dictionary containing 'nodes', 'edges', 'evidence', 'grouped_evidence'
        output_dir: Directory to save generated artifacts
        knowledge_graph: BiomedicalKnowledgeGraph instance for HTML export
        
    Returns:
        Dictionary of output file paths keyed by artifact name
    """
    logger.info(f"\n{'='*80}")
    logger.info("Exporting Pipeline Results")
    logger.info(f"{'='*80}\n")

    output_files = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 1. Export Evidence Mapping CSV
        evidence_file = os.path.join(output_dir, "evidence_mapping.csv")
        evidence_df = pd.DataFrame(graph_data.get("evidence", []))
        evidence_df.to_csv(evidence_file, index=False)
        output_files["evidence_mapping"] = evidence_file
        logger.info(f"Evidence mapping exported to {evidence_file}")

        # 2. Compute and Export Graph Statistics JSON
        stats_file = os.path.join(output_dir, "graph_statistics.json")
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        grouped_evidence = graph_data.get("grouped_evidence", {})

        stats = {
            "query": query,
            "timestamp": timestamp,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "unique_relations": len(grouped_evidence),
            "nodes_by_type": {},
            "relations_distribution": {}
        }

        for node in nodes:
            node_type = node.get("type", "Unknown")
            stats["nodes_by_type"][node_type] = (
                stats["nodes_by_type"].get(node_type, 0) + 1
            )

        for edge in edges:
            relation = edge.get("relation", "Unknown")
            stats["relations_distribution"][relation] = (
                stats["relations_distribution"].get(relation, 0) + 1
            )

        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
        output_files["statistics"] = stats_file
        logger.info(f"Graph statistics exported to {stats_file}")

        # 3. Discover and Export Repurposing Hypotheses (Cards 4, 5, 7)
        opportunities = []
        try:
            from repurposing.engine import RepurposingEngine
            rep_engine = RepurposingEngine()
            opportunities = rep_engine.find_all_opportunities(
                nodes=nodes,
                edges=edges,
                evidence_list=graph_data.get("evidence", [])
            )
            opp_json_file = os.path.join(output_dir, "repurposing_opportunities.json")
            with open(opp_json_file, "w", encoding="utf-8") as f:
                json.dump(opportunities, f, indent=2)
            output_files["repurposing_opportunities"] = opp_json_file
            logger.info(f"Discovered {len(opportunities)} repurposing opportunities -> {opp_json_file}")
        except Exception as e:
            logger.warning(f"Could not compute repurposing opportunities: {e}")

        # 3b. Fetch Drug Overview Profile (Card 2)
        drug_profile = None
        try:
            from ingestion.pubchem import PubChemClient
            pubchem = PubChemClient()
            # Extract primary drug name from query or first Chemical node
            primary_drug = query
            for n in nodes:
                if n.get("type") == "Chemical":
                    primary_drug = n.get("name", query)
                    break
            drug_profile = pubchem.get_drug_overview(primary_drug)
        except Exception as e:
            logger.warning(f"Could not fetch drug profile: {e}")

        # 4. Export Knowledge Graph HTML Visualization (with Repurposing Tabs)
        if knowledge_graph is not None:
            kg_html_file = os.path.join(output_dir, "knowledge_graph.html")
            knowledge_graph.export_graph(
                kg_html_file,
                query=query,
                evidence=graph_data.get("evidence", []),
                stats=stats,
                title=f"BioGraph AI | {query}",
                opportunities=opportunities,
                drug_profile=drug_profile
            )
            output_files["knowledge_graph_html"] = kg_html_file
            logger.info(f"Knowledge graph visualization exported to {kg_html_file}")

        # 4b. Export Graph Data JSON
        graph_json_file = os.path.join(output_dir, "graph_data.json")
        graph_json = {
            "nodes": nodes,
            "edges": edges
        }
        with open(graph_json_file, "w", encoding="utf-8") as f:
            json.dump(graph_json, f, indent=2)
        output_files["graph_data_json"] = graph_json_file
        logger.info(f"Graph data exported to {graph_json_file}")

        # 5. Export Summary Text Report
        summary_file = os.path.join(output_dir, "PIPELINE_SUMMARY.txt")
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("DRUG REPURPOSING ENGINE - PIPELINE EXECUTION SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Query: {query}\n")
            f.write(f"Timestamp: {timestamp}\n\n")
            f.write("RESULTS:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Biomedical Entities Extracted: {len(nodes)}\n")
            f.write(f"Total Relationships Discovered: {len(edges)}\n")
            f.write(f"Unique Relation Types: {len(grouped_evidence)}\n\n")
            f.write("Nodes by Type:\n")
            for node_type, count in stats["nodes_by_type"].items():
                f.write(f"  - {node_type}: {count}\n")
            f.write("\nRelationships Distribution:\n")
            for rel_type, count in stats["relations_distribution"].items():
                f.write(f"  - {rel_type}: {count}\n")
            f.write("\n" + "=" * 80 + "\n")
            f.write("OUTPUT FILES:\n")
            f.write("-" * 80 + "\n")
            for file_type, file_path in output_files.items():
                f.write(f"  {file_type}: {file_path}\n")
            f.write("=" * 80 + "\n")

        output_files["summary"] = summary_file
        logger.info(f"Summary report exported to {summary_file}")

        return output_files

    except Exception as e:
        logger.error(f"Failed to export results: {e}")
        raise
