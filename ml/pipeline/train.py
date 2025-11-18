import pandas as pd
from sklearn.linear_model import LinearRegression
from joblib import dump
from loguru import logger
from .preprocess import preprocess

def train_model(input_path: str, model_path: str):
    logger.info("Training model...")
    df = pd.read_csv(input_path)
    df = preprocess(df)
    X = df.drop('target', axis=1)
    y = df['target']
    model = LinearRegression()
    model.fit(X, y)
    dump(model, model_path)
    logger.info(f"Model saved to {model_path}")
