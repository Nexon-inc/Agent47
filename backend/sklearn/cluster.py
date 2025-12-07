class DBSCAN:
    def __init__(self, *args, **kwargs):
        pass
    def fit(self, X):
        return self
    def fit_predict(self, X):
        return [0] * (len(X) if hasattr(X, '__len__') else 1)
