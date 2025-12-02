# backend/data.py

from backend.data_loader import load_movies_from_kaggle

if __name__ == "__main__":
    summary = load_movies_from_kaggle()
    print(f"Copied {summary['files_copied']} files to: {summary['target_root']}")
    print("Created movies.json and movies.csv")
