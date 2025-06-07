import pickle
from collections import defaultdict
from pathlib import Path
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDFS, SKOS

# Optional synonym property from OBO ontologies
OBOINOWL = Namespace("http://www.geneontology.org/formats/oboInOwl#")

def normalize_text(text):
    """Lowercase and strip special characters for consistent indexing."""
    import re
    text = text.lower()
    text = re.sub(r'[\(\)\[\],:;]', '', text)  # remove punctuation
    text = re.sub(r'\s{2,}', ' ', text)       # multiple spaces to single
    return text.strip()

class NCItInspector:
    def __init__(self, owl_path="./ncit/Cancer_Thesaurus.owl"):
        self.g = Graph()
        self.g.parse(owl_path)
        print(f"Loaded ontology with {len(self.g)} triples")

    def build_and_save_indexes(self, output_path="ncit_indexes.pkl"):
        print("🔍 Building entity and relationship indexes...")
        
        entity_index = defaultdict(list)     # {text: [C12345, ...]}
        rel_index = defaultdict(set)         # {(C123, C456): {rel_code}}
        predicate_labels = {}                # {rel_code: label}

        for s, p, o in self.g:
            # --- ENTITY LABEL INDEX ---
            if p in [RDFS.label, SKOS.altLabel, OBOINOWL.hasExactSynonym]:
                if isinstance(s, URIRef) and isinstance(o, str):
                    concept_id = s.split("#")[-1]  # e.g. C12345
                    norm_text = normalize_text(o)
                    if norm_text:
                        entity_index[norm_text].append(concept_id)

            # --- RELATIONSHIP INDEX ---
            if isinstance(s, URIRef) and isinstance(o, URIRef):
                subj_id = s.split("#")[-1]
                obj_id = o.split("#")[-1]
                pred_id = p.split("#")[-1]
                rel_index[(subj_id, obj_id)].add(pred_id)

                # Label of relation
                if pred_id not in predicate_labels:
                    label = next(self.g.objects(p, RDFS.label), None)
                    if isinstance(label, str):
                        predicate_labels[pred_id] = label

        print(f"✅ Indexed {len(entity_index)} terms and {len(rel_index)} relationships")

        # Save
        with open(output_path, 'wb') as f:
            pickle.dump({
                "entity_index": dict(entity_index),
                "rel_index": dict(rel_index),
                "predicate_labels": predicate_labels
            }, f)

        print(f"📦 Saved index to {output_path}")

if __name__ == "__main__":
    inspector = NCItInspector()
    inspector.build_and_save_indexes()
