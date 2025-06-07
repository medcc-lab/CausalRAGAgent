import json
import re
import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_core.prompts import PromptTemplate
import tiktoken

# === CONFIGURATION ===
#SPECIFIC_FILE = "s00262-020-02736-z.txt"
#CORE_ENTITY = "breast cancer"  # Update this per document
#OUTPUT_DIR = Path("./output")
#CLEANED_PAPERS_DIR = Path("./dataset/cleaned_papers")

# === LLM INITIALIZATION ===
# llm = OllamaLLM(
#     model="llama3.3:latest",
#     stop=["<Think>", "</Think>", "<|im_end|>"]
# )

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("API_KEY")

relationship_extraction_prompt = PromptTemplate.from_template("""
Analyze this biomedical text and extract precise relationships between entities with scientific rigor.
The text may contain technical terminology and entity names with minor variations — use contextual understanding to match them.

Return ONLY a valid JSON array following this exact schema:
[{{
  "source": "EntityName (normalized form)",
  "relation": "SpecificBiomedicalRelation",
  "target": "EntityName (normalized form)",
}}]

Text: {text}
Entities: {entities}
Core Topic Entity: {core_entity}

Focus on these biomedical relationship types (ordered by priority):
1. Molecular interactions: binds_to, inhibits, activates, phosphorylates, regulates_expression_of  
2. Pharmacological: treats, contraindicates, metabolizes, potentiates, side_effect_of  
3. Diagnostic: diagnoses, biomarker_for, prognostic_indicator_of  
4. Pathological: causes, predisposes_to, complication_of, manifestation_of  
5. Genetic: associated_with, variant_of, encodes, coexpressed_with  
6. Anatomical: located_in, part_of, connected_to  

Extraction rules:
- Only extract relationships explicitly stated in the text
- For ambiguous cases, prefer more specific relationship types
- Split compound entities into separate relationships
- Try to extract meaningful relationships for as many entities as possible, but never extract unsupported relationships
- Ensure at least one extracted relationship involves the core topic entity: "{core_entity}"
- However, avoid making all relationships about "{core_entity}" unless the text explicitly supports that.
- Include diverse and relevant biomedical relationships, even if they do not directly reference "{core_entity}"

IMPORTANT: You MUST return ONLY a valid JSON array following the exact schema above.
Do not include any additional text, explanations, or markdown formatting.
The output should begin with [ and end with ].
                                                              
Example Output:
[
  {{
    "source": "metformin",
    "relation": "inhibits",
    "target": "mTORC1"
  }},
  {{
    "source": "BRCA1",
    "relation": "associated_with",
    "target": "breast cancer"
  }}
]

Output ONLY the JSON array with no additional commentary:
""")


#relationship_chain = relationship_extraction_prompt | llm

def trim_to_token_limit(text, max_tokens=22000, model_name="gpt-4o"):
    enc = tiktoken.encoding_for_model(model_name)
    tokens = enc.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return enc.decode(tokens)

def extract_relationships(text, entities, core_entity, backend="ollama"):
    try:
        # Dynamically choose backend
        if backend == "openai":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
        else:
            from langchain_ollama import OllamaLLM
            llm = OllamaLLM(model="llama3.3:latest", stop=["<Think>", "</Think>", "<|im_end|>"])

        chain = relationship_extraction_prompt | llm

        response = chain.invoke({
            "text": trim_to_token_limit(text),
            "entities": json.dumps(entities),
            "core_entity": core_entity
        })

        # Get the content from the response object
        response_content = response.content if hasattr(response, "content") else str(response)
        
        # Print raw response for debugging
        print("\n=== RAW RESPONSE ===")
        print(response_content)
        print("===================\n")
        
        # Clean the response - remove markdown code blocks if present
        cleaned_response = re.sub(r'```json|```', '', response_content).strip()
        
        # Fix common JSON issues before parsing
        def fix_json(json_str):
            # Remove trailing commas
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            # Remove comments
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
            json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
            return json_str

        fixed_response = fix_json(cleaned_response)
        
        # Parse the JSON response
        relationships = None
        try:
            relationships = json.loads(fixed_response)
        except json.JSONDecodeError:
            json_match = re.search(r'(\[.*\]|\{.*\})', fixed_response, re.DOTALL)
            if json_match:
                try:
                    relationships = json.loads(fix_json(json_match.group(1)))
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to parse JSON: {str(e)}")

        if relationships is None:
            raise ValueError("No valid JSON found in response")

        # Normalize to list format
        if isinstance(relationships, dict):
            relationships = [relationships]
        elif not isinstance(relationships, list):
            raise ValueError("Response is not a JSON array or object")

        # Validate and clean relationships
        valid_relationships = []
        for rel in relationships:
            if isinstance(rel, dict) and all(key in rel for key in ["source", "relation", "target"]):
                valid_relationships.append({
                    "source": rel["source"].strip(),
                    "relation": rel["relation"].strip(),
                    "target": rel["target"].strip()
                })

        # Print final output
        print("\n=== EXTRACTED RELATIONSHIPS ===")
        print(json.dumps(valid_relationships, indent=2))
        print("==============================\n")
        
        return valid_relationships

    except Exception as e:
        print(f"❌ Error in relationship extraction: {str(e)}")
        if 'response_content' in locals():
            print(f"Raw response was: {response_content[:1000]}")
        return []

    
def read_text_file(file_path):
    """Read content from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"Failed to read text file: {str(e)}")

def main():
    output_dir = Path("./output")
    cleaned_papers_dir = Path("./dataset/cleaned_papers")  
    
    entities_path = output_dir / "final_entities.json"
    try:
        with open(entities_path, "r") as f:
            entities = json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load entities: {str(e)}")


    text_file_path = cleaned_papers_dir / SPECIFIC_FILE  
    try:
        research_text = read_text_file(text_file_path)  
    except Exception as e:
        raise ValueError(f"Failed to read text file: {str(e)}")

    relationships = extract_relationships(research_text, entities)
    
    output_path = output_dir / "extracted_relationships.json"
    with open(output_path, "w") as f:
        json.dump(relationships, f, indent=2)
    
    print(f"Successfully extracted {len(relationships)} relationships")

if __name__ == "__main__":
    main()