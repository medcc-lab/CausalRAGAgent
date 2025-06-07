from transformers import AutoConfig

# Check config without loading full model
config = AutoConfig.from_pretrained("d4data/biomedical-ner-all")
print("Original label mapping:", config.label2id)