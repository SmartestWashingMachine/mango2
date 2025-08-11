import os

os.environ['CUDA_MODULE_LOADING'] = "LAZY"

os.environ["EVENTLET_NO_GREENDNS"] = 'yes'

from gevent import monkey
# monkey.patch_all(os=True, socket=True, ssl=True, thread=True, threading=True)
#monkey.patch_os()
#monkey.patch_socket()
#monkey.patch_ssl()
# monkey.patch_thread()
# monkey.patch_queue()

import tqdm
from time import strftime
import logging

import sklearn
import sklearn.neighbors
import sklearn.tree
import sklearn.metrics._pairwise_distances_reduction._datasets_pair
import sklearn.metrics._pairwise_distances_reduction._middle_term_computer
import sklearn.metrics._pairwise_distances_reduction

import unidic_lite
from unidic_lite import unidic

import pillow_avif


try:
	import torch
except:
	pass

from gandy.app import run_server

run_server()

# TODO: Better importing.