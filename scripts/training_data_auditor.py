import json

PATH = "finetune_data/training_data.jsonl"
REQUIRED_KEYS = ["summary", "urgency_score"]

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Checking {len(lines)} training examples\n")

problems = 0
for i, line in enumerate(lines):
    example = json.loads(line)
    completion = json.loads(example["messages"][1]["content"])

    missing_keys = [k for k in REQUIRED_KEYS if k not in completion]
    empty_values = [k for k, v in completion.items() if v == "" or v is None]

    if missing_keys or empty_values:
        problems += 1
        print(f"Row {i}: missing={missing_keys}, empty={empty_values}")

print(f"\n{problems} of {len(lines)} rows have issues")