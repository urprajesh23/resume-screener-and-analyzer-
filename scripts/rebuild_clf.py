import pickle
import re
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC


ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT_DIR / "data" / "UpdatedResumeDataSet.csv"
MODELS_DIR = ROOT_DIR / "models"
TFIDF_PATH = MODELS_DIR / "tfidf.pkl"
ENCODER_PATH = MODELS_DIR / "encoder.pkl"
MODEL_PATH = MODELS_DIR / "clf.pkl"


def clean_resume(text: str) -> str:
    cleaned = re.sub(r"http\S+\s", " ", text)
    cleaned = re.sub(r"RT|cc", " ", cleaned)
    cleaned = re.sub(r"#\S+\s", " ", cleaned)
    cleaned = re.sub(r"@\S+", " ", cleaned)
    cleaned = re.sub(r"[%s]" % re.escape("""!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"""), " ", cleaned)
    cleaned = re.sub(r"[^\x00-\x7f]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def validate_dataset(dataset: pd.DataFrame) -> None:
    required_columns = {"Resume", "Category"}
    missing = required_columns.difference(dataset.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Dataset is missing required column(s): {missing_text}")


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    dataset = pd.read_csv(DATASET_PATH)
    validate_dataset(dataset)

    cleaned_resumes = dataset["Resume"].astype(str).map(clean_resume)
    categories = dataset["Category"].astype(str)

    tfidf = TfidfVectorizer(stop_words="english")
    features = tfidf.fit_transform(cleaned_resumes)

    label_encoder = LabelEncoder()
    targets = label_encoder.fit_transform(categories)

    classifier = OneVsRestClassifier(SVC())
    classifier.fit(features, targets)

    with open(TFIDF_PATH, "wb") as tfidf_file:
        pickle.dump(tfidf, tfidf_file)

    with open(ENCODER_PATH, "wb") as encoder_file:
        pickle.dump(label_encoder, encoder_file)

    with open(MODEL_PATH, "wb") as model_file:
        pickle.dump(classifier, model_file)

    print(f"Training complete. Created: {TFIDF_PATH}, {ENCODER_PATH}, {MODEL_PATH}")


if __name__ == "__main__":
    main()