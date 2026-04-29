import json
from pathlib import Path

data = json.loads(Path("data/dataset.json").read_text(encoding="utf-8"))
phish = [s for s in data if s["label"] == 1]
legit = [s for s in data if s["label"] == 0]
print("Total:", len(data), "phishing:", len(phish), "legit:", len(legit))

leg_names = {"Alice","Bob","Carol","David","Eve","Frank","Grace","Henry","Irene",
             "Jack","Karen","Leo","Mia","Nathan","Olivia","Pete"}
hard_p = [s for s in phish if any(s["text"].startswith(p+n+",") for n in leg_names for p in ["Hi ","Hey ","Dear "])]
hard_l = [s for s in legit if not any(s["text"].startswith(p+n+",") for n in leg_names for p in ["Hi ","Hey ","Dear "])]
print("Hard phishing samples (using internal names):", len(hard_p))
print("Hard legitimate samples (using external names):", len(hard_l))

print("\n=== HARD PHISHING sample (label=1, looks internal) ===")
if hard_p:
    print(hard_p[0]["text"][:350])

print("\n=== HARD LEGITIMATE sample (label=0, looks like phishing) ===")
if hard_l:
    print(hard_l[0]["text"][:350])
