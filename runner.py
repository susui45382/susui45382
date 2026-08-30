import subprocess
import time
import os

FLAG_FILE = "bot_was_running.flag"

def main():
    first_run = not os.path.exists(FLAG_FILE)

    while True:
        cmd = ["python", "bot.py"]
        
        # Agar bot second time ya start/crash ke baad run ho raha hai to flag pass karein
        if not first_run:
            cmd.append("--restarted")

        # Flag file create karein ki bot run status me hai
        with open(FLAG_FILE, "w") as f:
            f.write("running")

        print("🚀 [Runner] Bot Ko Start Kiya Jaa Raha Hai...")
        process = subprocess.Popen(cmd)
        process.wait()  # Bot ke band hone tak wait karega

        print("⚠️ [Runner] Bot Stop Ya Crash Ho Gaya! Wapas Restart Ho Raha Hai 5 Seconds Me...")
        first_run = False
        time.sleep(5)

if __name__ == "__main__":
    main()
