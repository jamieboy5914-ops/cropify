# Cropify — Cotton Leaf Pest and Disease Detection

A precision agriculture system in two halves. A convolutional neural network
classifies a photographed cotton leaf into one of seven conditions. An ESP32
sensor node reports temperature, humidity and soil moisture to a cloud database,
which a web dashboard reads live.

Seven classes: Bacterial Blight, Curl Virus, Healthy Leaf, Herbicide Growth
Damage, Leaf Hopper Jassids, Leaf Redding, Leaf Variegation.

Two of those are pests rather than diseases, so the project is described as pest
**and** disease detection. The title matches what the model does.

---

## Repository layout

```
app.py                    Flask application
treatment.json            guidance text shown beside each prediction
requirements.txt

templates/                web pages
static/css/theme.css      shared palette and layout, all pages use it
static/assets/            logo and background images

src/download_dataset.py   fetch the dataset from Kaggle
notebooks/                training, dataset audit, and a one-cell app runner
hardware/                 ESP32 firmware, three stages
docs/                     technical handover, setup guides, a report section
archive/original_code/    the 16 code files from the original submission
models/                   trained model goes here, not committed
data/                     dataset goes here, not committed
figures/  results/        training outputs
```

The dataset and the trained model are **deliberately absent**. See below.

---

## Quick start

```bash
pip install -r requirements.txt
python src/download_dataset.py          # needs a Kaggle API token
python app.py                           # needs models/cotton_model.keras
```

Then open `http://127.0.0.1:5000`. Check `/health` first to confirm the model
loaded.

To train, open `notebooks/TRAIN_IN_COLAB.ipynb` in Google Colab with a T4 GPU.
Training on a CPU takes hours.

---

## Dataset

**SAR-CLD-2024**, Kaggle slug `sheikhrafi/cotton-leaf-disease`.

2,137 photographs across 7 classes. Files equal photographs, so this collection
carries no offline augmentation. Class imbalance 5 to 1, largest against
smallest, which is why class weights are applied and macro F1 is reported
alongside accuracy.

The archive ships an `Augmented Dataset` folder beside an `Original Dataset`
folder. **Only the original is used.** `src/download_dataset.py` deletes the
augmented copy before anything reads it.

### Why the dataset changed

The original submission used a different dataset, and it had a fault that
invalidated every reported result.

That dataset held 2,080 image files. Those files derived from **160
photographs**, 40 per class, each expanded offline into 13 saved variants named
`rotation_35.jpg`, `zoom_35.jpg` and so on. The 2,080 files were then split at
random, treating each variant as an independent image.

A grouping check found **156 of 156 test photographs also present in the training
set**. Every test image was a transformed copy of a leaf the model had already
learned. An accuracy measured that way describes memorisation, not
generalisation, which is why the 92 percent reported at interim stage could not
be defended.

Hashing also found 111 byte-identical duplicate files.

The current split groups by source photograph, so all variants of one photograph
land in a single split. Verification prints the count of photographs shared
between splits, and it must read zero.

---

## Results

Ablation, each row adding one change to the row above. Identical split,
identical 433-photograph test set.

| Step | Change added | Test accuracy | Macro F1 | Gain |
|---|---|---|---|---|
| A | none | 0.7298 | 0.6898 | – |
| B | on-the-fly augmentation | 0.6905 | 0.6022 | **−0.0876** |
| C | class weights | 0.7829 | 0.7589 | +0.1567 |
| D | transfer learning, MobileNetV2 | **0.9307** | **0.9250** | +0.1661 |

Augmentation alone **reduced** performance. The smallest class, Leaf Variegation
at 116 photographs, dropped from 0.583 recall to 0.125, meaning 3 of its 24 test
photographs were found. The largest class improved. Augmentation widens
within-class variation, and a small class cannot cover the widened spread. Class
weighting returned that recall to 0.958.

Class weighting and transfer learning contributed 0.1567 and 0.1661, figures
0.0094 apart. Neither carries the result alone.

Full detail, including per-class metrics and error analysis, is in
`docs/TECHNICAL_HANDOVER.md` and `docs/SECTION_experimental_modelling.md`.

---

## Hardware

ESP32 DevKit, DHT11, capacitive soil moisture probe v1.2.

| Sensor pin | ESP32 pin |
|---|---|
| DHT11 `out` | GPIO 14 |
| Soil `AOUT` | GPIO 32 |
| both `VCC` | 3V3 |
| both `GND` | GND |

**GPIO 32 for the analogue probe is deliberate.** The ESP32 has two analogue
converters and ADC2 stops working once the Wi-Fi radio is active. A probe on any
ADC2 pin reads correctly on the bench and then fails silently the moment the
board joins a network. GPIO 32 is on ADC1.

**Soil calibration**, measured on this probe. Dry air 4095, in water to the
printed line 1648. 4095 is the converter ceiling, so the probe saturates in open
air and a reading of exactly 4095 means "at least as dry as air" rather than a
precise value.

Firmware runs in three stages: `stage1_sensor_test.ino` proves the sensors,
`stage2_firebase.ino` adds Wi-Fi and uploads, `soil_diagnostic.ino` locates a
mis-wired analogue pin.

Wiring and setup steps are in `docs/hardware_setup.md`.

---

## Cloud

Firebase Realtime Database, region `asia-southeast1`, path `/sensors.json`,
written by HTTPS PUT every 15 seconds.

PUT rather than POST, so the database holds only the newest reading instead of
growing without bound. The consequence is that a node which stops uploading
leaves a stale value behind, so `/data` tracks whether the board's reported
uptime is still advancing and the dashboard warns when a reading is over 60
seconds old rather than presenting it as live.

**Security.** Test mode rules permit unauthenticated read and write, and they
expire 30 days after creation. Acceptable for a demonstration, unacceptable for
deployment. Authentication is identified as future work.

---

## Application routes

| Route | Purpose |
|---|---|
| `/` | home |
| `/prediction` | upload a leaf, GET the form and POST the image |
| `/dashboard` | live sensor readings |
| `/data` | JSON, latest reading from Firebase |
| `/health` | model load state, classes, parameter count |
| `/aboutapp` | about |
| `/login`, `/signup` | pages exist, no backend, see Known issues |

`IMG_SIZE` in `app.py` must equal the training input size of 224. A mismatch
costs accuracy with no visible error.

Predictions below 60 percent confidence carry an explicit uncertainty notice
rather than presenting a low-confidence guess as a diagnosis.

---

## What changed from the original submission

The `archive/original_code/` folder holds all 16 code files as submitted, for
comparison.

**Blocking faults**

- `/prediction` returned the literal string
  `'This logic is under development it will be functional once the API is tested'`
  and no model was ever loaded.
- Total test-set leakage, described above.
- Training used a 256 pixel input while the report stated 224.

**Evaluation faults**

- `steps = samples // batch_size` dropped the final partial batch from every
  evaluation.
- The generator was not reset before `predict`, so predictions and labels could
  misalign and the confusion matrix became meaningless.
- Only overall accuracy was reported, so a class the model never got right would
  not show.

**Presentation**

- Four unrelated colour schemes across the pages, no shared stylesheet, no
  responsive layout. All pages now share `static/css/theme.css`.
- The dashboard had no navigation.

---

## Known issues

- `login.html` and `signup.html` have markup and no backend. Either finish them
  or remove them, since a page that looks functional and does nothing reads worse
  than its absence.
- `login.html` requests `/static/CSS/lsstyle.css` with a capital directory name
  against a lowercase `css/` folder. Works on Windows, fails on Linux.
- Five photographs in SAR-CLD-2024 appear under two different class labels as
  byte-identical files. Ten files, 0.5 percent of the dataset, present in the
  data used for the reported results and recorded as a limitation.
- The model is trained on one controlled collection and misclassifies images from
  other sources. Confidence falls below the 60 percent floor in those cases, so
  the application flags them rather than reporting them.

---

## Credentials

None are stored in this repository.

`hardware/stage2_firebase.ino` carries placeholders for the Wi-Fi name and
password. Fill them in locally and **do not commit the real values**. Git retains
deleted content in its history, so a password committed once stays recoverable.

The Kaggle API token belongs at `~/.kaggle/kaggle.json` and is excluded by
`.gitignore`.
