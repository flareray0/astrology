
# AGENT.md — Astrology Engine Professionalization Guide

## Purpose
This document instructs an AI coding agent (Codex / GPT Engineer / similar) how to upgrade the existing **astrology repository**
into a **professional‑grade local application** that can be cloned and run locally on Windows, Linux, or macOS.

The final result must allow a user to:

1. `git clone` the repository
2. install dependencies
3. run a local server
4. open a browser on `localhost`
5. generate astrology reports

The system must support:

- Natal
- Progressed
- Transit
- Triple Chart
- Synastry

with **high‑quality interpretation output**.

---

# High‑Level Goal

Transform the project from:

```
script-based astrology generator
```

into:

```
professional local astrology engine
+ local web interface
+ reproducible environment
```

---

# Required Architecture

```
astrology/
│
├── astrology.py
├── aspect_engine.py
├── interpretation_engine.py
├── report_engine.py
│
├── data/
│   ├── ephemeris/
│   └── results/
│
├── web/
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│
├── requirements.txt
├── AGENT.md
└── README.md
```

---

# Environment Setup

Use **Python 3.10+**

Create `requirements.txt` including:

```
pyswisseph
numpy
pandas
fastapi
uvicorn
jinja2
python-multipart
```

Install:

```
pip install -r requirements.txt
```

---

# Ephemeris Handling

Ensure Swiss Ephemeris files are loaded from:

```
data/ephemeris/
```

Code must set:

```
swe.set_ephe_path("data/ephemeris")
```

Agent must automatically detect `.se1` files already placed in the repository.

---

# Core Modules

## 1. aspect_engine.py

Responsible for:

- aspect detection
- orb calculation
- strength scoring

Aspect types:

```
conjunction
sextile
square
trine
opposition
```

Orb weighting:

```
strength = 1 - (orb / max_orb)
```

---

## 2. interpretation_engine.py

Transforms astrological data into narrative.

Pipeline:

```
astro data
↓
planet interaction
↓
psychological theme
↓
life manifestation
↓
action guidance
```

Functions:

```
interpret_planet_position()
interpret_aspect()
interpret_house_overlay()
translate_life_event()
synthesize_narrative()
```

---

## 3. report_engine.py

Responsible for assembling reports.

Supported report modes:

```
natal
progressed
transit
triple
synastry
```

Each report must contain:

```
core themes
aspect analysis
life interpretation
practical guidance
```

---

# Aspect Interpretation Quality

Aspect explanation must include:

1. Planet relationship
2. Aspect type meaning
3. Orb intensity
4. Psychological effect
5. Life manifestation
6. Practical advice

Example:

```
Mars sextile Saturn

Action and discipline cooperate.

Effort becomes structured progress.
This aspect often appears when sustained work produces visible results.

Advice:
Focus on consistent daily action rather than sudden bursts of effort.
```

---

# Chart Mode Behavior

## Natal

Focus on personality patterns.

## Progressed

Focus on inner development phase.

## Transit

Focus on current external events.

## Triple

Integrate natal + progressed + transit.

## Synastry

Focus on relationship dynamics.

---

# Local Web Interface

Create a minimal **FastAPI** server.

File:

```
web/app.py
```

Example:

```python
from fastapi import FastAPI
from astrology import run_report_by_mode

app = FastAPI()

@app.get("/")
def root():
    return {"status": "astrology engine running"}
```

Run with:

```
uvicorn web.app:app --reload
```

Access:

```
http://127.0.0.1:8000
```

---

# Minimal Web UI

`templates/index.html` must allow:

- input birth data
- choose report mode
- run report
- display generated interpretation

---

# CLI Mode

Users must also be able to run:

```
python astrology.py
```

and generate a report from terminal.

---

# Testing

After cloning repository, the following must work:

```
git clone <repo>
cd astrology
pip install -r requirements.txt
uvicorn web.app:app --reload
```

Then open browser:

```
http://127.0.0.1:8000
```

User should be able to generate charts.

---

# Performance Goals

Report generation time:

```
< 2 seconds
```

Interpretation quality:

```
professional astrology report level
```

---

# Code Quality

Agent must:

- keep functions modular
- avoid duplicated templates
- include docstrings
- keep interpretation dictionaries separate

---

# Deliverables

Agent must output:

1. modified repository structure
2. new modules
3. requirements.txt
4. FastAPI server
5. example usage
6. README instructions

---

# Final Success Criteria

A user must be able to:

```
git clone repo
pip install requirements
run server
open localhost
generate astrology reports
```

without additional manual setup.
