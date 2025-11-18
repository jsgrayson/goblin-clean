from joblib import load
import pandas as pd
from loguru import logger

def predict(model_path: str, input_data: dict):
    logger.info("Running prediction...")
    df = pd.DataFrame([input_data])
    model = load(model_path)
    return model.predict(df)[0]
