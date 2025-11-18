import pandas as pd
from loguru import logger

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Preprocessing data...")
    df = df.dropna()
    return df
