# agent_entity_extractor.py

import json
import torch
import os
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from nltk.tokenize import sent_tokenize

MODEL_NAME = "d4data/biomedical-ner-all"
PDF_CLEANED_PATH = Path("./dataset/cleaned_papers")

def initialize_pipeline():
    """Initialize the NER pipeline"""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)
    return pipeline(
        "ner",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="max",
        device="cuda:0" if torch.cuda.is_available() else -1
    )

def extract_text_from_cleaned_file(filename):
    """Load a cleaned text file"""
    try:
        with open(PDF_CLEANED_PATH / filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"⚠ Error reading cleaned file: {e}")
        return ""

def process_text_chunk(nlp, text_chunk):
    try:
        return nlp(text_chunk)
    except Exception as e:
        print(f"⚠ Error processing chunk: {e}")
        return []

def extract_entities(nlp, text):
    try:
        sentences = sent_tokenize(text)
    except LookupError:
        print("❌ NLTK not available. Run setup_nltk.py first.")
        return []

    entities = []
    tokenizer = nlp.tokenizer
    
    for sent in sentences:
        tokens = tokenizer.tokenize(sent)
        if len(tokens) > 400:
            words = sent.split()
            chunks = [' '.join(words[i:i+300]) for i in range(0, len(words), 300)]
            for chunk in chunks:
                entities.extend(process_text_chunk(nlp, chunk))
        else:
            entities.extend(process_text_chunk(nlp, sent))

    return [
        {"label": ent["entity_group"], "text": ent["word"], "score": float(ent["score"])}
        for ent in entities if ent["score"] >= 0.7
    ]

def extract_entities_from_file(filename: str, output_folder: Path):
    """Process a cleaned .txt file and save extracted entities to a folder"""
    nlp = initialize_pipeline()
    text = extract_text_from_cleaned_file(filename)
    entities = extract_entities(nlp, text)

    output_folder.mkdir(parents=True, exist_ok=True)
    output_path = output_folder / "extracted_entities.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)

    print(f"✅ Extracted {len(entities)} entities to {output_path}")

# Optional: Remove or comment out main() block
if __name__ == "__main__":
    print("❌ This script should be used via main_pipeline.py")
