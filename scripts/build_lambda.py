import os
import subprocess
import shutil

service = "index-calculator"
build_dir = "build_linux"
requirements = f"services/{service}/requirements.txt"

if os.path.exists(build_dir):
    shutil.rmtree(build_dir)
os.makedirs(build_dir)

# 1. Install all dependencies normally first to get the list
print("Installing all dependencies...")
subprocess.run(["pip", "install", "-r", requirements, "-t", build_dir, "--quiet"])

# 2. Get the list of all installed packages (directories)
installed_packages = [d for d in os.listdir(build_dir) if os.path.isdir(os.path.join(build_dir, d)) and not d.endswith('.dist-info')]
print(f"Detected packages: {installed_packages}")

# 3. For each package, try to force-install the Linux binary version
# If it fails (pure python), it's fine.
# We enforce strict versions for pydantic and pydantic-core to avoid SystemError
binary_targets = [
    "asyncpg==0.29.0", 
    "sqlalchemy==2.0.30", 
    "pydantic==2.10.3", 
    "pydantic-core==2.27.1", 
    "annotated-types==0.7.0",
    "typing-extensions==4.12.2", 
    "anyio==4.4.0"
]
for pkg in binary_targets:
    print(f"Overriding {pkg} with Linux binary...")
    subprocess.run([
        "pip", "install", pkg,
        "-t", build_dir,
        "--platform", "manylinux2014_x86_64",
        "--implementation", "cp",
        "--python-version", "3.11",
        "--only-binary=:all:",
        "--upgrade",
        "--quiet"
    ])

# 4. Copy source code
print("Copying source code...")
for item in os.listdir(f"services/{service}"):
    s = os.path.join(f"services/{service}", item)
    d = os.path.join(build_dir, item)
    if os.path.isdir(s):
        shutil.copytree(s, d, dirs_exist_ok=True)
    else:
        shutil.copy2(s, d)

print("Build directory ready for zipping.")
