#test_env.py
import importlib

packages = ["langchain", "langgraph", "google_genai", "cv2", "torch"]

print("== ENV CHECK ==")

for pkg in packages:
    try:
        importlib.import_module(pkg)
        print(f"{pkg}: OK")
    except ModuleNotFoundError:
        print(f"{pkg}: ERROR -> Not installed")
