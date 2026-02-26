from gandy.utils.fancy_logger import logger
import json
import os
from gandy.database.faiss_store import FAISSStore
from tqdm import tqdm
import hashlib
from math import ceil
import traceback

# This function is AI generated, not that it matters... it's fairly simple.
def hash_file_sha256(filename):
    h = hashlib.sha256()
    
    with open(filename, 'rb') as file:
        while True:
            chunk = file.read(65536) 
            if not chunk:
                break

            h.update(chunk)
            
    return h.hexdigest()

# Unlike FAISS MT Cache, which is used for retrieving cached machine translations from source texts...
# This RAG module is intended to be used to find similar source texts and their translations from some user-given dataset.
# Only "Custom GGUF models" (including my Reforged model) can use this, as my initial models were not trained to work with RAG effectively.
# ^ Actually that comment is old. My new models (gem_uni & gem_mage) can also work with it. And gem_uni is a default model.

class TranslationRAG():
    def __init__(self, file_suffixes: str):
        self.mt_rag = None

        self.file_suffixes = file_suffixes

    def _build_dataset(self, items, cur_data_hash = None):
        with logger.begin_event('Creating RAG data and index files') as ctx:
            # Each item should be a tuple of (source STR, target STR).

            if self.mt_rag.embedder.get_can_cuda():
                batch_size = 1024 #8192 has many out-of-context errors. # 16 also works decently.
                total_batches = ceil(len(items) / batch_size)

                for idx, batch in enumerate(
                    tqdm(
                        (items[i:i + batch_size] for i in range(0, len(items), batch_size)),
                        total=total_batches
                    )
                ):
                    try:
                        self.mt_rag._add(
                            source_texts=[x[0] for x in batch],
                            translated_texts=batch,
                            do_log=False,
                        )
                    except Exception as err:
                        ctx.log("Error adding RAG entry for batch - likely due to context length being exceeded. Dropping batch.", batch_idx=idx)
                        print(traceback.format_exc())

                    if idx % 200 == 0:
                        ctx.log(f'Processing batch...', last_finished_idx=idx, total_len=total_batches)
            else:
                for idx, (st, tt) in enumerate(tqdm(items, desc="Building RAG dataset")):
                    self.mt_rag.add_translation(source_text=st, translated_text=(st, tt), do_log=False)

                    if idx % 1000 == 0:
                        ctx.log(f'Processing item...', last_finished_idx=idx, total_len=len(items))

        with logger.begin_event('Saving RAG data and index files'):
            self.mt_rag._save_async() # Actually not async cause we call it directly here, rather than using a thread.
            del self.mt_rag

            # Save the hash after everything is done.
            with open(self.get_hash_path(), "w", encoding="utf-8") as fp:
                fp.write(cur_data_hash)

        with logger.begin_event('Reloading RAG module'):
            self._load_mt_rag()

    def get_input_file_path(self):
        if self.file_suffixes == '':
            return f'models/database/rag_input_data.jsonl'
        return f'models/database/rag_input_data_{self.file_suffixes}.jsonl'

    def data_file_exists(self):
        return os.path.exists(self.get_input_file_path())

    def get_hash_path(self):
        return rf'models/database/rag_hash{self.file_suffixes}'

    def do_build_index(self):
        with logger.begin_event("Checking whether or not to build RAG data") as ctx:
            input_path = self.get_input_file_path()
            cur_hash = hash_file_sha256(input_path).strip()
            
            # If the hash of the previous JSONL user input data does not exist or is not equal to the current JSONL user input data, rebuild.
            precomputed_hash_path = self.get_hash_path()
            if not os.path.exists(precomputed_hash_path):
                ctx.log("Old hash does not exist - building.", cur_hash=cur_hash)
                return (True, cur_hash)

            prev_hash = open(precomputed_hash_path, encoding="utf-8").read().strip()
            ctx.log("Checking if old hash is equal to current hash", cur_hash=cur_hash, prev_hash=prev_hash, equal=cur_hash == prev_hash)
            return (cur_hash != prev_hash, cur_hash)

    def _load_mt_rag(self):
        with logger.begin_event('Loading RAG module for translation') as ctx:
            do_build, cur_data_hash = self.do_build_index()

            if do_build:
                self.mt_rag = FAISSStore(
                    db_path='models/database/rag',
                    model_name='nite',
                    save_interval=-1,
                    db_name=f'_index{self.file_suffixes}',
                    data_name=f'_data{self.file_suffixes}',
                    high_cost=True, # Much faster but more demanding (if using a good GPU).
                )

                ctx.log('RAG Index file does NOT exist - creating from input data file.')

                input_path = self.get_input_file_path()
                if not os.path.exists(input_path):
                    ctx.log('Will NOT create RAG data file - input data file not found!')
                    return

                items = []
                with logger.begin_event('Reading input data file...') as loading_ctx:
                    with open(input_path, encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if len(line) == 0:
                                continue

                            data = json.loads(line)
                            items.append((data['source'], data['target']))

                    loading_ctx.log('Done mapping items in input data file', n_items=len(items))

                self._build_dataset(items, cur_data_hash)

                self.mt_rag.embedder.llm.stop_server() # So we can load the low-cost one afterwards.
                del self.mt_rag
            else:
                ctx.log('RAG Index file already exists - using existing RAG data file.')

            self.mt_rag = FAISSStore(
                db_path='models/database/rag',
                model_name='nite',
                save_interval=-1,
                db_name=f'_index{self.file_suffixes}',
                data_name=f'_data{self.file_suffixes}',
                high_cost=False,
            )

    def get_entries(self, inp: str):
        # Returns a list of tuples. Each tuple is (source STR, target STR).

        with logger.begin_event('Checking vector dataset') as ctx:
            # Cut any context. TODO: Sure about this?
            inp = inp.split('<TSOS>')[-1].strip()

            if self.mt_rag is None:
                self._load_mt_rag()

            found_translations, sim, _ = self.mt_rag.retrieve(inp, top_k=3, similarity_threshold=0.4)
            if len(found_translations) > 0:
                ctx.log(f'Similar translation(s) found in dataset', cosine_sim=sim)

                return found_translations
            else:
                ctx.log('No similar translations found in dataset')

        return []
