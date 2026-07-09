# PyQual

## Project Description

PyQual is a primitive client that I wrote at work to facilitate working with Qualtrics.

## Getting Started

1. Clone this repo.
2. Install `uv` if you do not already have it:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Create/sync the local environment:

   ```bash
   uv sync
   ```

   To include development dependencies:

   ```bash
   uv sync --extra dev
   ```

4. If you prefer installing into your active environment instead, use an editable install:

   ```bash
   uv pip install -e .
   ```

5. Run the tests:

   ```bash
   uv run python -m unittest discover tests -v
   ```

## Contributing Members

**Team Leads (Contacts) : [Sebastian Fest](https://github.com/sebfest)**
