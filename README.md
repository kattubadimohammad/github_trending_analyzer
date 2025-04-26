# GitHub Trending Repository Analyzer

A **FastAPI application** that fetches and analyzes trending repositories from GitHub for a specified programming language.

---

## 🚀 Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kattubadimohammad/github_trending_analyzer.git
   cd github_trending_analyzer
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/macOS
   venv\Scripts\activate     # On Windows
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application locally**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

---

## 📌 Usage

The API exposes endpoints to fetch trending GitHub repositories.

**Base URL (Live on Render):**
```
https://github-trending-analyzer-service.onrender.com/
```

**Main API Endpoint:**
```
GET /analyze/github/trending/{language}
```

- `language`: The programming language to analyze (e.g., `"python"`, `"javascript"`).
- `repo_limit`: *(Optional)* The maximum number of repositories to analyze. Default is **10**.

---

### 📎 Example Requests

- **Base URL** (Health check or welcome route):
  - [`https://github-trending-analyzer-service.onrender.com/`](https://github-trending-analyzer-service.onrender.com/)

- **Analyze Python repos (default limit)**:
  - [`https://github-trending-analyzer-service.onrender.com/analyze/github/trending/python`](https://github-trending-analyzer-service.onrender.com/analyze/github/trending/python)

- **Analyze top 5 Python repos**:
  - [`https://github-trending-analyzer-service.onrender.com/analyze/github/trending/python?repo_limit=5`](https://github-trending-analyzer-service.onrender.com/analyze/github/trending/python?repo_limit=5)

---

### 📋 API Response Structure

```json
{
  "nodes": [
    {
      "id": "owner1/repo1",
      "description": "Repository description here...",
      "stars": 1234,
      "forks": 567,
      "language": "python"
    }
  ],
  "edges": [
    {
      "source": "owner1/repo1",
      "target": "owner2/repo2",
      "weight": 2
    }
  ]
}
```

---

## ☁️ Deployment on Render

1. Create a Render account.
2. Create a new Web Service.
3. Connect your GitHub repository.
4. Set the **Build and Start commands**:
   - Build Command:
     ```bash
     pip install -r requirements.txt
     ```
   - Start Command:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port 10000
     ```
5. Set the environment variable:
   - `PORT=10000`
6. Deploy and test your API:
   - 🌐 [`https://github-trending-analyzer-service.onrender.com/`](https://github-trending-analyzer-service.onrender.com/)

---

## 📖 About

FastAPI application for analyzing trending GitHub repositories based on the programming language.  
Designed to visualize and understand relationships between popular repositories.

---

## 🛠 Tech Stack

- FastAPI
- Python
- GitHub Trending (web scraping)
- Uvicorn (ASGI server)
- Hosted on Render

---

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GitHub Trending](https://github.com/trending)

---

## 🤝 Contributing

1. Fork the repository.
2. Create a new branch.
3. Make your changes and commit.
4. Push to your branch and create a Pull Request.

---

## ⭐ Show Some Love

If you find this project useful, consider starring the repo! ⭐
```
