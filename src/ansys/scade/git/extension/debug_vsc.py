# enable debugging of an embedded Python script

import os
#import scade

def log(text: str):
    """
    Display the input message in the `Messages` output tab.

    The messages are prefixed by 'Git Extension - '.

    Parameters
    ----------
    text : str
        Message to display.
    """
    if text:
        # scade is a CPython module defined dynamically
        #scade.tabput("LOG", "Git Extension - " + text + "\n")  # type: ignore
        print("Git Extension: " + text + "\n")


log("init debug\n")
os_module_path = os.path.dirname(os.path.realpath(os.__file__))
python_exe = os.path.join(os_module_path, "..", "python.exe")

log(f"python exec = {python_exe}\n")

try:
    import debugpy
    log("loaded debugpy\n")
    
    os.environ["PYDEVD_LOAD_NATIVE_LIB"] = "0"
    os.environ["PYDEVD_USE_CYTHON"] = "0"
    
    debugpy.configure(python=python_exe)
    debugpy.listen(("127.0.0.1", 5678))
    debugpy.wait_for_client()
    
except ImportError as e:
    log(f"Git Extension ERROR: debugpy not found - {e}\n")
except Exception as e:
    log(f"Git Extension ERROR: {type(e).__name__}: {e}\n")

# enable logging
# try:
#     debugpy.log_to('C:/tmp/logs')
# except:
#     pass
#import time

#while True:
#    time.sleep(1)