# 🧬 Bane (Biotech Arbitrage Engine)
### *Next-Generation Biomedical NLP & Traceable Drug Repurposing Platform*

---

[![Flutter](https://img.shields.io/badge/Flutter-3.10+-02569B?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![HuggingFace](https://img.shields.io/badge/Transformers-4.45+-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co)
[![License](https://img.shields.io/badge/License-Proprietary-blue?style=for-the-badge)](#)

---

## 📌 Executive Summary

**Bane** (Biotech Arbitrage Engine) is an end-to-end computational drug repurposing intelligence platform. It connects real-time biomedical literature retrieval with fine-tuned Transformer NLP models to construct **fully traceable, evidence-backed knowledge graphs**. 

Unlike generic generative AI summaries that hallucinate or collapse conflicting data, Bane extracts structured relationships (**Drug ➔ Target ➔ Pathway ➔ Disease**) and strictly preserves both supporting and contradictory trial evidence with sentence-level PubMed/DOI citations.

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 BANE RESEARCH PLATFORM                  │
                  └────────────────────────────┬────────────────────────────┘
                                               │
               ┌───────────────────────────────┴───────────────────────────────┐
               ▼                                                               ▼
  ┌─────────────────────────┐                                     ┌─────────────────────────┐
  │   FLUTTER CLIENT APP    │                                     │     FASTAPI BACKEND     │
  │  (iOS, Android, Web,    │ ◄─────── REST API / JSON ─────────► │ (Drug Repurposing Engine│
  │   macOS, Windows)       │                                     │  & Transformer Pipeline)│
  └─────────────────────────┘                                     └─────────────────────────┘
```

---

## 🏗️ System Architecture

The project is architected into two decoupled components:

```
alfahamapp/
├── lib/                             # Flutter Cross-Platform Frontend (Bane)
│   ├── core/                        # Design System, Routing, Config & Networking
│   │   ├── config/api_config.dart   # Dynamic Base URL resolution & persistence
│   │   ├── routing/app_router.dart  # GoRouter navigation schema
│   │   └── theme/app_theme.dart     # Warm Ivory Scientific UI Design System
│   ├── models/                      # Domain Data Models (Papers, Signals, Evidence, Graph)
│   ├── providers/                   # Riverpod State Providers & Controllers
│   ├── screens/                     # Modular Feature Workbenches
│   │   ├── landing/                 # Product Overview & Scientific Philosophy
│   │   ├── auth/                    # Auth Session & Server URL Configuration
│   │   ├── workspace/               # Workspace Shell & Navigation Drawer
│   │   ├── dashboard/               # Research Metrics & Quick Query Hub
│   │   ├── search/                  # PubMed/Europe PMC Query Workbench
│   │   ├── signals/                 # Repurposing Signals & Hypothesis Detail
│   │   ├── graph/                   # Interactive Biological Knowledge Graph Canvas
│   │   ├── evidence/                # Sentence-Level Evidence & Citation Explorer
│   │   ├── papers/                  # Research Paper Library & Abstract Viewer
│   │   ├── drugs/ & diseases/       # Molecular & Phenotype Detail Dossiers
│   │   ├── projects/                # Curated Research Workspace Collections
│   │   ├── alerts/                  # Literature Surveillance Feeds
│   │   └── saved/                   # Offline Saved Hypotheses & Notes
│   └── widgets/                     # Reusable Scientific & Visual Components
│
└── drug_repurposing_engine/         # Python / PyTorch Biomedical NLP Engine
    ├── ingestion/                   # Literature Retrieval (Europe PMC & PubChem)
    ├── nlp/                         # Transformer NER & Relation Extraction Pipelines
    ├── knowledge_graph/             # NetworkX Graph Construction & PyVis Exporters
    ├── repurposing/                 # Multi-Hop Graph Pathfinding & Scoring Engine
    ├── models/                      # Trained Transformer Weights & Tokenizers
    │   ├── ner/                     # Bio-NER Model (Chemicals, Genes, Diseases, Targets)
    │   └── relation/                # Relation Extraction Model (Glasgow-AI4BioMed)
    ├── pipeline.py                  # CLI Pipeline Orchestrator
    ├── main.py                      # Production FastAPI REST Server
    ├── db.py                        # SQLite Persistent Storage & User Data
    └── requirements.txt             # Python Dependencies
```

---

## ⚡ Core Features & Capabilities

### 1. 🔍 Automated Biomedical Ingestion
- Real-time ingestion via **Europe PMC REST API** and **PubChem**.
- Dynamic query expansion and relevancy filtering over titles and abstracts.

### 2. 🧠 Dual-Stage Transformer NLP Pipeline
- **Named Entity Recognition (NER)**: Identifies biomedical entities (`Chemical`, `Disease`, `Gene`, `Protein`, `Species`) with confidence scores.
- **Relation Extraction (RE)**: Classifies directional mechanisms (`treats`, `inhibits`, `upregulates`, `interacts_with`, `causes`, `biomarker_of`).
- Automatic sliding-window chunking for documents exceeding tokenizer limits (512 tokens).

### 3. 🕸️ Traceable Knowledge Graph & Multi-Hop Pathfinding
- Graph representations constructed using **NetworkX** and exported to **PyVis interactive HTML**.
- Algorithmic pathfinding discovers hidden multi-step biological links:
  $$\text{Drug } A \xrightarrow{\text{inhibits}} \text{Target } T \xrightarrow{\text{pathway}} \text{Disease } D$$
- Full provenance: Every relationship points directly to the underlying DOI, PMID, and raw abstract sentence.

### 4. ⚖️ Contradictory Evidence Preservation
- Opposing and negative trial findings are never collapsed or suppressed, providing unbiased scientific diligence.

### 5. 🎨 Modern Warm Ivory Scientific UI
- Built with Flutter and Riverpod for 60fps responsive desktop and mobile experiences.
- Live server switcher, pipeline progress modal, interactive graph inspector, and research project management.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Flutter SDK**: `^3.10.4` ([Install Flutter](https://docs.flutter.dev/get-started/install))
- **Python**: `3.9+` (Recommended `3.10` or `3.11`)
- **System Memory**: 8GB+ RAM recommended for running local PyTorch models.

---

### Step 1: Run the Backend Engine

1. Navigate to the backend directory:
   ```bash
   cd drug_repurposing_engine
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *The interactive API documentation is available at `http://localhost:8000/docs`.*

---

### Step 2: Run the Flutter Client

1. Open a new terminal in the project root:
   ```bash
   flutter pub get
   ```

2. Launch on your platform of choice:
   ```bash
   # Web (Google Chrome)
   flutter run -d chrome

   # Windows Desktop
   flutter run -d windows

   # Android / iOS
   flutter run -d <device_id>
   ```

---

## 📡 REST API Overview

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/pipeline/run` | `POST` | Launches an asynchronous end-to-end literature & NLP extraction run. |
| `GET /api/pipeline/status` | `GET` | Returns live status and progress of the active pipeline run. |
| `GET /api/graph/data` | `GET` | Returns nodes and directed edges formatted for client rendering. |
| `GET /api/graph/view` | `GET` | Serves the interactive PyVis HTML knowledge graph. |
| `GET /api/evidence` | `GET` | Retrieves sentence-level evidence snippets mapped to PMIDs and DOIs. |
| `GET /api/repurposing/signals`| `GET` | Returns scored drug repurposing candidates and confidence ranks. |
| `GET /api/stats` | `GET` | Summarizes entity counts, relation types, and publication metrics. |
| `POST /api/auth/login` | `POST` | Authenticates researchers and returns a session token. |
| `GET /api/projects` | `GET` | Fetches saved research projects and dossiers. |

---

## 🧪 Testing & Verification

Run Flutter unit and widget smoke tests:
```bash
flutter test
```

Analyze Dart code for linting and type health:
```bash
flutter analyze
```

Execute a direct CLI test run of the Python NLP pipeline:
```bash
cd drug_repurposing_engine
python pipeline.py "metformin longevity" --max-results 20
```

---

## ☁️ Deployment Notes

- **Backend RAM Requirements**: The local backend loads dual Transformer models (`~874 MB` weight files on disk). Runtime memory consumption ranges between **1.3 GB – 2.0 GB RAM**. Hosting on free-tier platforms with hard 512 MB limits (e.g., Render Free) will trigger Out-Of-Memory (`OOMKilled`) kills. 
- **Recommended Hosting**: Render Starter ($7/mo - 2GB RAM), Hugging Face Spaces (Free CPU tier with 16GB RAM), or offloading model inference to serverless APIs (Hugging Face Endpoints / Gemini API).

---

## 📄 License

Proprietary — Developed for advanced biomedical research and computational drug repurposing diligence.
