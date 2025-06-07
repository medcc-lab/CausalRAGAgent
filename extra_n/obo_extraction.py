import json
import re

def parse_obo(file_path):
    terms = []
    current_term = {}

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            
            # New term block starts
            if line == "[Term]":
                if current_term:  # Save previous term
                    terms.append(current_term)
                current_term = {"id": "", "name": "", "synonyms": []}
            
            # Extract ID
            elif line.startswith("id:"):
                current_term["id"] = line.split("id: ")[1]
            
            # Extract Name
            elif line.startswith("name:"):
                current_term["name"] = line.split("name: ")[1]
            
            # Extract Synonyms
            elif line.startswith("synonym:"):
                match = re.search(r'synonym: "(.*?)"', line)
                if match:
                    current_term["synonyms"].append(match.group(1))

    # Append last term
    if current_term:
        terms.append(current_term)

    return terms

# File path where the OBO file is stored
file_path = "obo/NCI_Thesaurus.obo"

# Convert to JSON
parsed_terms = parse_obo(file_path)
json_output = json.dumps(parsed_terms, indent=4)

# Save JSON to a file
with open("output.json", "w", encoding="utf-8") as json_file:
    json_file.write(json_output)

print("JSON extraction completed! ✅")
