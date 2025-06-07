import json
import pickle
from collections import defaultdict
from tqdm import tqdm
from rapidfuzz import process, fuzz
import re

class NCItValidator:
    def __init__(self, index_path="ncit_indexes.pkl"):
        with open(index_path, 'rb') as f:
            data = pickle.load(f)

        self.entity_index = data['entity_index']             # {normalized_text: [C_IDs]}
        self.rel_index = data['rel_index']                   # {(C1, C2): [REL_TYPEs]}
        self.predicate_labels = data.get('predicate_labels', {})
        self.term_list = list(self.entity_index.keys())

        print(f"✅ Loaded {len(self.entity_index)} entities and {len(self.rel_index)} relationships")

    def normalize(self, term):
        """Lowercase and strip unwanted characters."""
        term = term.lower()
        term = re.sub(r'[\(\)\[\],:;]', '', term)
        term = re.sub(r'\s{2,}', ' ', term)
        return term.strip()

    def resolve_entity(self, term, fuzzy=True, threshold=85):
        """Resolve a term to NCIt concept IDs using exact or fuzzy match."""
        norm_term = self.normalize(term)

        # Exact match
        if norm_term in self.entity_index:
            return self.entity_index[norm_term]

        # Fuzzy match fallback
        if fuzzy:
            matches = process.extract(norm_term, self.term_list, scorer=fuzz.ratio, limit=1)
            if matches and matches[0][1] >= threshold:
                best_match = matches[0][0]
                return self.entity_index[best_match]

        return []

    def find_relationships(self, source_id, target_id, requested_relation=None):
        relationships = []
        requested_relation = requested_relation.lower() if requested_relation else None

        for (s, t), preds in self.rel_index.items():
            if s == source_id and t == target_id:
                for pred in preds:
                    pred_label = self.predicate_labels.get(pred, "").lower()
                    is_requested = (
                        requested_relation
                        and (requested_relation == pred.lower() or requested_relation in pred_label)
                    )
                    relationships.append({
                        "code": pred,
                        "label": self.predicate_labels.get(pred, ""),
                        "is_requested_relation": is_requested
                    })

        return relationships


def validate(input_path, output_path):
    validator = NCItValidator()

    with open(input_path, encoding='utf-8') as f:
        extractions = json.load(f)

    results = []
    for rel in tqdm(extractions, desc="Validating"):
        source_ids = validator.resolve_entity(rel['source'])
        target_ids = validator.resolve_entity(rel['target'])

        result = {
            "source": rel['source'],
            "target": rel['target'],
            "requested_relation": rel['relation'],
            "source_ids": source_ids,
            "target_ids": target_ids,
            "valid_entities": bool(source_ids and target_ids),
            "requested_relation_found": False,
            "all_relationships": []
        }

        if source_ids and target_ids:
            for sid in source_ids:
                for tid in target_ids:
                    rels = validator.find_relationships(sid, tid, rel['relation'])
                    if rels:
                        result['all_relationships'].extend([{
                            "source_id": sid,
                            "target_id": tid,
                            **r
                        } for r in rels])
                        if any(r['is_requested_relation'] for r in rels):
                            result['requested_relation_found'] = True

        results.append(result)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved validation output to {output_path}")


if __name__ == "__main__":
    validate(
        input_path="./output/extracted_relationships.json",
        output_path="./output/validated_relationships.json"
    )