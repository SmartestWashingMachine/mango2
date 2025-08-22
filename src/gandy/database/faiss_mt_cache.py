import faiss
import numpy as np
import os
import threading
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger
import numpy as np
from gandy.translation.llama_server_wrapper import LlamaCppExecutableOpenAIClient
from gandy.database.faiss_store import FAISSStore

class MTCache():
    def __init__(self):
        self.mt_cache = None

    def load_mt_cache(self):
        self.mt_cache = FAISSStore(db_path='models/database/cache', model_name='nite', save_interval=50, db_name='_index', data_name='_machinetranslations')

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
