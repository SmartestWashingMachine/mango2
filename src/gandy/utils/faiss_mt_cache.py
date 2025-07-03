import faiss
import numpy as np
import os
import threading
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger
import numpy as np

# Vibe coded bro.

class FAISSEmbedder:
    def __init__(self, model_name: str):
        """
        Initialize the FAISSEmbedder with a multilingual model.

        :param model_name: Name of the multilingual model.
        """

        can_cuda = config_state.use_cuda and not config_state.force_translation_cpu
        logger.info(f"Loading embedding model...")

        if can_cuda:
            from llama_cpp_cuda import Llama as LlamaGpu

            llm_to_use = LlamaGpu
        else:
            from llama_cpp import Llama as LlamaCpu

            llm_to_use = LlamaCpu

        self.model = llm_to_use(model_name, n_gpu_layers=0, embedding=True, verbose=False)

    def embed(self, sentences: list) -> np.ndarray:
        """
        Embed a list of sentences into dense vectors.

        :param sentences: List of sentences to embed.
        :return: Numpy array of embeddings.
        """
        return self.model.embed(sentences)

class FAISSStore:
    def __init__(self, db_path: str, model_name: str, hnsw_m: int = 32, save_interval: int = 50):
        """
        Initialize the FAISSStore.

        :param db_path: Path to the local FAISS database file.
        :param model_name: Name of the multilingual model for embedding.
        :param hnsw_m: Number of neighbors for HNSW graph construction (default: 32).
        :param save_interval: Number of additions after which the database is saved (default: 50).
        """
        self.db_path = db_path + '_index'
        self.hnsw_m = hnsw_m
        self.embedder = FAISSEmbedder(model_name)
        self.index = None
        self.translations = []  # Store only translated_text
        self.translations_file = db_path + "_machinetranslations.npy"
        self.save_interval = save_interval
        self.add_count = 0  # Tracks the number of additions since the last save
        self.save_lock = threading.Lock()  # Lock for thread-safe saving
        self.save_timer = None  # Timer for periodic saving
        self.timer_lock = threading.Lock()  # Lock for thread-safe timer management

        # Load existing index or create a new one
        self._load_or_initialize_index()

    def _load_or_initialize_index(self):
        try:
            self.index = faiss.read_index(self.db_path)
            logger.log(f"Loaded FAISS index from {self.db_path}")
            if os.path.exists(self.translations_file):
                self.translations = np.load(self.translations_file, allow_pickle=True).tolist()
                logger.log(f"Loaded {len(self.translations)} translations from {self.translations_file}")
        except Exception:
            logger.log("Creating a new FAISS HNSW index.")
            dimension = 384  # TODO: Cleaner. # self.embedder.model.config.hidden_size
            self.index = faiss.IndexHNSWFlat(dimension, self.hnsw_m, faiss.METRIC_INNER_PRODUCT)  # HNSW index with cosine similarity
            self.index.hnsw.efConstruction = 200  # High-quality graph construction
            self.index.hnsw.efSearch = 50  # Fast and accurate retrieval
            self.translations = []

    def _reset_save_timer(self, start = True):
        """
        Reset the save timer to trigger saving 60 seconds after the last addition.
        """
        with self.timer_lock:
            if self.save_timer:
                self.save_timer.cancel()  # Cancel the existing timer
                self.save_timer = None

            if start:
                self.save_timer = threading.Timer(60, self._save_async)  # Set a new timer
                self.save_timer.start()

    def _save_async(self):
        """
        Save the FAISS index and translations asynchronously.
        """
        with self.save_lock:
            faiss.write_index(self.index, self.db_path)
            np.save(self.translations_file, np.array(self.translations, dtype=object))
            logger.log(f"FAISS index and translations saved to {self.db_path} and {self.translations_file}.")

    def _add(self, source_texts: list, translated_texts: list, already_embed = False):
        """
        Add source texts and their corresponding translations to the FAISS index.

        :param source_texts: List of source sentences to embed.
        :param translated_texts: List of translated sentences to store.
        :param already_embed: If True, don't embed the source_texts. The source_texts should be embeddings in this case.
        """
        embeddings = source_texts if already_embed else self.embedder.embed(source_texts)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)  # Normalize for cosine similarity
        self.index.add(embeddings)
        self.translations.extend(translated_texts)
        logger.log(f"Added {len(translated_texts)} translations to the index.")
        self.add_count += len(translated_texts)

        save_right_now = self.add_count >= self.save_interval
        if save_right_now:
            self.add_count = 0
            threading.Thread(target=self._save_async).start()  # Save asynchronously

        self._reset_save_timer(start=(not save_right_now))  # Reset the save timer after each addition

    def retrieve(self, query: str, top_k: int = 5, similarity_threshold = 0.95) -> list:
        """
        Retrieve translations similar to the query.

        :param query: Query sentence.
        :param top_k: Number of top results to return.
        :param similarity_threshold: Top results must pass this threshold to be returned.
        :return: List of translated_texts and a list of distances for each, as well as the query embedding.
        """

        with logger.begin_event('Retrieving neighbors') as ctx:
            query_embedding = self.embedder.embed([query])
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)  # Normalize
            distances, indices = self.index.search(query_embedding, top_k)
            results, dists = [], []
            for dist, idx in zip(distances[0], indices[0]):
                if idx != -1 and dist >= similarity_threshold:  # Cosine similarity is higher for closer matches
                    results.append(self.translations[idx])
                    dists.append(dist)
                if idx != -1:
                    ctx.log(f'Found neighbor with similarity score', cosine_similarity=dist)

        return results, dists, query_embedding

    def add_translation(self, source_text: str, translated_text: str):
        """
        Add a single translation to the FAISS index.

        :param source_text: Source sentence.
        :param translated_text: Translated sentence.
        """
        self._add([source_text], [translated_text])

    def add_translation_from_embed(self, source_embed, translated_text: str):
        """
        Add a single translation to the FAISS index.
        """
        self._add(source_embed, [translated_text], already_embed=True)

    def embed_text(self, text: str):
        return self.embedder.embed([text])

    def __del__(self):
        """
        Ensure the timer is cleaned up when the object is deleted.
        """
        with self.timer_lock:
            if self.save_timer:
                self.save_timer.cancel()

class MTCache():
    def __init__(self):
        self.mt_cache = None

    def load_mt_cache(self):
        self.mt_cache = FAISSStore(db_path='models/database/cache', model_name='models/database/nite.gguf')

    def embed_text(self, inp: str):
        if self.mt_cache is None:
            self.load_mt_cache()
        return self.mt_cache.embed_text(inp)

    def look_for_translation(self, inp: str):
        with logger.begin_event('Checking vector cache') as ctx:
            # Cut any context. TODO: Sure about this?
            inp = inp.split('<TSOS>')[-1].strip()

            if self.mt_cache is None:
                self.load_mt_cache()

            found_translations, sim, embed_inp = self.mt_cache.retrieve(inp, top_k=1, similarity_threshold=0.975)
            if len(found_translations) > 0:
                ctx.log(f'Translation already found in cache', cosine_sim=sim[0])

                return [found_translations[0]], embed_inp
            else:
                ctx.log('Translation is new!')

        return None, embed_inp

    def add_translation(self, embed_inp, prediction: str):
        with logger.begin_event('Adding to vector cache') as ctx:
            self.mt_cache.add_translation_from_embed(embed_inp, prediction)
