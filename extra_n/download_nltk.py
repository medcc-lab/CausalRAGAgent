# setup_nltk.py
import nltk

def download_nltk_resources():
    print("⏳ Downloading required NLTK resources...")
    nltk.download('punkt')
    nltk.download('punkt_tab')  # Additional resource needed
    print("✅ All NLTK resources downloaded successfully!")

if __name__ == "__main__":
    download_nltk_resources()