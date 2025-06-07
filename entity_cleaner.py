import json
import re

def has_unbalanced_brackets(text):
    """Check for unmatched parentheses"""
    return text.count('(') != text.count(')')

def clean_entities(input_file, cleaned_output, final_output, score_threshold=0.85):
    # Step 1: Load entities
    with open(input_file, 'r', encoding='utf-8') as f:
        entities = json.load(f)

    cleaned = []
    seen = set()

    for entity in entities:
        label = entity.get('label', '')
        score = entity.get('score', 0)
        raw_text = entity.get('text', '').strip()

        # Filter unwanted labels
        if label in ['Nonbiological_location', 'Lab_value', 'Date']:
            continue

        # Confidence threshold
        if score < score_threshold:
            continue

        # Clean hyphen spacing (e.g., "non - small" → "non-small")
        text = re.sub(r'\s+-\s+', '-', raw_text)

        # Remove leading/trailing non-word chars (quotes, symbols, etc.)
        text = re.sub(r"^\W+|\W+$", "", text)

        # Remove trailing punctuation
        text = re.sub(r"[.,;:!?]+$", "", text)

        # Final trim
        text = text.strip()

        # Rule-based filters
        if not text:
            continue

        if has_unbalanced_brackets(text):
            continue

        if len(text) <= 1:
            continue

        if len(text.split()) == 1 and len(text) <= 4:
            continue  # short, isolated term — usually noise

        if re.search(r"[^\w\s\-)(]", text):  # disallow stray symbols
            continue

        # Case-insensitive deduplication by (text, label)
        key = (text.lower(), label)
        if key not in seen:
            seen.add(key)
            cleaned.append({
                'text': text,
                'label': label,
                'score': round(float(score), 4)
            })

    # Output cleaned entities (full + text-only)
    with open(cleaned_output, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    with open(final_output, 'w', encoding='utf-8') as f:
        json.dump([e['text'] for e in cleaned], f, indent=2, ensure_ascii=False)

    print(f"Original: {len(entities)} entities")
    print(f"Cleaned: {len(cleaned)} entities")
    print(f"Removed: {len(entities) - len(cleaned)} entities")

if __name__ == "__main__":
    clean_entities(
        input_file="output/extracted_entities.json",
        cleaned_output="output/cleaned_entities.json",
        final_output="output/final_entities.json",
        score_threshold=0.88
    )
