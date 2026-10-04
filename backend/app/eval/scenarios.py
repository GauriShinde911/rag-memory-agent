"""Multi-session evaluation scenarios from the assignment notebook."""
from typing import List, Dict, Any

SCENARIOS: List[Dict[str, Any]] = [
    {
        "name": "S1 Profile & project recall",
        "sessions": [
            {
                "id": "1a",
                "turns": [
                    {
                        "user": "I'm doing a literature review on transformer-based time-series forecasting for solar power. My report is due on 15 October."
                    },
                    {
                        "user": "My supervisor is Prof. Kulkarni and she wants IEEE citation style."
                    },
                ],
            },
            {
                "id": "1b",
                "turns": [
                    {
                        "user": "What topic am I researching and when is it due?",
                        "expect_memory": ["time-series", "15 October"],
                    },
                    {
                        "user": "Which citation style does my supervisor want?",
                        "expect_memory": ["IEEE"],
                    },
                    {
                        "user": "There are 16 days left and I plan to read 4 papers a day. How many papers is that in total?",
                        "expect_tool": "calculator",
                    },
                ],
            },
        ],
    },
    {
        "name": "S2 Correction / feedback loop",
        "sessions": [
            {
                "id": "2a",
                "turns": [
                    {"user": "My cloud GPU budget is $50 per month."},
                    {"user": "I use Chroma as my vector database."},
                ],
            },
            {
                "id": "2b",
                "turns": [
                    {
                        "user": "Correction: my GPU budget was raised to $80 per month, not $50."
                    }
                ],
            },
            {
                "id": "2c",
                "turns": [
                    {
                        "user": "What is my monthly GPU budget?",
                        "expect_memory": ["$80"],
                        "forbid_memory": ["$50"],
                    },
                    {
                        "user": "Use Python to compute how many months a $400 GPU purchase would last if I spent my whole monthly budget on it.",
                        "expect_tool": "python_executor",
                    },
                ],
            },
        ],
    },
    {
        "name": "S3 Web research saved to memory",
        "sessions": [
            {
                "id": "3a",
                "turns": [
                    {
                        "user": "Search the web for what FAISS is and save a one-line summary of it to your memory.",
                        "expect_tool": "web_search",
                    },
                    {
                        "user": "I'm using Python 3.11 on Google Colab for this project, please remember that."
                    },
                ],
            },
            {
                "id": "3b",
                "turns": [
                    {
                        "user": "What did you find about FAISS earlier?",
                        "expect_memory": ["FAISS"],
                    },
                    {
                        "user": "Which Python version and platform am I using?",
                        "expect_memory": ["3.11", "Colab"],
                    },
                ],
            },
        ],
    },
]
