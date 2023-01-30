import logging

logging.basicConfig(
    level=logging.INFO,
    filename=f"log.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s",
)