import json
from pathlib import Path

import requests


BASE_URL = "http://127.0.0.1:8000"


def main():
    questions_path = Path("eval/questions.json")
    questions = json.loads(questions_path.read_text(encoding="utf-8"))

    results = []

    for item in questions:
        question = item["question"]

        response = requests.get(
            f"{BASE_URL}/ask",
            params={"q": question, "top_k": 3},
            timeout=60,
        )
        response.raise_for_status()

        data = response.json()

        results.append(
            {
                "question": question,
                "answer": data.get("answer"),
                "sources": data.get("sources"),
                "duration_ms": data.get("duration_ms"),
            }
        )

    output_path = Path("eval/results.json")
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("evaluation finished: eval/results.json")


if __name__ == "__main__":
    main()