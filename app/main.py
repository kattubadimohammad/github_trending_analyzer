import os
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse
from cachetools import TTLCache
from pydantic import BaseModel, Field

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

async def fetch_github_trending(language: str) -> str:
    """
    Fetches the HTML content of the GitHub trending page for a given language.

    Args:
        language: The programming language to fetch trending repositories for.

    Returns:
        The HTML content of the trending page as a string.

    Raises:
        HTTPException: If the request fails or the response is not 200.
    """
    url = f"{GITHUB_TRENDING_URL}/{language}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",  # Add Accept-Language header
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()  # Raise for bad status codes
            return response.text
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error fetching {url}: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch {url}: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

def extract_repo_data(html_content: str, language: str, repo_limit: int) -> List[Dict]:
    """
    Extracts repository data from the HTML content of the GitHub trending page.

    Args:
        html_content: The HTML content to parse.
        language: The programming language.
        repo_limit: Maximum number of repos to extract

    Returns:
        A list of dictionaries, where each dictionary represents a repository.
        Returns an empty list if no repositories are found.
    """
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
            if not repo_name_element:
                continue
            repo_name = repo_name_element.text.strip()
            description_element = repo_element.find("p", class_="col-8 color-fg-muted my-1")
            description = description_element.text.strip() if description_element else "No description provided."
            stars_element = repo_element.find("a", href=lambda href: href and "/stargazers" in href)
            stars_text = stars_element.text.strip() if stars_element else "0"
            stars = int(stars_text.replace(",", ""))
            forks_element = repo_element.find("a", href=lambda href: href and "/network/members" in href)
            forks_text = forks_element.text.strip() if forks_element else "0"
            forks = int(forks_text.replace(",", ""))
            language_element = repo_element.find("span", itemprop="programmingLanguage")
            repo_language = language_element.text.strip().lower() if language_element else "Unknown"

            # Verify the language matches.  If it doesn't, skip.
            if repo_language != language.lower():
                continue

            repos.append({
                "name": repo_name,
                "description": description,
                "stars": stars,
                "forks": forks,
                "language": repo_language,
            })
        except Exception as e:
            print(f"Error processing repository: {e}") # Log error and continue

    return repos

async def fetch_repository_topics(repo_name: str) -> List[str]:
    """
    Fetches the topics/tags for a given repository from its GitHub page.

    Args:
        repo_name: The name of the repository (e.g., "owner/repo").

    Returns:
        A list of topic names.  Returns an empty list on error or if no topics.
    """
    url = f"https://github.com/{repo_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            topics_elements = soup.find_all("a", class_="topic-tag")  # Corrected class name
            topics = [topic.text.strip() for topic in topics_elements]
            return topics
        except httpx.RequestError as e:
            print(f"Error fetching topics for {repo_name}: {e}")
            return []
        except httpx.HTTPStatusError as e:
            print(f"Failed to fetch topics for {repo_name}: {e}")
            return []
        except Exception as e:
            print(f"Error processing topics for {repo_name}: {e}")
            return []
    return []

def calculate_similarity(desc1: str, desc2: str) -> float:
    """
    Calculates the semantic similarity between two text descriptions using a very basic approach.
    This is a placeholder for a more advanced method using the ChatGPT API or other NLP techniques.
    For this basic version, it returns a value between 0 and 1, representing the percentage of shared words.

    Args:
        desc1: The first text description.
        desc2: The second text description.

    Returns:
        A similarity score between 0 and 1.
    """
    words1 = set(desc1.lower().split())
    words2 = set(desc2.lower().split())
    common_words = words1.intersection(words2)
    total_unique_words = len(words1.union(words2))
    if total_unique_words == 0:
        return 0.0  # Handle empty descriptions
    return len(common_words) / total_unique_words

async def analyze_repositories(language: str, repo_limit: int) -> GraphData:
    """
    Fetches trending repositories for a language, analyzes them, and returns graph data.

    Args:
        language: The programming language to analyze.
        repo_limit: The maximum number of repositories to analyze.

    Returns:
        A GraphData object representing the analyzed repositories and their relationships.

    Raises:
        HTTPException: If there are issues fetching or processing the data.
    """
    try:
        html_content = await fetch_github_trending(language)
        repos_data = extract_repo_data(html_content, language, repo_limit)

        nodes = [Node(**repo) for repo in repos_data]
        edges: List[Edge] = []

        # Fetch topics and calculate edges.  Added error handling around topic fetching.
        repo_topics = {}
        for repo in repos_data:
            repo_topics[repo["name"]] = await fetch_repository_topics(repo["name"])

        for i in range(len(repos_data)):
            for j in range(i + 1, len(repos_data)):
                repo1_name = repos_data[i]["name"]
                repo2_name = repos_data[j]["name"]
                topics1 = repo_topics.get(repo1_name, [])
                topics2 = repo_topics.get(repo2_name, [])
                common_topics_count = len(set(topics1) & set(topics2))
                similarity = calculate_similarity(repos_data[i]["description"], repos_data[j]["description"])

                # Use either shared topics or semantic similarity as the edge weight.
                # You can choose which one to use, or combine them.
                edge_weight = common_topics_count #  Use shared topics
                # edge_weight = similarity # Use semantic similarity
                # edge_weight = common_topics_count + similarity # Combine them.

                if edge_weight > 0:
                    edges.append(Edge(source=repo1_name, target=repo2_name, weight=edge_weight))

        return GraphData(nodes=nodes, edges=edges)
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing repositories: {e}")

# --- API Endpoint ---
@app.get(
    "/analyze/github/trending/{language}",
    response_model=GraphData,
    responses={
        200: {"description": "Successfully analyzed trending repositories."},
        400: {"description": "Invalid language provided."},
        500: {"description": "Internal server error."},
    },
)
async def get_trending_repos(
    language: str = Path(..., title="Programming language to analyze"),
    repo_limit: int = 10,  # Add the repo_limit parameter with a default value of 10
) -> JSONResponse:
    """
    Analyzes trending repositories on GitHub for a given programming language and returns
    the data in a graph-like JSON format.

    Args:
        language: The programming language to analyze (e.g., "python", "javascript").
        repo_limit: The maximum number of repositories to analyze (default: 10).

    Returns:
        A JSON response containing the graph data, including nodes (repositories) and
        edges (connections between repositories based on shared topics).

    Raises:
        HTTPException:
            - 400: If the language is invalid or not supported.
            - 500: If there is an error during the process (e.g., network issues,
              parsing errors, or issues with the ChatGPT API).
    """
    if not language:
        raise HTTPException(status_code=400, detail="Language must be provided.")

    if language.lower() in ("all", "unknown"):
        raise HTTPException(status_code=400, detail="Language 'all' or 'unknown' is not supported.")

    if repo_limit <= 0:
        raise HTTPException(status_code=400, detail="repo_limit must be greater than 0.")

    cache_key = f"{language}:{repo_limit}" # Include limit in cache key
    if cache_key in cache:
        return JSONResponse(content=cache[cache_key])

    try:
        graph_data = await analyze_repositories(language, repo_limit)
        cache[cache_key] = graph_data.dict()  # Store the dictionary representation
        return JSONResponse(content=graph_data.dict())
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")



@app.get("/")  # Add this route
async def root():
    return {"message": "Welcome to the GitHub Trending Analyzer API!  Use /analyze/github/trending/{language} to get data."}


# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    """
    Startup event to perform any initial setup (currently, it's empty).
    """
    pass # Can be used for initial setup, e.g., connecting to a database.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
