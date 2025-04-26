import os
import time
from typing import Dict, List
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse
from cachetools import TTLCache
from pydantic import BaseModel, Field
import logging

logging.basicConfig(level=logging.DEBUG)

# --- Configuration ---
GITHUB_TRENDING_URL = "https://github.com/trending"
CACHE_TTL = 3600  # 1 hour
DEFAULT_REPO_LIMIT = 10

# --- Models ---
class Node(BaseModel):
    id: str = Field(..., description="Repository name (owner/repo)")
    description: str = Field(..., description="Repository description")
    stars: int = Field(..., description="Number of stars")
    forks: int = Field(..., description="Number of forks")
    language: str = Field(..., description="Programming language")

class Edge(BaseModel):
    source: str = Field(..., description="Source repository name")
    target: str = Field(..., description="Target repository name")
    weight: float = Field(..., description="Number of shared topics (or semantic similarity)")

class GraphData(BaseModel):
    nodes: List[Node] = Field(..., description="List of repository nodes")
    edges: List[Edge] = Field(..., description="List of connections between repositories")

# --- FastAPI App ---
app = FastAPI(
    title="GitHub Trending Repository Analyzer",
    description="Fetches and analyzes trending repositories from GitHub, providing data for graph visualization.",
    version="1.0.0",
)

# --- Cache ---
cache = TTLCache(maxsize=128, ttl=CACHE_TTL)

# --- Helper Functions ---
async def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.text

async def fetch_github_trending(language: str) -> str:
    url = f"{GITHUB_TRENDING_URL}/{language}"
    try:
        return await fetch_html(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trending repositories: {e}")

def extract_repo_data(html_content: str, language: str, repo_limit: int) -> List[Dict]:
    soup = BeautifulSoup(html_content, "html.parser")
    repo_elements = soup.find_all("article", class_="Box-row")
    repos = []

    for repo_element in repo_elements[:repo_limit]:
        try:
            header = repo_element.find("h2")
            repo_name_element = header.find("a") if header else None
            if not repo_name_element:
                continue

            repo_name = ' '.join(repo_name_element.text.split())
            description_element = repo_element.find("p", class_="col-8 color-fg-muted my-1")
            description = description_element.text.strip() if description_element else "No description provided."

            stars_element = repo_element.find("a", href=lambda href: href and "/stargazers" in href)
            stars = int(stars_element.text.strip().replace(",", "")) if stars_element else 0

            forks_element = repo_element.find("a", href=lambda href: href and "/network/members" in href)
            forks = int(forks_element.text.strip().replace(",", "")) if forks_element else 0

            language_element = repo_element.find("span", itemprop="programmingLanguage")
            repo_language = language_element.text.strip().lower() if language_element else "unknown"

            if repo_language != language.lower():
                continue

            repos.append({
                "id": repo_name,
                "description": description,
                "stars": stars,
                "forks": forks,
                "language": repo_language,
            })
        except Exception as e:
            print(f"Error processing repo element: {e}")
            continue
    return repos

async def fetch_repository_topics(repo_name: str) -> List[str]:
    url = f"https://github.com/{repo_name}"
    try:
        html_content = await fetch_html(url)
        soup = BeautifulSoup(html_content, "html.parser")
        topics_elements = soup.find_all("a", class_="topic-tag")
        return [tag.text.strip() for tag in topics_elements]
    except Exception as e:
        print(f"Error fetching topics for {repo_name}: {e}")
        return []

async def fetch_all_topics_parallel(repos_data: List[Dict]) -> Dict[str, List[str]]:
    """Fetch topics for all repositories concurrently."""
    from asyncio import gather

    tasks = [fetch_repository_topics(repo["id"]) for repo in repos_data]
    topics_list = await gather(*tasks, return_exceptions=True)

    repo_topics = {}
    for repo, topics in zip(repos_data, topics_list):
        if isinstance(topics, Exception):
            repo_topics[repo["id"]] = []
        else:
            repo_topics[repo["id"]] = topics
    return repo_topics

def calculate_similarity(desc1: str, desc2: str) -> float:
    words1 = set(desc1.lower().split())
    words2 = set(desc2.lower().split())
    common_words = words1.intersection(words2)
    total_unique_words = len(words1.union(words2))
    return len(common_words) / total_unique_words if total_unique_words else 0.0

async def analyze_repositories(language: str, repo_limit: int) -> GraphData:
    html_content = await fetch_github_trending(language)
    repos_data = extract_repo_data(html_content, language, repo_limit)
    if not repos_data:
        raise HTTPException(status_code=404, detail="No trending repositories found.")

    nodes = [Node(**repo) for repo in repos_data]
    repo_topics = await fetch_all_topics_parallel(repos_data)

    edges: List[Edge] = []
    for i in range(len(repos_data)):
        for j in range(i + 1, len(repos_data)):
            repo1 = repos_data[i]
            repo2 = repos_data[j]

            common_topics_count = len(set(repo_topics.get(repo1["id"], [])) & set(repo_topics.get(repo2["id"], [])))
            if common_topics_count > 0:
                edges.append(Edge(
                    source=repo1["id"],
                    target=repo2["id"],
                    weight=float(common_topics_count)
                ))

    return GraphData(nodes=nodes, edges=edges)

# --- API Endpoints ---
@app.get(
    "/analyze/github/trending/{language}",
    response_model=GraphData,
    responses={
        200: {"description": "Successfully analyzed trending repositories."},
        400: {"description": "Invalid request."},
        404: {"description": "No repositories found."},
        500: {"description": "Internal server error."},
    },
)
async def get_trending_repos(
    language: str = Path(..., title="Programming language to analyze"),
    repo_limit: int = DEFAULT_REPO_LIMIT,
) -> JSONResponse:
    if not language or language.lower() in ("all", "unknown"):
        raise HTTPException(status_code=400, detail="Invalid language provided.")
    if repo_limit <= 0:
        raise HTTPException(status_code=400, detail="repo_limit must be greater than 0.")

    cache_key = f"{language}:{repo_limit}"
    if cache_key in cache:
        return JSONResponse(content=cache[cache_key])

    graph_data = await analyze_repositories(language, repo_limit)
    cache[cache_key] = graph_data.dict()
    return JSONResponse(content=graph_data.dict())

@app.get("/")
async def root():
    return {"message": "Welcome to the GitHub Trending Repository Analyzer!"}

@app.on_event("startup")
async def startup_event():
    pass

# --- Run the app ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
