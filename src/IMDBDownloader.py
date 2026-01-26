import os
import requests


class IMDBDownloader:
    """Class to handle downloading IMDb datasets."""
    
    IMDB_BASE_URL = "https://datasets.imdbws.com/"
    IMDB_FILES = [
        "title.basics.tsv.gz",
        "title.ratings.tsv.gz",
        "name.basics.tsv.gz",
        "title.crew.tsv.gz",
        "title.principals.tsv.gz"
    ]
    
    def __init__(self, download_dir):
        """Initialize the downloader with the target directory."""
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
    
    def download_imdb_files(self):
        """Download IMDb dataset files."""
        for filename in self.IMDB_FILES:
            url = self.IMDB_BASE_URL + filename
            local_path = os.path.join(self.download_dir, filename)
            print(f"Downloading {filename}...")
            response = requests.get(url, stream=True)
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded {filename} to {local_path}")