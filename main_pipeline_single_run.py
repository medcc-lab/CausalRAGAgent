import json
from pathlib import Path
import argparse

# Import all your agents
from main_pipeline import main as main_pipeline
from pdf_cleaner import process_all_pdfs
from agent_entity_extractor import extract_entities_from_file
from entity_cleaner import clean_entities
from agent_relationship_extractor import extract_relationships, read_text_file
from ontology_validator import validate
from agent_neo4j_adder import add_to_neo4j

# Path configurations
CLEANED_DIR = Path("./dataset/cleaned_papers")
RESEARCH_DIR = Path("./dataset/research_papers")
OUTPUT_ROOT = Path("./output")

def show_menu():
    print("\n=== Step Selection ===")
    print("1. PDF Cleaning")
    print("2. Entity Extraction")
    print("3. Entity Cleaning")
    print("4. Relationship Extraction")
    print("5. Ontology Validation")
    print("6. Neo4j Storage")
    print("7. Run Full Pipeline")
    print("0. Exit")
    return input("Select step to execute (0-7): ")

def run_selected_step(choice, core_entity=None, backend=None):
    if choice == "1":
        print("\n🔧 Running PDF Cleaning...")
        process_all_pdfs(RESEARCH_DIR, CLEANED_DIR)
    
    elif choice == "2":
        print("\n🔍 Running Entity Extraction...")
        for txt_file in CLEANED_DIR.glob("*.txt"):
            paper_id = txt_file.stem
            output_dir = OUTPUT_ROOT / paper_id
            extract_entities_from_file(txt_file.name, output_dir)
    
    elif choice == "3":
        print("\n🧹 Running Entity Cleaning...")
        for folder in OUTPUT_ROOT.iterdir():
            if folder.is_dir():
                input_path = folder / "extracted_entities.json"
                cleaned_output = folder / "cleaned_entities.json"
                final_output = folder / "final_entities.json"
                if input_path.exists():
                    clean_entities(input_path, cleaned_output, final_output)
    
    elif choice == "4":
        if not core_entity:
            core_entity = input("Enter core entity (e.g. 'breast cancer'): ").strip()
        if not backend:
            backend = input("Choose backend (ollama/openai): ").strip()
        
        print(f"\n🔗 Running Relationship Extraction (Core: {core_entity})...")
        for folder in OUTPUT_ROOT.iterdir():
            if folder.is_dir():
                txt_path = CLEANED_DIR / f"{folder.name}.txt"
                entity_path = folder / "final_entities.json"
                output_path = folder / "extracted_relationships.json"
                
                if txt_path.exists() and entity_path.exists():
                    text = read_text_file(txt_path)
                    with open(entity_path, "r") as f:
                        entities = json.load(f)
                    relationships = extract_relationships(text, entities, core_entity, backend)
                    with open(output_path, "w") as f:
                        json.dump(relationships, f, indent=2)
    
    elif choice == "5":
        print("\n🧪 Running Ontology Validation...")
        for folder in OUTPUT_ROOT.iterdir():
            if folder.is_dir():
                input_path = folder / "extracted_relationships.json"
                output_path = folder / "validated_relationships.json"
                if input_path.exists():
                    validate(str(input_path), str(output_path))
    
    elif choice == "6":
        print("\n🛢️ Storing in Neo4j...")
        for folder in OUTPUT_ROOT.iterdir():
            if folder.is_dir():
                rel_path = folder / "validated_relationships.json"
                if rel_path.exists():
                    add_to_neo4j(paper_name=folder.name, relationships_path=rel_path)
    
    elif choice == "7":
        print("\n🚀 Initializing Full Pipeline...")
        main_pipeline()  # Call the complete pipeline function

def main():
    while True:
        choice = show_menu()
        if choice == "0":
            print("Exiting...")
            break
        if choice not in ["1", "2", "3", "4", "5", "6", "7"]:
            print("Invalid choice!")
            continue
        
        run_selected_step(choice)

if __name__ == "__main__":
    main()