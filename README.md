# BC5CDR XML → JSON Converter

Convert the **BioCreative V CDR (BC5CDR)** BioC XML files into a compact, analysis-friendly JSON format.

> This repo contains a single Python script that parses the official train/dev/test XML files and writes structured JSON with passages (title, abstract), entity spans, and document-level chemical–disease relations.

---

## Contents

- [Overview](#overview)
- [Input & Output](#input--output)
- [Installation](#installation)
- [Usage](#usage)
- [JSON Schema](#json-schema)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Repo Structure](#repo-structure)
- [Citing & License](#citing--license)

---

## Overview

The script uses **BeautifulSoup (lxml/xml)** to parse the BioC XML and produces a JSON file per split (`train`, `dev`, `test`).

It supports:

- Title & abstract extraction per document
- Entity extraction (name, type, MeSH IDs, character spans relative to the passage)
- Composite/Individual mention grouping
- Document-level relations (Chemical–Disease), mapping MeSH IDs to surface forms

---

## Input & Output

### Input (required)
- Official BC5CDR XML files (BioC format):
  - `CDR_TrainingSet.BioC.xml`
  - `CDR_DevelopmentSet.BioC.xml`
  - `CDR_TestSet.BioC.xml`

### Output (produced)
- One JSON per split, written to `output/` (configurable via code):
  - `train_set_preprocessed.json`
  - `dev_set_preprocessed.json`
  - `test_set_preprocessed.json`

Each file is an array of document objects; see the [JSON Schema](#json-schema).

---

## Installation

```bash
# 1) (Recommended) create a virtual environment
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2) Install deps
pip install beautifulsoup4 lxml
```

> The standard library `xml.dom.minidom` is used for optional XML "prettify"; no extra install required.

---

## Usage

1) **Adjust file paths** in `BC5CDR.__init__` to point at your local XML files. For example:

```python
splits = {
    "train": Path("/path/to/CDR_TrainingSet.BioC.xml"),
    "test": Path("/path/to/CDR_TestSet.BioC.xml"),
    "dev":  Path("/path/to/CDR_DevelopmentSet.BioC.xml")
}
```

Also optionally change the output directory:

```python
self.output_save_path = Path("./output") / f"{split}_set_preprocessed.json"
```

2) **Run the converter** for a split:

```bash
python bc5cdr_to_json.py  # uses the split hardcoded in __main__
```

By default, the script’s `__main__` runs the **train** split. You can edit these lines to switch splits:

```python
# make instance
bc5cdr = BC5CDR(split="train")
# bc5cdr = BC5CDR(split="test")
# bc5cdr = BC5CDR(split="dev")

bc5cdr.prepare()
```

> 💡 *Optional:* You can quickly add CLI args so you can run `python bc5cdr_to_json.py --split train`. Example snippet:
>
> ```python
> import argparse
> if __name__ == "__main__":
>     parser = argparse.ArgumentParser()
>     parser.add_argument("--split", choices=["train","dev","test"], default="train")
>     args = parser.parse_args()
>     BC5CDR(split=args.split).prepare()
> ```

---

## JSON Schema

Each document in the output JSON has the following shape (simplified):

```jsonc
{
  "id": "PMID12345678",
  "title": "...",
  "abstract": "...",
  "title_entities": [
    {
      "entity_name": "Aspirin",
      "entity_type": "Chemical",
      "entity_MESH": ["D001241"],
      "entity_locations": [[0, 7]],
      "IndividualMention": [
        {
          "Individual_entity_name": "...",
          "Individual_entity_type": "Chemical",
          "Individual_entity_MESH": ["..."],
          "Individual_entity_locations": [[...]]
        }
      ]
    }
  ],
  "abstract_entities": [ /* same structure as title_entities */ ],
  "relations": [
    {
      "relation": "CID",
      "chemical": ["Aspirin", "Acetylsalicylic Acid"],
      "disease": ["Myocardial Infarction"]
    }
  ]
}
```

**Offsets:** `entity_locations` are computed relative to the passage (title or abstract), not the whole document. They are half-open intervals `[start, end)`.

**MeSH mapping:** For each relation, the script maps the MeSH IDs in the XML to sets of surface forms found elsewhere in the document.

---

## Examples

### Minimal programmatic use

```python
from bc5cdr_to_json import BC5CDR
bc5 = BC5CDR(split="dev")
bc5.prepare()  # writes ./output/dev_set_preprocessed.json
```

### Sample record (abridged)

```json
{
  "id": "12345678",
  "title": "Aspirin and heart disease",
  "abstract": "...",
  "title_entities": [ { "entity_name": "Aspirin", "entity_type": "Chemical", "entity_MESH": ["D001241"], "entity_locations": [[0,7]], "IndividualMention": [] } ],
  "abstract_entities": [ ... ],
  "relations": [ { "relation": "CID", "chemical": ["Aspirin"], "disease": ["Heart Diseases"] } ]
}
```

---

## Troubleshooting

- **Windows-specific `cls` call** clears the console between documents. On non-Windows systems, you can remove or guard it:
  ```python
  if os.name == "nt":
      os.system("cls")
  ```
- **Parser errors**: ensure `lxml` is installed; BeautifulSoup falls back to Python’s XML if not, which can be slower or stricter: `pip install lxml`.
- **Wrong offsets**: Offsets are computed as `location.offset - passage.offset` per the BioC spec. If you modify passage handling, keep the relative offset logic.
- **Large files**: Run from SSD and avoid debug prints if you add any; JSON writing is already pretty-printed (`indent=2`).

---

## Repo Structure

```
.
├─ bc5cdr_to_json.py
├─ output/
└─ README.md
```

> If you’re committing the generated JSON, consider adding a short note on its provenance (date, script commit hash, and original source version).

---

## Citing & License

- **Dataset:** If you use BC5CDR, please cite the original paper and follow their license and usage terms:
- **Code:** Unless you choose otherwise, this converter is released under the MIT License (see `LICENSE`).

---

## Acknowledgments

- Thanks to the BC5CDR organizers and dataset authors.
- This converter was authored by [Mahdi Khoshmaram](https://github.com/mahdi-khoshmaram).
