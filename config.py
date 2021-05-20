import os
from dotenv import load_dotenv

load_dotenv(verbose=True)
# print(load_dotenv())  # True

# # Or, explicitly provide path to '.env'
# from pathlib import Path

# env_path = Path(".") / ".env"
# load_dotenv(dotenv_path=env_path)

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# KRAKEN_API_KEY = os.getenv("KRAKEN_API_KEY")
KRAKEN_API_KEY = f"{os.getenv('KRAKEN_API_KEY')}"
KRAKEN_API_KEY_DESCRIPTION = os.getenv("KRAKEN_API_KEY_DESCRIPTION")
KRAKEN_PRIVATE_KEY = os.getenv("KRAKEN_PRIVATE_KEY")
KRAKEN_API_SECRET = os.getenv("KRAKEN_API_SECRET")
