import subprocess
import time
import json
import os
from gandy.utils.fancy_logger import logger
import sys
from openai import AsyncOpenAI # Import the OpenAI client
import requests
import atexit

import win32api
import win32con
import win32job
import asyncio

class LlamaCppExecutableOpenAIClient:
    def __init__(self, model_path, num_gpu_layers, can_cuda,
                 llama_cpp_server_path, host="127.0.0.1", port=8000, prepend_phrase = None, verbose = False, n_context=750):
        """
        Initializes the client to interact with a llama.cpp server executable using the OpenAI client.

        Args:
            num_gpu_layers (int): Number of layers to offload to the GPU.
            can_cuda (bool): Whether CUDA is available and should be used.
            llama_cpp_server_path (str): The full path to the llama.cpp 'server' executable.
                                         e.g., "/path/to/llama.cpp/build/bin/server"
            host (str): The host address for the llama.cpp server.
            port (int): The port for the llama.cpp server.
        """
        self.model_path = model_path

        self.host = host
        self.port = port
        self.server_url = f"http://{self.host}:{self.port}/v1" # Base URL for OpenAI client
        self.server_process = None
        self.num_gpu_layers = num_gpu_layers
        self.can_cuda = can_cuda
        self.llama_cpp_server_path = llama_cpp_server_path
        self.prepend_phrase = prepend_phrase

        self.verbose = True #verbose
        
        self.n_context = n_context

        # Initialize the OpenAI client pointing to the llama.cpp server
        self.client = AsyncOpenAI(
            base_url=self.server_url,
            api_key="sk-no-key-required" # A dummy key, as llama.cpp server doesn't require one
        )

        # Ensure the model path exists
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        # Ensure the server executable exists
        if not os.path.exists(self.llama_cpp_server_path):
            raise FileNotFoundError(f"Llama.cpp server executable not found: {self.llama_cpp_server_path}")

        atexit.register(self.stop_server)

    def __del__(self):
        with logger.begin_event("Deleting Llama CPP server...") as ctx:
            self.stop_server()

            try:
                atexit.unregister(self.stop_server)
            except:
                pass

    def start_server(self):
        """Starts the llama.cpp server executable in a subprocess."""

        with logger.begin_event("Starting Llama CPP server...") as ctx:
            if self.server_process:
                ctx.log("Server already exists - reusing server instance.")
                return

            command = [
                self.llama_cpp_server_path,
                "-m",
                self.model_path,
                "--host",
                self.host,
                "--port",
                str(self.port),
                "-c", # Context size (equivalent to n_ctx)
                str(self.n_context),
                # "--mmap",
                "--mlock", # Lock model in memory
                # --- Sampling Parameters (replicating your llama-cpp-python settings) ---
                "--samplers", "top_k;dry;top_p;min_p;temperature", # Sampler order
                "--dry-multiplier", "0.8",
                "--dry-base", "1.75",
                "--dry-allowed-length", "2",
                # For sequence breakers, each needs to be a separate argument.
                # Handle special characters carefully; for cmd line "" might be needed.
                # In Python list, simple strings for each:
                # Defaults are already set. "--dry-seq-breakers", "\n", ":", "\"", "*",
                # ? idk if this works ? "--dry-range", "-1",
                "--temp", "0.02",
                "--top-p", "0.95",
                "--top-k", "40",
                "--min-p", "0.05",
                # Misc.
                # "--no-webui",
                # "--no-mmproj",
                # "--cache-reuse", "128",
            ]

            if self.verbose:
                command.append("--verbose")

            if self.can_cuda and self.num_gpu_layers > 0:
                command.extend(["-ngl", str(self.num_gpu_layers)])
                command.append("--flash-attn")
            else:
                # ik_llama deluxe! Building this from source was SO FUN!
                # This sheep randomly makes some models hang. WHY? WHY? WHY?
                # command.append("--run-time-repack")
                pass

            ctx.log(f"Starting server with command", command=' '.join(command))
            try:
                stdout_to_use = subprocess.DEVNULL
                stderr_to_use = subprocess.DEVNULL
                if self.verbose:
                    stdout_to_use = sys.stdout
                    stderr_to_use = sys.stderr

                self.server_process = subprocess.Popen(
                    command, stdout=stdout_to_use, stderr=stderr_to_use,
                )
                ctx.log("Llama.cpp server process started.")

                # 2. Create and configure the Job Object
                self.hJob = win32job.CreateJobObject(None, "")
                if not self.hJob:
                    raise win32api.error(win32api.GetLastError(), "CreateJobObject")

                extended_info = win32job.QueryInformationJobObject(self.hJob, win32job.JobObjectExtendedLimitInformation)
                extended_info['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE # Use |= to preserve other flags
                win32job.SetInformationJobObject(self.hJob, win32job.JobObjectExtendedLimitInformation, extended_info)
                print(f"Job Object {self.hJob} created and configured to kill on close.")

                # 3. Get a handle to the server process
                # PROCESS_TERMINATE is essential for Job Object to terminate it
                perms = win32con.PROCESS_TERMINATE | win32con.PROCESS_SET_QUOTA
                hProcess = win32api.OpenProcess(perms, False, self.server_process.pid)
                if not hProcess:
                    raise win32api.error(win32api.GetLastError(), "OpenProcess")

                # 4. Assign the server process to the Job Object
                win32job.AssignProcessToJobObject(self.hJob, hProcess)
                print(f"Server process {self.server_process.pid} assigned to Job Object {self.hJob}.")

                # 5. Close the process handle (Job Object now manages the reference)
                win32api.CloseHandle(hProcess)

                self._wait_for_server_ready()
                ctx.log("Llama.cpp server is ready.")
            except FileNotFoundError:
                ctx.log(f"Error: Server executable not found.", looking_in_path=self.llama_cpp_server_path)
            except Exception as e:
                ctx.log(f"Error starting llama.cpp server.")
                if self.server_process:
                    self.server_process.kill()
                    self.server_process = None

                raise e

    def _wait_for_server_ready(self, timeout=120):
        """Waits until the llama.cpp server is accessible."""

        start_time = time.time()

        # The /health endpoint is provided by llama.cpp server
        health_url = f"http://{self.host}:{self.port}/health"
        while time.time() - start_time < timeout:
            try:
                # Use requests directly for the health check.
                response = requests.get(health_url, timeout=1)
                if response.status_code == 200 and response.json().get("status") == "ok":
                    return True
            except (requests.exceptions.ConnectionError, json.JSONDecodeError, requests.exceptions.ReadTimeout):
                pass
            time.sleep(1)

        raise TimeoutError(f"Llama.cpp server did not become ready within {timeout} seconds.")

    def stop_server(self):
        """Stops the llama.cpp server subprocess."""

        with logger.begin_event("Stopping server...") as ctx:
            if self.server_process:
                self.server_process.terminate()  # Send SIGTERM
                try:
                    self.server_process.wait(timeout=10) # Wait for a bit for it to terminate
                except subprocess.TimeoutExpired:
                    self.server_process.kill() # Force kill if it doesn't terminate
                self.server_process = None
            else:
                ctx.log("Server is not running - doing nothing.")

            if self.hJob:
                print(f"Closing Job Object handle {self.hJob}.")
                win32api.CloseHandle(self.hJob)
                self.hJob = None

    async def single_async_call(self, messages, use_stream = None):
        """
        Calls the llama.cpp server using the OpenAI client for chat completion.
        Messages should be in OpenAI chat format:
        [{"role": "user", "content": "Hello!"}]
        """

        # Prepend the phrase by adding an assistant message
        # This makes the model *start* its generation with this phrase
        if self.prepend_phrase is not None:
            messages = messages + [{"role": "assistant", "content": self.prepend_phrase}]

        model_name = self.model_path.split(os.sep)[-1] # Just the model name (e.g., "my_model.gguf")

        prediction = ""
        if use_stream is not None:
            # Streaming call
            stream_response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True,
                temperature=0.02,
            )

            async for chunk in stream_response:
                try:
                    new_word = chunk.choices[0].delta.content or ""
                    if new_word:
                        use_stream.put(new_word, already_detokenized=True)
                        prediction += new_word
                except Exception as e:
                    # First entry has nothing, as does last (usually).
                    # NOTE: This was the case with llcp python. IDK about server. TODO
                    pass
        else:
            # Non-streaming call
            completion = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=False,
                temperature=0.02,
            )
            prediction = completion.choices[0].message.content

        return prediction
    
    async def batch_async(self, batch_inputs, use_stream = None):
        tasks = [self.single_async_call(messages, use_stream) for messages in batch_inputs]
        predictions = await asyncio.gather(*tasks)

        return predictions

    def call_llm(self, batch_inputs, use_stream = None):
        predictions = asyncio.run(self.batch_async(batch_inputs, use_stream))
        return predictions

    def call_llm_no_batch(self, messages, use_stream = None):
        # For non-batched inference (99% of the calls go here).
        return self.call_llm([messages], use_stream=use_stream)[0]

    def call_llm_with_batch(self, batch_inputs):
        # For batched inference. batch_inputs should be a List of messages.
        return self.call_llm(batch_inputs, use_stream=None)