import torch

### Utils from: https://github.com/UKPLab/sentence-transformers/blob/master/sentence_transformers/util.py

def normalize_embeddings(embeddings):
    return torch.nn.functional.normalize(embeddings, p=2, dim=1)

def cos_sim(a, b):
    # Average over tokens to get sentence-level emb.
    a = a.mean(dim=1)
    b = b.mean(dim=1)

    a_norm = normalize_embeddings(a)
    b_norm = normalize_embeddings(b)
    return torch.mm(a_norm, b_norm.transpose(0, 1))
