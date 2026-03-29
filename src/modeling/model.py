# src/modeling/train_models.py
# ============================================================
# REPORT 4: MODELING & VALIDATION
# Xây dựng 2 mô hình ML để phân loại Sentiment trên dữ liệu Foody.vn
# Model 1: Logistic Regression (Baseline)
# Model 2: Random Forest (Ensemble)
# ============================================================

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
import os
import json
import joblib
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

# --- CẤU HÌNH ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "foody_clean_master.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

# Tạo thư mục output
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# --- Tham số ---
RANDOM_STATE = 42
TEST_SIZE = 0.2
MAX_TFIDF_FEATURES = 5000


def load_data():
    """Đọc dữ liệu sạch và lọc bỏ các nhãn Unknown."""
    print("=" * 60)
    print("📂 BƯỚC 1: ĐỌC DỮ LIỆU")
    print("=" * 60)

    df = pd.read_csv(DATA_PATH)
    print(f"   Tổng số dòng ban đầu: {len(df)}")

    # Lọc bỏ nhãn Unknown và dòng rỗng
    df = df[df['sentiment_label'].isin(['Positive', 'Negative', 'Neutral'])]
    df = df[df['comment_clean'].notna() & (df['comment_clean'].str.strip() != "")]
    df.reset_index(drop=True, inplace=True)

    print(f"   Sau khi lọc: {len(df)} dòng hợp lệ")
    print(f"\n   📊 Phân bố nhãn:")
    label_counts = df['sentiment_label'].value_counts()
    for label, count in label_counts.items():
        pct = count / len(df) * 100
        print(f"      - {label}: {count} ({pct:.1f}%)")

    return df


def build_tfidf_features(X_train_text, X_test_text):
    """Xây dựng TF-IDF Vector từ comment_clean."""
    print("\n" + "=" * 60)
    print("🔧 BƯỚC 2: FEATURE ENGINEERING (TF-IDF)")
    print("=" * 60)

    vectorizer = TfidfVectorizer(
        max_features=MAX_TFIDF_FEATURES,
        ngram_range=(1, 2),       # Unigram + Bigram
        min_df=2,                 # Bỏ từ xuất hiện < 2 lần
        max_df=0.95,              # Bỏ từ xuất hiện > 95% documents
        sublinear_tf=True,        # Áp dụng log scaling cho TF
    )

    X_train_tfidf = vectorizer.fit_transform(X_train_text)
    X_test_tfidf = vectorizer.transform(X_test_text)

    print(f"   Vocabulary size: {len(vectorizer.vocabulary_)}")
    print(f"   TF-IDF matrix shape (train): {X_train_tfidf.shape}")
    print(f"   TF-IDF matrix shape (test):  {X_test_tfidf.shape}")

    # Lưu vectorizer
    vec_path = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
    joblib.dump(vectorizer, vec_path)
    print(f"   💾 Đã lưu TF-IDF vectorizer → {vec_path}")

    return X_train_tfidf, X_test_tfidf, vectorizer


def evaluate_model(model, model_name, X_test, y_test):
    """Đánh giá mô hình và trả về dict kết quả."""
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=['Positive', 'Neutral', 'Negative'])
    report = classification_report(y_test, y_pred, labels=['Positive', 'Neutral', 'Negative'], zero_division=0)

    results = {
        'model_name': model_name,
        'accuracy': round(acc, 4),
        'precision': round(prec, 4),
        'recall': round(rec, 4),
        'f1_score': round(f1, 4),
        'confusion_matrix': cm.tolist(),
        'classification_report': report
    }
    return results


def train_and_evaluate():
    """Pipeline chính: Load → TF-IDF → Train 2 Models → Evaluate → Compare."""

    # === BƯỚC 1: Load data ===
    df = load_data()

    X_text = df['comment_clean']
    y = df['sentiment_label']

    # Train/Test Split (80/20, stratified)
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        X_text, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    print(f"\n   📦 Train/Test split: {len(X_train_text)} train / {len(X_test_text)} test")

    # === BƯỚC 2: TF-IDF ===
    X_train, X_test, vectorizer = build_tfidf_features(X_train_text, X_test_text)

    # === BƯỚC 3: TRAIN MODELS ===
    all_results = []

    # --- MODEL 1: Logistic Regression ---
    print("\n" + "=" * 60)
    print("🤖 BƯỚC 3A: LOGISTIC REGRESSION")
    print("=" * 60)

    lr_model = LogisticRegression(
        max_iter=1000,
        C=1.0,
        solver='lbfgs',
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    lr_model.fit(X_train, y_train)

    lr_results = evaluate_model(lr_model, "Logistic Regression", X_test, y_test)
    all_results.append(lr_results)

    # Lưu model
    lr_path = os.path.join(MODEL_DIR, "logistic_regression.pkl")
    joblib.dump(lr_model, lr_path)

    print(f"   ✅ Accuracy:  {lr_results['accuracy']}")
    print(f"   ✅ Precision: {lr_results['precision']}")
    print(f"   ✅ Recall:    {lr_results['recall']}")
    print(f"   ✅ F1-Score:  {lr_results['f1_score']}")
    print(f"\n   📋 Classification Report:\n{lr_results['classification_report']}")
    print(f"   📊 Confusion Matrix:")
    print(f"   {np.array(lr_results['confusion_matrix'])}")
    print(f"   💾 Model saved → {lr_path}")

    # --- MODEL 2: Random Forest ---
    print("\n" + "=" * 60)
    print("🌲 BƯỚC 3B: RANDOM FOREST")
    print("=" * 60)

    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)

    rf_results = evaluate_model(rf_model, "Random Forest", X_test, y_test)
    all_results.append(rf_results)

    # Lưu model
    rf_path = os.path.join(MODEL_DIR, "random_forest.pkl")
    joblib.dump(rf_model, rf_path)

    print(f"   ✅ Accuracy:  {rf_results['accuracy']}")
    print(f"   ✅ Precision: {rf_results['precision']}")
    print(f"   ✅ Recall:    {rf_results['recall']}")
    print(f"   ✅ F1-Score:  {rf_results['f1_score']}")
    print(f"\n   📋 Classification Report:\n{rf_results['classification_report']}")
    print(f"   📊 Confusion Matrix:")
    print(f"   {np.array(rf_results['confusion_matrix'])}")
    print(f"   💾 Model saved → {rf_path}")

    # === BƯỚC 4: SO SÁNH ===
    print("\n" + "=" * 60)
    print("📊 BƯỚC 4: SO SÁNH 2 MÔ HÌNH")
    print("=" * 60)

    print(f"\n   {'Metric':<15} {'Logistic Regression':>20} {'Random Forest':>20}")
    print(f"   {'-'*55}")
    print(f"   {'Accuracy':<15} {lr_results['accuracy']:>20.4f} {rf_results['accuracy']:>20.4f}")
    print(f"   {'Precision':<15} {lr_results['precision']:>20.4f} {rf_results['precision']:>20.4f}")
    print(f"   {'Recall':<15} {lr_results['recall']:>20.4f} {rf_results['recall']:>20.4f}")
    print(f"   {'F1-Score':<15} {lr_results['f1_score']:>20.4f} {rf_results['f1_score']:>20.4f}")

    # Xác định Best Model
    if lr_results['f1_score'] >= rf_results['f1_score']:
        best = "Logistic Regression"
        best_f1 = lr_results['f1_score']
    else:
        best = "Random Forest"
        best_f1 = rf_results['f1_score']

    print(f"\n   🏆 BEST MODEL: {best} (F1 = {best_f1:.4f})")

    # === BƯỚC 5: LƯU KẾT QUẢ ===
    output = {
        'timestamp': datetime.now().isoformat(),
        'dataset': {
            'total_samples': len(df),
            'train_samples': len(y_train),
            'test_samples': len(y_test),
            'labels': list(y.unique()),
            'tfidf_features': MAX_TFIDF_FEATURES
        },
        'models': all_results,
        'best_model': best,
        'best_f1': best_f1
    }

    results_path = os.path.join(RESULTS_DIR, "model_comparison.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n   📁 Kết quả chi tiết đã lưu → {results_path}")
    print("\n" + "=" * 60)
    print("🎉 HOÀN TẤT MODELING & VALIDATION!")
    print("=" * 60)

    return output


if __name__ == "__main__":
    train_and_evaluate()
