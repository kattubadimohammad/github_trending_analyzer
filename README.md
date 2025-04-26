# GitHub Trending Repository Analyzer
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
    -   `repo_limit`: (Optional) The maximum number of repositories to analyze. Default is 10.

Example:

-   `http://localhost:8000/analyze/github/trending/python`
-   `http://localhost:8000/analyze/github/trending/python?repo_limit=5`

The API returns a JSON response with the following structure:

```json
{
  "nodes": [
    {
      "id": "owner1/repo1",
      "description": "...",
      "stars": 1234,
      "forks": 567,
      "language": "python"
    },
    // ... more nodes
  ],
  "edges": [
    {
      "source": "owner1/repo1",
      "target": "owner2/repo2",
      "weight": 2
    },
    // ... more edges
  ]
}
```

## Deployment on Render

1.  Create a Render account.
2.  Create a new web service.
3.  Connect your GitHub repository.
4.  Set the build and start commands:
    -   **Build Command:** `pip install -r requirements.txt`
    -   **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port 10000`
5.  Set the environment variable `PORT` to `10000`.
6.  Deploy the web service.
