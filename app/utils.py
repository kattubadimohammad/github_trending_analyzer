import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException



async def fetch_github_trending(language: str) -> str:
    """Fetches GitHub trending page HTML."""
    url = f"https://github.com/trending/{language}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error fetching {url}: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch {url}: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

def extract_repo_data(html_content: str, language: str, repo_limit: int) -> List[Dict]:
    """Extracts repository data from HTML."""
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
            print(f"Error processing repository: {e}")
    return repos

async def fetch_repository_topics(repo_name: str) -> List[str]:
    """Fetches repository topics from GitHub."""
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
            topics_elements = soup.find_all("a", class_="topic-tag")
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
    """Calculates semantic similarity between two descriptions."""
    words1 = set(desc1.lower().split())
    words2 = set(desc2.lower().split())
    common_words = words1.intersection(words2)
    total_unique_words = len(words1.union(words2))
    if total_unique_words == 0:
        return 0.0
    return len(common_words) / total_unique_words
