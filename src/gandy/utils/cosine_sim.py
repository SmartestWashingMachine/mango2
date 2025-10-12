import numpy as np

### Utils inspired from: https://github.com/UKPLab/sentence-transformers/blob/master/sentence_transformers/util.py

def normalize_embeddings(embeddings):
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)

    eps = 1e-12 # Just like (https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.normalize.html)
    return embeddings / (norms + eps)

def cos_sim(a: np.ndarray, b: np.ndarray, from_mt_model = False):
    # This averages over tokens to get sentence-level emb, intended for use with Madness MT models directly.
    # But now that we have a dedicated sentence embedding model, from_mt_model=True is probably never needed.
    if from_mt_model:
        a = a.mean(axis=1)
        b = b.mean(axis=1)

    a = normalize_embeddings(a)
    b = normalize_embeddings(b)

    return np.dot(a, b.T)
