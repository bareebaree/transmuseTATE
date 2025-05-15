

import json
from tokenizers import Tokenizer, models, trainers, pre_tokenizers
from tokenizers.pre_tokenizers import Whitespace

# Collect all REMI token strings from .jsonl
remi_lines = []
with open("results/all_remi.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        tokens = data["tokens"]
        remi_lines.append(tokens)

# Write them to a temporary file for tokeniser training
training_file = "results/remi_for_tokenizer.txt"
with open(training_file, "w", encoding="utf-8") as f:
    for line in remi_lines:
        f.write(line.strip() + "\n")

# Build and train tokeniser
tokenizer = Tokenizer(models.WordLevel(unk_token="[UNK]"))
tokenizer.pre_tokenizer = Whitespace()

trainer = trainers.WordLevelTrainer(
    vocab_size=512,
    special_tokens=["[PAD]", "[CLS]", "[SEP]", "[MASK]", "[UNK]"]
)

tokenizer.train(files=[training_file], trainer=trainer)
tokenizer.save("remi_tokenizer.json")

print("✅ Tokenizer trained and saved to remi_tokenizer.json")

