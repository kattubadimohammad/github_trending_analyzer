# GitHub Trending Repository Analyzer

A FastAPI application that fetches and analyzes trending repositories from GitHub for a specified programming language. It provides insights into the repositories and their relationships based on shared topics, making the data suitable for graph visualization.

## Live Deployment

Access the GitHub Trending Repository Analyzer **[here](https://github-trending-analyzer-service.onrender.com)**.

- **Root Endpoint** (`/`): Displays a welcome message to verify the service is live.
- **Trending Repositories Endpoint** (`/analyze/github/trending/{language}`): Fetches and analyzes trending repositories for a specified programming language.

---

## Features

1. **Fetch GitHub Trending Repositories**
   - Extracts repository details including:
     - Name (owner/repo)
     - Description
     - Number of stars
     - Number of forks
     - Programming language
   - Ensures proper formatting of repository names.

2. **Graph-Based JSON Output**
   - Represents repositories as nodes.
   - Includes relationships (edges) between repositories based on shared topics and semantic similarities.

3. **Caching**
   - Uses a Time-to-Live (TTL) cache to prevent redundant requests to GitHub.

4. **Error Handling**
   - Handles network issues, invalid requests, and GitHub rate limits gracefully.

---

## Setup

Follow these steps to set up the application locally:

### 1. Clone the Repository
```bash
git clone https://github.com/kattubadimohammad/github_trending_analyzer.git
cd github_trending_analyzer

2. Create a Virtual Environment (Optional but Recommended)
bash
python3 -m venv venv
# Activate the virtual environment:
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
3. Install Dependencies
bash
pip install -r requirements.txt
4. Run the Application
bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
API Usage
Base URL
If running locally:

http://localhost:8000
Deployed on Render:

https://github-trending-analyzer-service.onrender.com
Endpoints
Root Endpoint
GET /

Returns a welcome message to verify the service is live.

Analyze Trending Repositories
GET /analyze/github/trending/{language}

Path Parameter:

language: The programming language to analyze (e.g., python, javascript).

Query Parameter:

repo_limit (optional): The maximum number of repositories to analyze (default: 10).

Example Requests:

bash
curl -X GET "https://github-trending-analyzer-service.onrender.com/analyze/github/trending/python"
curl -X GET "https://github-trending-analyzer-service.onrender.com/analyze/github/trending/python?repo_limit=5"
Example Response:

json
{
  "nodes": [
    {"id": "owner1/repo1", "description": "...", "stars": 1234, "forks": 567, "language": "python"},
    {"id": "owner2/repo2", "description": "...", "stars": 876, "forks": 234, "language": "python"}
  ],
  "edges": [
    {"source": "owner1/repo1", "target": "owner2/repo2", "weight": 2}
  ]
}
Deployment on Render
To deploy this application on Render, follow these steps:

Create a Render Account at Render.com.

Create a New Web Service:

Connect your GitHub repository.

Set the following commands:

Build Command: pip install -r requirements.txt

Start Command: uvicorn app.main:app --host 0.0.0.0 --port 10000

Set the environment variable PORT to 10000.

Deploy the Service:

Monitor logs to ensure the service starts successfully.

Access the deployed app using the URL provided by Render.

How It Works
Web Scraping:

The app fetches GitHub’s trending page for the given programming language using httpx.

Parses HTML with BeautifulSoup to extract repository data.

Data Analysis:

Represents repositories as nodes.

Computes relationships (edges) based on shared topics.

Graph-Based JSON Output:

Nodes: Repository details.

Edges: Connections between repositories with a weight representing shared topics or semantic similarities.

Caching:

Results are cached for one hour to minimize redundant requests.

Development and Contributions
Testing
To run tests (if implemented):

bash
pytest tests
Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.

Acknowledgments
FastAPI for creating modern APIs with Python.

BeautifulSoup for HTML parsing.

Render for deployment.

License
This project is licensed under the MIT License. See the LICENSE file for details.


This README is complete, informative, and well-structured. Let me know if you'd like to tweak any specific section!


