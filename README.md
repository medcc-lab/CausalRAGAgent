# With Agent(WA) Project - README

## Setup Instructions

1. **Create and Activate Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate
```

2. **Install Required Packages**

Make sure to install all dependencies (if a requirements.txt is present):

```bash
pip install -r ../m_GRAG/requirements.txt
```

3. **Run Initial Scripts**

Before starting the main pipeline, run the following scripts from the `extra_n` directory:

- `download_ntlk.py`  

Example:

```bash
python extra_n/download_ntlk.py
```

> **If you do not have `ncit_indexes.pkl` in the source(main) folder, you must run both `ontology_download.py` and `ontology_inspector.py` to generate it.**

If the automatic download fails, you can manually download the OWL file from https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/ and place it in the `ncit` folder. Make sure the file is named `Cancer_Thesaurus.owl` and has the `.owl` extension.

Alternatively, if you do not want to generate the index, a zipped `ncit_indexes.pkl` is provided in the `lib` folder. You can extract it and place it in the WA root directory.

**Before starting the project:**
- If you plan to use Ollama, make sure to start Ollama locally with `ollama serve`.
- If you plan to use OpenAI, ensure your API key is set in the `.env` file.
- You must also sign up for Neo4j Aura and put your Neo4j credentials in the `.env` file.

4. **Start the Project**

After completing the above steps, start the main pipeline:

```bash
python main_pipeline_single_run.py
```

---

**Note:**
- If you encounter missing dependencies, install them using pip.
- If you have problems with libraries or dependencies, a pre-built `venv` is provided as a zip file in the `lib` folder. You can extract it and use it directly:

```bash
unzip lib/venv.zip -d ./
source venv/bin/activate
```
