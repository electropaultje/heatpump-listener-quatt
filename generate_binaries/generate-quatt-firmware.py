from importlib.metadata import files
import pathlib
import subprocess
import hashlib
import shutil

def md5_checksum(filepath):
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()

base_yaml = "../yaml/packages/base.yaml"
base_yaml_json = pathlib.Path(base_yaml).read_text()
release_file_json = pathlib.Path("./release-file-base.json").read_text()

import re
match = re.search(r' version:\s"*([^\s]+)"', base_yaml_json)
version_number = match.group(1) if match else "notfound"
match = re.search(r'name:\s*([^\s]+)', base_yaml_json)
project_name = match.group(1) if match else "notfound"

build_path = f"../yaml/.esphome/build/{project_name}"
compiled_file = f"{build_path}/.pioenvs/{project_name}/firmware.bin"

variants = [
    {"version": "quatt-single-2relay", "folder": "single"},
    {"version": "quatt-duo-2relay", "folder": "duo"},
    {"version": "quatt-single-4relay", "folder": "single"},
    {"version": "quatt-duo-4relay", "folder": "duo"}
]
for v in variants:
    # STEP 3: Compile generated YAML into ESPHome binary file
    print(f"Compiling firmware")

    result = subprocess.run(f"esphome compile ../yaml/{v['version']}.yaml", capture_output=True, text=True)

    if result.returncode == 0:
        print(f"Copy firmware binary to deployment directory")

        # STEP 4: Copy compiled file into version binary in correct publish directory
        version_filename = f"{v['version']}-v{version_number.replace('.', '-')}.bin"
        version_path = f"../{v['folder']}/{version_filename}"

        shutil.copy(compiled_file, version_path)

        # STEP 5: Copy compiled file into latest binary in correct publish directory
        latest_filename = f"../{v['folder']}/{v['version']}-latest.bin"
        shutil.copy(compiled_file, latest_filename)

        # STEP 6: Calculate MD5 checksum
        md5 = md5_checksum(latest_filename)
        print(f"Calculated checksum: {md5}")

        # STEP 7: Write calculated checksum into latest file
        pathlib.Path(f"../{v['folder']}/{v['version']}-latest.md5").write_text(md5)
        print(f"Checksum written to file")

        # STEP 8: Update release file
        out_yaml = release_file_json.replace("##MD5##", md5).replace("##FILE##", version_filename).replace("##FOLDER##", v['folder']).replace("##VERSION##", version_number)
        pathlib.Path(f"../{v['version']}-release.json").write_text(out_yaml)
    else:
        print(f"Compilation failed for {v['version']}")
        print("Error output:")
        print(result.stderr)
