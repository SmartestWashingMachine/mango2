from flask import request
from gandy.app import app
import numpy as np
import random
import torch
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger


@app.route("/setseed", methods=["POST"])
def set_seed_route():
    with logger.begin_event("Set seed") as ctx:
        data = request.json
        new_seed = data["seed"]
        new_seed = int(new_seed)

        random.seed(new_seed)
        np.random.seed(new_seed)

        try:
            torch.manual_seed(new_seed)
        except:
            pass

        ctx.log(f"Seed set", new_seed=new_seed)

    return {}, 200

@app.route("/circuitbreak", methods=["POST"])
def trigger_circuit_breaker():
    with logger.begin_event("Breaking circuit") as ctx:
        config_state._temp_circuit_broken = True

    return {}, 200