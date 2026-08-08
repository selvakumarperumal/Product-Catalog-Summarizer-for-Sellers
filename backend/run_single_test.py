import os
import subprocess
import sys
import time
import requests

def run_test():
    env = os.environ.copy()

    print("[1/3] Starting FastAPI server...")
    proc = subprocess.Popen(
        ["uv", "run", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8888"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        # Poll health endpoint until server is ready
        server_ready = False
        for _ in range(15):
            try:
                r = requests.get("http://127.0.0.1:8888/api/v1/health", timeout=1)
                if r.status_code == 200:
                    server_ready = True
                    break
            except Exception:
                time.sleep(0.5)

        if not server_ready:
            print("ERROR: Server failed to start within timeout.")
            if proc.poll() is not None:
                out, _ = proc.communicate()
                print("Server output:\n", out)
            sys.exit(1)

        print("[2/3] Server health check OK.")

        # Upload + Summarize (single call, returns CSV directly)
        print("[3/3] Uploading and summarizing product catalog CSV (2 rows)...")
        start_time = time.time()
        with open("test_catalog.csv", "rb") as f:
            res = requests.post(
                "http://127.0.0.1:8888/api/v1/summarize",
                files={"file": ("test_catalog.csv", f, "text/csv")},
            )
        elapsed = time.time() - start_time

        print(f"Status: {res.status_code} (took {elapsed:.2f}s)")
        print(f"\n================ FINAL SUMMARIZED CSV ================")
        print(res.text)
        print("======================================================\n")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    run_test()
