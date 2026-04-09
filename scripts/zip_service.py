import zipfile
import os
import sys

def zip_dir(build_dir, zip_path):
    print(f"Zipping {build_dir} to {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(build_dir):
            for f in files:
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, build_dir)
                z.write(abs_path, rel_path)
    print("Zip created successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python zip_service.py <build_dir> <zip_path>")
        sys.exit(1)
    zip_dir(sys.argv[1], sys.argv[2])
