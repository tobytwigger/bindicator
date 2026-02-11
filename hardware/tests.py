#!/home/toby/bindicator/.venv/bin/python
import datetime
import sys
from pathlib import Path
from dotenv import load_dotenv
# Load environment variables from .env file
root_dir = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=root_dir / ".env")

sys.path.append(str(root_dir))

from core.scheduler.factory import BinCollectionFactory

# Load environment variables from .env file
root_dir = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=root_dir / ".env")

sys.path.append(str(root_dir))

from core.scheduler.scheduler import BinCollectionExplorer

def run():
    factory = BinCollectionFactory()

    dataframe = factory.build_collections_dataframe()

    print(dataframe)

    print(BinCollectionExplorer().get_next_collections_for_all_bins())


if __name__ == "__main__":
    run()