import json
import re
from pathlib import Path
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
import os 
# Optional: select your model backend
USE_OPENAI = False  # Set to True to use OpenAI GPT-4o

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("API_KEY")

if USE_OPENAI:
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
else:
    from langchain_ollama import OllamaLLM
    llm = OllamaLLM(model="", temperature=0, stop=["<|im_end|>"])

# Prompt template
prompt_template = """
You are verifying a biomedical relationship inside a scientific paper.

Context:
{context}

Claim to verify:
"Entity '{source}' is related to entity '{target}' via relation '{relation}'."

Answer these questions strictly:
1. Does the source entity appear in the context? (yes/no)
2. Does the target entity appear in the context? (yes/no)
3. Is the relationship clearly described? (yes/no)
4. Briefly explain why or why not (1-2 sentences).

Respond only in this exact JSON format:
{{
  "source_present": true,
  "target_present": true,
  "relationship_valid": false,
  "reason": "..."
}}
"""

# Load helpers
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def normalize(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("‑", "-").replace("–", "-").replace("−", "-")
    return text.strip()

def filter_context(text, keywords, max_chars=12000):
    sentences = sent_tokenize(text)
    filtered = [s for s in sentences if any(k in s.lower() for k in keywords)]
    return " ".join(filtered)[:max_chars]

# Paths
output_root = Path("./output")
text_root = Path("./dataset/cleaned_papers")
validation_out_dir = Path("./llm_validations")
validation_out_dir.mkdir(parents=True, exist_ok=True)

# Main loop
for folder in output_root.iterdir():
    if not folder.is_dir():
        continue

    paper_id = folder.name
    print(f"\n📄 Validating relationships in: {paper_id}")

    txt_path = text_root / f"{paper_id}.txt"
    val_path = folder / "validated_relationships.json"

    if not txt_path.exists() or not val_path.exists():
        print(f"⚠️ Skipping {paper_id} — missing .txt or validation file")
        continue

    text = normalize(read_text(txt_path))
    relationships = load_json(val_path)

    validated_output = []

    for rel in relationships:
        source = rel.get("source", "")
        target = rel.get("target", "")
        relation = rel.get("requested_relation", "")

        # Generate prompt
        keywords = [source.lower(), target.lower()]
        context = filter_context(text, keywords)
        prompt = prompt_template.format(
            context=context,
            source=source,
            target=target,
            relation=relation
        )

        # Query the model
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            
            
            print(f"Raw response: {content}")
            
            content = re.sub(r"```json|```", "", content).strip()
            data = json.loads(content)
            data.update({
                "source": source,
                "target": target,
                "relation": relation
            })
            validated_output.append(data)
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error for ({source}, {relation}, {target}): {e}\nResponse was: {content}")
        except Exception as e:
            print(f"❌ Error validating ({source}, {relation}, {target}): {str(e)}")

    # Save result outside output folder
    out_path = validation_out_dir / f"{paper_id}_llm_validated.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(validated_output, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved: {out_path} ({len(validated_output)} validated)")
