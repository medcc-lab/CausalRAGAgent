import os
import requests

def download_ncit_owl(destination_folder="../ncit", filename="Cancer_Thesaurus.owl"):
    url = "https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/CURRENT/Cancer_Thesaurus.owl"
    os.makedirs(destination_folder, exist_ok=True)
    file_path = os.path.join(destination_folder, filename)
    print(f"Downloading NCIT Cancer_Thesaurus.OWL to {file_path} ...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download completed! ✅")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

if __name__ == "__main__":
    download_ncit_owl()
