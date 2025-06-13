try:
    import torch
except:
    pass

### Utils from: https://github.com/UKPLab/sentence-transformers/blob/master/sentence_transformers/util.py

def normalize_embeddings(embeddings):
    return torch.nn.functional.normalize(embeddings, p=2, dim=1)

def cos_sim(a, b, from_mt_model = False):
    # This averages over tokens to get sentence-level emb, intended for use with Madness MT models directly.
    # But now that we have a dedicated sentence embedding model, from_mt_model=True is probably never needed.
    if from_mt_model:
        a = a.mean(dim=1)
        b = b.mean(dim=1)

    a = normalize_embeddings(a)
    b = normalize_embeddings(b)

    return torch.mm(a, b.transpose(0, 1))
