# # core/calibrator.py
# import joblib
# import numpy as np

# def fit_linear_calibrator(X, y, model=None):
#     try:
#         from sklearn.linear_model import LinearRegression
#     except Exception as e:
#         raise RuntimeError("scikit-learn required to train calibrator") from e
#     if model is None:
#         model = LinearRegression()
#     model.fit(np.array(X), np.array(y))
#     return model

# def fit_logreg_calibrator(X, y, model=None):
#     try:
#         from sklearn.linear_model import LogisticRegression
#     except Exception as e:
#         raise RuntimeError("scikit-learn required to train calibrator") from e
#     if model is None:
#         model = LogisticRegression(max_iter=500)
#     model.fit(np.array(X), np.array(y))
#     return model

# def save_calibrator(model, path: str):
#     joblib.dump(model, path)

# def load_calibrator(path: str):
#     return joblib.load(path)

# def predict_calibrated(model, X):
#     X = np.array(X)
#     if hasattr(model, "predict_proba"):
#         probs = model.predict_proba(X)
#         preds = probs.argmax(axis=1)
#         return preds
#     else:
#         preds = model.predict(X)
#         return preds
