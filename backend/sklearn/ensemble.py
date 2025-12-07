class RandomForestClassifier:
    def __init__(self, *args, **kwargs):
        pass
    def fit(self, X, y):
        return self
    def predict(self, X):
        return [None] * (len(X) if hasattr(X, '__len__') else 1)

class IsolationForest:
    def __init__(self, *args, **kwargs):
        pass
    def fit(self, X):
        return self
    def predict(self, X):
        return [1] * (len(X) if hasattr(X, '__len__') else 1)
