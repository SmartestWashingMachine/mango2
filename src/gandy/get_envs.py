import os

web_env_var_const = os.getenv("MANGO_WEB_UI", "0")
ENABLE_WEB_UI = web_env_var_const == "1" or web_env_var_const == 1
