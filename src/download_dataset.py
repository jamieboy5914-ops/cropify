"""
Download the cotton leaf dataset from Kaggle.

This project uses SAR-CLD-2024, not the dataset committed to the original
repository. The original held 2,080 files built from only 160 photographs,
each expanded offline into 13 saved variants, and a random split placed
variants of one photograph on both sides. See docs/TECHNICAL_HANDOVER.md
section 3.

ONE-TIME SETUP
    1. Sign in at kaggle.com, open Settings, find the API section
    2. Click Create Legacy API Key. A kaggle.json file downloads
    3. Move it to  ~/.kaggle/kaggle.json  on Mac or Linux, or
       C:\\Users\\<you>\\.kaggle\\kaggle.json  on Windows
    4. pip install kaggle

THEN
    python src/download_dataset.py
"""
import os
import shutil
import subprocess
import sys

DATASET = "sheikhrafi/cotton-leaf-disease"
RAW = "data/raw"

# The archive ships an Original Dataset folder beside an Augmented Dataset
# folder. Only the original is used. Training on the augmented copy would
# reproduce the leakage fault this project exists to correct.
SKIP_WORDS = ("augment", "hog", "black and white", "grayscale", "greyscale")

EXPECTED = ["Bacterial Blight", "Curl Virus", "Healthy Leaf",
            "Herbicide Growth Damage", "Leaf Hopper Jassids",
            "Leaf Redding", "Leaf Variegation"]

IMG_EXT = (".jpg", ".jpeg", ".png")


def download():
    os.makedirs(RAW, exist_ok=True)
    if any(os.scandir(RAW)):
        print("Already downloaded.")
        return
    print("Downloading", DATASET, "to", RAW)
    try:
        subprocess.run(["kaggle", "datasets", "download", "-d", DATASET,
                        "-p", RAW, "--unzip"], check=True)
    except FileNotFoundError:
        sys.exit("The kaggle command was not found. Run: pip install kaggle")
    except subprocess.CalledProcessError:
        sys.exit("Download failed. A 403 means the dataset terms need "
                 "accepting in a browser first. A 404 means the slug is wrong.")


def remove_processed_copies():
    removed = []
    for dirpath, dirnames, _ in os.walk(RAW, topdown=True):
        for d in list(dirnames):
            if any(w in d.lower() for w in SKIP_WORDS):
                shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)
                dirnames.remove(d)
                removed.append(d)
    for d in sorted(set(removed)):
        print("Removed pre-processed copy:", d)


def find_class_level():
    """Prefer a folder named original. Otherwise match on the class names."""
    named, matched = [], []
    for dirpath, dirnames, _ in os.walk(RAW):
        hits = sum(1 for c in EXPECTED if c in set(dirnames))
        if hits >= 2:
            matched.append((hits, dirpath))
            if "original" in os.path.basename(dirpath).lower():
                named.append((hits, dirpath))
    pool = named or matched
    if not pool:
        return None
    pool.sort(key=lambda t: (-t[0], len(t[1])))
    return pool[0][1]


def raise_class_folders():
    level = find_class_level()
    if level is None:
        print("Could not find the expected class folders. Tree below.")
        for dp, dn, fn in os.walk(RAW):
            depth = dp.replace(RAW, "").count(os.sep)
            if depth > 4:
                continue
            n = sum(1 for f in fn if f.lower().endswith(IMG_EXT))
            print("  " * depth, os.path.basename(dp) or ".",
                  "(%d images)" % n if n else "")
        sys.exit("Edit EXPECTED to match the folder names above.")

    print("Class folders found at", level)
    if os.path.abspath(level) != os.path.abspath(RAW):
        for name in os.listdir(level):
            src = os.path.join(level, name)
            dst = os.path.join(RAW, name)
            if os.path.abspath(src) != os.path.abspath(RAW) \
                    and not os.path.exists(dst):
                shutil.move(src, dst)


def drop_empty_folders():
    """
    The archive wraps everything in one long directory. After the class folders
    are raised that wrapper is left empty, and an empty directory is otherwise
    counted as an eighth class, which breaks the split.
    """
    for d in sorted(os.listdir(RAW)):
        p = os.path.join(RAW, d)
        if not os.path.isdir(p):
            continue
        has_images = any(f.lower().endswith(IMG_EXT) for f in os.listdir(p))
        if not has_images:
            shutil.rmtree(p, ignore_errors=True)
            print("Removed empty folder:", d)


def report():
    print("\nDATASET SUMMARY")
    total = 0
    for cls in sorted(os.listdir(RAW)):
        p = os.path.join(RAW, cls)
        if not os.path.isdir(p):
            continue
        n = len([f for f in os.listdir(p) if f.lower().endswith(IMG_EXT)])
        total += n
        print("   %-26s %5d" % (cls, n))
    print("   %-26s %5d" % ("TOTAL", total))
    print("\nExpected 2137 photographs across 7 classes.")
    print("NEXT STEP: run the split, see notebooks/TRAIN_IN_COLAB.ipynb")


if __name__ == "__main__":
    download()
    remove_processed_copies()
    raise_class_folders()
    drop_empty_folders()
    report()
