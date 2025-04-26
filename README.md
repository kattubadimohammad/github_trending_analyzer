# GitHub Trending Repository Analyzer

A FastAPI application that fetches and analyzes trending repositories from GitHub for a specified programming language.

## Setup

1.  Clone the repository.
2.  Create a virtual environment (optional but recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```
3.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the application:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```

## Usage

The API endpoint is:

-   `GET /analyze/github/trending/{language}`

    -   `language`: The programming language to analyze (e.g., "python", "javascript").
