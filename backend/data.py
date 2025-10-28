import kagglehub
import os

# Download latest version
data_dir = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(data_dir, exist_ok=True)

path = kagglehub.dataset_download("sadmadlad/imdb-user-reviews", download_dir=data_dir)

print("Path to dataset files:", path)