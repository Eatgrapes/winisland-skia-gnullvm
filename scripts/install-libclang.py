import argparse
import hashlib
from pathlib import Path
import shutil
import tarfile
import urllib.request


parser = argparse.ArgumentParser()
parser.add_argument("output", type=Path)
args = parser.parse_args()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
url = "https://github.com/llvm/llvm-project/releases/download/llvmorg-23.1.2/clang%2Bllvm-23.1.2-x86_64-pc-windows-msvc.tar.xz"

extracted = set()
with urllib.request.urlopen(url) as response:
    with tarfile.open(fileobj=response, mode="r|xz") as archive:
        for entry in archive:
            name = Path(entry.name).name.lower()
            if not entry.name.lower().endswith("/bin/") and not name.endswith(".dll"):
                continue
            if not (name.startswith("libclang") or name.startswith("libllvm") or name == "llvm-c.dll"):
                continue
            if shutil.disk_usage(output).free < entry.size + 100 * 1024 * 1024:
                raise RuntimeError("Not enough disk space to extract libclang runtime")
            target = output / Path(entry.name).name
            with archive.extractfile(entry) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            extracted.add(target.name)
            print(f"Extracted {target.name}: {entry.size} bytes", flush=True)

if "libclang.dll" not in {name.lower() for name in extracted}:
    raise RuntimeError("The LLVM archive contains no libclang.dll")
