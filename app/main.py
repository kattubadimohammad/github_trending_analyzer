import os
from typing import Dict, List
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse
from cachetools import TTLCache
from pydantic import BaseModel, Field

from utils import calculate_similarity
from models import Node, Edge, GraphData

# --- Configuration ---
GITHUB_TRENDING_URL = "https://github.com/trending"
CACHE_TTL = 3600  # 1 hour


# --- FastAPI App ---
app = FastAPI(
    title="GitHub Trending Repository Analyzer",
    description="Fetches and analyzes trending repositories from GitHub, providing data for graph visualization.",
    version="1.0.0",
)

# --- Cache ---
cache = TTLCache(maxsize=128, ttl=CACHE_TTL)


# --- Helper Functions ---
async def fetch_github_trending(language: str) -> str:
    url = f"{GITHUB_TRENDING_URL}/{language}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.text


def extract_repo_data(html_content: str, language: str, repo_limit: int) -> List[Dict]:
    soup = BeautifulSoup(html_content, "html.parser")
    repo_elements = soup.find_all("article", class_="Box-row")
    repos = []
    for i, repo_element in enumerate(repo_elements):
        if i >= repo_limit:
            break
        try:
            header = repo_element.find("h2")
            if not header:
                continue
            repo_name_element = header.find("a")
            repo_name = repo_name_element.text.strip().replace("\n", "").replace(" ", "")
            description_element = repo_element.find("p", class_="col-8 color-fg-muted my-1")
            description = description_element.text.strip() if description_element else "No description provided."
            stars_element = repo_element.find("a", href=lambda href: href and "/stargazers" in href)
            stars = int(stars_element.text.strip().replace(",", "")) if stars_element else 0
            forks_element = repo_element.find("a", href=lambda href: href and "/network/members" in href)
            forks = int(forks_element.text.strip().replace(",", "")) if forks_element else 0
            lang_element = repo_element.find("span", itemprop="programmingLanguage")
            repo_language = lang_element.text.strip().lower() if lang_element else "unknown"
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
            print(f"Error processing repo: {e}")
    return repos


async def fetch_repository_topics(repo_name: str) -> List[str]:
    url = f"https://github.com/{repo_name.strip()}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            topics = soup.find_all("a", class_="topic-tag topic-tag-link f6 my-1")
            return [tag.text.strip().lower() for tag in topics]
        except Exception:
            return []


async def analyze_repositories(language: str, repo_limit: int) -> GraphData:
    html_content = await fetch_github_trending(language)
    repos_data = extract_repo_data(html_content, language, repo_limit)
    nodes = [Node(**repo) for repo in repos_data]
    repo_topics: Dict[str, List[str]] = {}

    for repo in repos_data:
        repo_topics[repo["id"]] = await fetch_repository_topics(repo["id"])

    edges = []
    for i in range(len(repos_data)):
        for j in range(i + 1, len(repos_data)):
            repo1 = repos_data[i]
            repo2 = repos_data[j]
            topics1 = set(repo_topics.get(repo1["id"], []))
            topics2 = set(repo_topics.get(repo2["id"], []))
            common = topics1.intersection(topics2)
            similarity = calculate_similarity(repo1["description"], repo2["description"])
            weight = len(common)
            if weight > 0:
                edges.append(Edge(source=repo1["id"], target=repo2["id"], weight=weight))

    return GraphData(nodes=nodes, edges=edges)


# --- API Endpoint ---
@app.get(
    "/analyze/github/trending/{language}",
    response_model=GraphData,
)
async def get_trending_repos(
    language: str = Path(..., title="Programming language to analyze"),
    repo_limit: int = 10,
) -> JSONResponse:
    if not language:
        raise HTTPException(status_code=400, detail="Language must be provided.")
    if language.lower() in ("all", "unknown"):
        raise HTTPException(status_code=400, detail="Language 'all' or 'unknown' is not supported.")
    if repo_limit <= 0:
        raise HTTPException(status_code=400, detail="repo_limit must be greater than 0.")
    cache_key = f"{language}:{repo_limit}"
    if cache_key in cache:
        return JSONResponse(content=cache[cache_key])
    graph_data = await analyze_repositories(language, repo_limit)
    cache[cache_key] = graph_data.dict()
    return JSONResponse(content=graph_data.dict())


@app.on_event("startup")
async def startup_event():
    print("App has started!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
