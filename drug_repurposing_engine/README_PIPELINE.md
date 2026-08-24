# Drug Repurposing Engine - Unified Data Flow Pipeline

## 📋 Overview

This is a complete, production-ready biomedical NLP pipeline that automatically extracts biomedical entities and relationships from scientific literature to build a traceable knowledge graph for drug repurposing research.

**The entire pipeline runs with a single command!**

```bash
# Windows
run_pipeline.bat "your query"

# Linux/macOS
./run_pipeline.sh "your query"

# Direct Python
python pipeline.py "your query"
```

## 🔄 Pipeline Workflow

```
User Query
   ↓
[Step 1: Europe PMC API] → Retrieve Research Papers
   ↓
[Step 2: NER Model] → Extract Biomedical Entities
   ↓
[Step 3: Relation Extraction] → Extract Entity Relationships
   ↓
[Step 4: Knowledge Mapping + Evidence Mapping] → Build Traceable Knowledge Graph
   ↓
[Export Results] → Interactive Visualization, CSV, JSON, Statistics
```

### Pipeline Steps Explained

#### Step 1: Research Retrieval
- Sends user query to Europe PMC API
- Retrieves relevant research papers
- Extracts titles, abstracts, DOI, PMID, publication dates

#### Step 2: Named Entity Recognition (NER)
- Runs trained NER model on paper titles and abstracts
- Identifies biomedical entities: drugs, diseases, proteins, genes, targets
- Returns confidence scores for each entity
- Handles long texts by intelligent chunking (respects token limits)

#### Step 3: Relation Extraction
- Extracts relationships between identified entities
- Uses trained Relation Extraction model (Glasgow-AI4BioMed/synthetic_relex)
- Classifies relation types (e.g., "treats", "interacts_with", "associated_with")
- Provides confidence scores for each relationship

#### Step 4: Knowledge Mapping + Evidence Mapping
- Builds a knowledge graph from extracted relationships
- **Ensures complete traceability**: every relationship is mapped back to its source paper
- Links relationships to evidence text, publication details, DOI, PMID
- Enables verification and citation of discoveries

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Internet connection (for downloading papers and models)
- 8GB+ RAM recommended

### Installation

```bash
cd "C:\Users\AMAL SUMESH\Desktop\drug_repurposing_engine"

# Install dependencies
python -m pip install -r requirements.txt
```

### Run the Pipeline

**Windows Command Prompt:**
```batch
run_pipeline.bat "COVID-19 treatment"
run_pipeline.bat "EGFR mutations" 200
run_pipeline.bat "cancer drug targets"
```

**Linux/macOS Terminal:**
```bash
chmod +x run_pipeline.sh
./run_pipeline.sh "COVID-19 treatment"
./run_pipeline.sh "EGFR mutations" 200
./run_pipeline.sh "cancer drug targets"
```

**Direct Python (All Platforms):**
```bash
python pipeline.py "COVID-19 treatment"
python pipeline.py "EGFR mutations" --max-results 200
python pipeline.py "cancer drug targets" --ner-model models/ner --relation-model models/relation
```

## 📊 Output Files

After pipeline execution, results are saved in `results/` (replaced on each run):

### 1. **knowledge_graph.html** ⭐
- Interactive visualization of the knowledge graph
- Click to explore entity connections
- Shows relationship types and confidence scores
- Open in any web browser

### 2. **evidence_mapping.csv**
- Complete traceability for every relationship
- Columns: subject, relation, object, paper_id, title, doi, pmid, evidence_text
- Allows verification and citation of discovered relationships
- Import into Excel/Spreadsheet for analysis

### 3. **graph_statistics.json**
- Summary metrics: total nodes, edges, unique relations
- Distribution of entity types (Drug, Disease, Protein, Gene, etc.)
- Distribution of relationship types
- Query metadata and execution timestamp

### 4. **graph_data.json**
- Complete knowledge graph in JSON format
- Nodes: biomedical entities with types
- Edges: relationships with confidence scores
- Can be imported into other visualization/analysis tools

### 5. **PIPELINE_SUMMARY.txt**
- Human-readable execution summary
- Quick reference for key metrics
- File locations and results overview

## 🎯 Usage Examples

### Example 1: Find drug-disease interactions
```bash
python pipeline.py "metformin diabetes treatment"
```

### Example 2: Large-scale biomedical research
```bash
python pipeline.py "EGFR mutations cancer therapy" --max-results 500
```

### Example 3: Protein interaction analysis
```bash
python pipeline.py "SARS-CoV-2 protein interactions" --max-results 200
```

### Example 4: Using GPU acceleration
```bash
python pipeline.py "your query" --device 0
```

## 🔧 Advanced Options

```bash
python pipeline.py "QUERY" [OPTIONS]

Options:
  --max-results NUM         Maximum papers to retrieve (default: 100)
  --ner-model PATH         Path to NER model (default: models/ner)
  --relation-model PATH    Path to Relation Extraction model (default: models/relation)
  --device ID              GPU device ID (-1 for CPU, default: -1)
```

## 📝 Configuration

### Default Settings
- Max papers: 100
- NER model: `models/ner`
- Relation model: `models/relation`
- Device: CPU (-1)
- Minimum confidence: 0.50 (for relation extraction)

### Model Information
- **NER Model**: Fine-tuned on biomedical texts
- **Relation Extraction**: Glasgow-AI4BioMed/synthetic_relex
- **Token limit**: 512 (with intelligent chunking for longer texts)

## 🧪 Testing

Test individual components:

```bash
# Test NER module
python -m tests.test_ner

# Test Relation Extraction
python -m tests.test_relation_extraction

# Test Knowledge Graph
python -m tests.test_knowledge_graph

# Test Evidence Mapping
python -m tests.test_evidence_mapping
```

## 📂 Project Structure

```
drug_repurposing_engine/
├── pipeline.py                 # Main orchestration script
├── run_pipeline.bat           # Windows launcher
├── run_pipeline.sh            # Unix/Linux/macOS launcher
├── requirements.txt           # Python dependencies
├── commands.txt               # Command reference
├── README.md                  # This file
├── ingestion/
│   └── europe_pmc.py         # Europe PMC API client
├── nlp/
│   ├── __init__.py
│   ├── ner.py                # Named Entity Recognition
│   └── relation_extraction.py # Relation Extraction
├── knowledge_graph/
│   ├── knowledge_graph.py     # Knowledge graph builder
│   └── evidence/
│       └── evidence_mapper.py # Evidence mapping
├── models/
│   ├── ner/                   # NER model files
│   └── relation/              # Relation Extraction model files
├── tests/                     # Test files
└── lib/                       # External libraries (vis.js, tom-select, etc.)
```

## 🐛 Troubleshooting

### "No papers retrieved"
- Check your internet connection
- Try a different query
- Increase `--max-results` to get broader results
- Ensure Europe PMC API is accessible

### "NER model not found"
- Verify `models/ner/` directory contains model files
- Use `--ner-model path/to/model` to specify custom path
- Check model download status

### "CUDA out of memory"
- Use `--device -1` to switch to CPU
- Reduce `--max-results` to process fewer papers
- Close other GPU-intensive applications

### "No relations extracted"
- May happen with limited entity pairs
- Pipeline continues with knowledge graph visualization
- Try different query or increase `--max-results`

### Module import errors
- Reinstall dependencies: `pip install -r requirements.txt`
- Ensure you're in the correct directory
- Check Python version is 3.8+

## 📈 Performance Tips

1. **For CPU-only execution**: Start with 100-200 papers
2. **For GPU execution**: Can process 500+ papers efficiently
3. **Longer queries**: Get more focused results
4. **Multiple runs**: Cache prevents redundant API calls within session

## 🔐 Data Privacy

- Data is processed locally after retrieval from Europe PMC
- Europe PMC papers are open access by design
- No data is stored permanently unless saved by user
- Logs are generated locally in `pipeline.log`

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs in `pipeline.log`
3. Verify all dependencies: `pip install -r requirements.txt`
4. Test individual components using test commands

## 📄 Citation

If you use this pipeline in research, please cite:
- Europe PMC API
- Glasgow-AI4BioMed Relation Extraction Model
- NetworkX and PyVis libraries

## 📜 License

See project license for usage terms.

---

**Ready to run?** Execute one of these commands:

```bash
# Windows
run_pipeline.bat "your biomedical query"

# Linux/macOS
./run_pipeline.sh "your biomedical query"

# Direct Python
python pipeline.py "your biomedical query"
```

Enjoy discovering biomedical relationships! 🧬
