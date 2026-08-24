---
task: sequence-classification
tags:
- biomedical
- bionlp
- relation extraction
license: mit
base_model: microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext
---

# synthetic_relex model for biomedical relation extraction

This is a relation extraction model that is distilled from Llama 3.3 70B down to a BERT model. It is a [microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext](https://huggingface.co/microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext) model that has been fine-tuned on synthetic labels created with Llama 3.3 70B when prompted with sentences from [PubTator Central](https://www.ncbi.nlm.nih.gov/research/pubtator3/). The dataset is available [here](https://huggingface.co/datasets/Glasgow-AI4BioMed/synthetic_relex).

**Note:** No humans were involved in annotating the dataset used, so there may be erroneous annotations. Detailed evaluation by human experts would be needed to gain an accurate view of the model's accuracy. The dataset and model offer a starting point for understanding and development of biomedical relation extraction models.

More information about the model and dataset can be found at the project repo: https://github.com/Glasgow-AI4BioMed/synthetic_relex

## 🚀 Example Usage

The model can classify the relationship between two entities into one of X labels. The labels are: 

To use the model, take the input text and wrap the first entity in [E1][/E1] tags and second entity in [E2][/E2] tags as in the example below. The classifier then outputs the predicted relation label with an associated score.

```python
from transformers import pipeline

classifier = pipeline("text-classification", model="Glasgow-AI4BioMed/synthetic_relex")

classifier("[E1]Paclitaxel[/E1] is a common chemotherapy used for [E2]lung cancer[/E2].")

# Output:
# [{'label': 'treats', 'score': 0.9868311882019043}]
```

## 📈 Performance

The results on the test set are reported below:

| Label | Precision | Recall | F1-score | Support |
| --- | --- | --- | --- | --- |
| affects_efficacy_of | 0.473 | 0.296 | 0.364 | 1127 |
| binds_to | 0.541 | 0.266 | 0.357 | 492 |
| biomarker_for | 0.455 | 0.621 | 0.525 | 314 |
| causes | 0.667 | 0.571 | 0.615 | 3400 |
| co_expressed_with | 0.440 | 0.473 | 0.456 | 131 |
| downregulates | 0.472 | 0.481 | 0.477 | 106 |
| inhibits | 0.460 | 0.251 | 0.324 | 1429 |
| interacts_with | 0.469 | 0.310 | 0.373 | 1588 |
| none | 0.936 | 0.961 | 0.948 | 76442 |
| plays_causal_role_in | 0.343 | 0.426 | 0.380 | 202 |
| precursor_of | 0.462 | 0.212 | 0.291 | 113 |
| prevents | 0.602 | 0.504 | 0.548 | 135 |
| regulates | 0.504 | 0.509 | 0.506 | 116 |
| subtype_of | 0.382 | 0.521 | 0.441 | 286 |
| treats | 0.630 | 0.702 | 0.664 | 1000 |
| upregulates | 0.564 | 0.549 | 0.557 | 224 |
| **macro avg** | **0.525** | **0.478** | **0.489** | **87105** |
| weighted avg | 0.889 | 0.898 | 0.892 | 87105 |
