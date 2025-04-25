from pydantic import BaseModel, Field
from typing import List

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
