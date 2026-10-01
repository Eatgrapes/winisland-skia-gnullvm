import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tomllib


parser = argparse.ArgumentParser()
parser.add_argument("--native", type=Path, required=True)
parser.add_argument("--binding-output", type=Path, required=True)
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--llvm-mingw", type=Path, required=True)
parser.add_argument("--registry", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

version = tomllib.loads((args.registry / "Cargo.toml").read_text())["package"]["version"]
vcs_info = json.loads((args.registry / ".cargo_vcs_info.json").read_text())
revision = vcs_info["git"]["sha1"][:20]
target = "x86_64-pc-windows-gnullvm"
key = f"{revision}-{target}-d3d-jpegd-jpege-pdf"

package = args.output / ".package" / "skia-binaries"
package.mkdir(parents=True, exist_ok=True)


def find_archive(directory, *names):
    for name in names:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No archive named {names} in {directory}")


def copy(source, name):
    shutil.copyfile(source, package / name)


copy(find_archive(args.native, "libskia.a", "skia.lib"), "skia.lib")
binding_archive = find_archive(args.binding_output, "libskia-bindings.a", "skia-bindings.lib")
runtime = args.llvm_mingw / "x86_64-w64-mingw32" / "lib"
archives = [binding_archive]
archives += [runtime / name for name in [
    "libc++.a", "libc++abi.a", "libunwind.a", "libwinpthread.a", "libuuid.a", "liboleaut32.a",
]]
for entry in archives:
    if not entry.is_file():
        raise FileNotFoundError(entry)
mri = [f"CREATE {(package / 'skia-bindings.lib').resolve().as_posix()}"]
mri += [f"ADDLIB {entry.resolve().as_posix()}" for entry in archives]
mri += ["SAVE", "END", ""]
subprocess.run([str(args.llvm_mingw / "bin" / "llvm-ar.exe"), "-M"],
               input="\n".join(mri), text=True, check=True)
copy(args.binding_output / "bindings.rs", "bindings.rs")
if (args.binding_output / "skia-defines.txt").is_file():
    copy(args.binding_output / "skia-defines.txt", "skia-defines.txt")
copy(args.source / "LICENSE", "LICENSE-Skia.txt")
copy(args.llvm_mingw / "LICENSE.TXT", "LICENSE-LLVM-MinGW.txt")

(package / "tag.txt").write_text(version + "\n")
(package / "key.txt").write_text(key + "\n")

output = args.output / version
output.mkdir(parents=True, exist_ok=True)
archive = output / f"skia-binaries-{key}.tar.gz"
with tarfile.open(archive, "w:gz", compresslevel=6) as tar:
    for entry in sorted(package.iterdir()):
        tar.add(entry, arcname=f"skia-binaries/{entry.name}", recursive=False)
with archive.open("rb") as stream:
    checksum = hashlib.file_digest(stream, "sha256").hexdigest()
archive.with_name(archive.name + ".sha256").write_text(f"{checksum}  {archive.name}\n")
print(archive)
print(f"SHA256: {checksum}")
