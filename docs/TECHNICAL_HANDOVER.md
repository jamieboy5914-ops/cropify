# Cropify  Technical Handover

**Project.** Cotton leaf pest and disease detection, combining a convolutional
neural network for image classification with an ESP32 sensor node reporting
environmental conditions to a web dashboard.

**Purpose of this document.** A record of what was wrong, what was changed and
every address, pin and value in use, written for a technical reader picking the
project up. Section 12 lists what remains outstanding.

**Status.** All build work complete and verified. Written submission incomplete.

---

## 1. Why the work was redone

Three marker reports failed the original submission. The substantive technical
objections were these.

| Objection | Finding on investigation |
|---|---|
| "No technical or academic merit" | The prediction route was a stub. No model was ever loaded. |
| "None of the objectives are being met" | Accurate. Nothing was demonstrable. |
| "Weakest part is the Experimental Modelling and the Design Approach" | No experiments existed. One accuracy figure, no method. |
| "Graphical presentation is poor quality, taken from existing literature" | Accurate. |
| "The reference list seems fake" | References present but never cited in text. |
| "No title of the project within the report, no author stated" | Accurate. |
| Student could not answer viva questions | Consistent with the above. |

An accuracy of 92 percent had been reported at interim stage. Section 3 explains
why that figure could not be defended.

---

## 2. Faults found in the original codebase

Repository: `github.com/Danish08-10/FYP`, single commit dated 17 January 2026,
676 MB of which 665 MB was the image dataset committed into git.

**Blocking faults**

1. **`/prediction` never ran the model.** The route returned a literal string:
   `jsonify('This logic is under development it will be functional once the API is tested')`.
   No model was loaded anywhere in the application.

2. **Total test-set leakage.** See section 3.

3. **Input size mismatch.** Training code used 256 pixels, the report stated 224.
   A model trained at one size and served at another loses accuracy silently.

**Evaluation faults, all of which inflate or corrupt reported metrics**

4. `steps = samples // batch_size` used integer division, dropping the final
   partial batch from every evaluation.
5. The data generator was not reset before `predict` so predictions and labels
   could misalign and the confusion matrix became meaningless.
6. Only overall accuracy was reported. No per-class precision, recall or F1 so a
   class the model never predicted correctly would not show.

**Lesser faults**

7. `login.html` requested `/static/CSS/lsstyle.css` with a capital directory name
   against a lowercase `css/` folder. Works on Windows, fails on Linux.
8. Hard-coded Windows absolute paths in the training script.
9. Four unrelated colour schemes across the pages.
10. The dashboard page carried no navigation and was visually disconnected.

---

## 3. The dataset leakage problem

**The original dataset** held 2,080 image files. Those files derived from **160
photographs**, 40 per class, each expanded offline into 13 saved variants with
names such as `rotation_35.jpg`, `zoom_35.jpg`, `constract_high_zoom_35.jpg`.

Those 2,080 files were split at random, treating each variant as an independent
image. A grouping check found **156 of 156 test photographs also present in the
training set**. Every test image was a transformed copy of a leaf the model had
already learned.

Hashing also found **111 byte-identical duplicate files**.

Any accuracy from that split measures recall of seen images, not generalisation.
Kapoor and Narayanan (2023) document the same failure across 294 published
papers and note it leaves no trace in the results themselves which is why the
figure survived to the viva unchallenged.

**Resolution.** Dataset replaced and the split rewritten to group by source
photograph so all variants of one photograph land in a single split. Verification
prints the count of photographs shared between splits. It must read zero.

---

## 4. Dataset in use

**Source.** SAR-CLD-2024, Kaggle slug **`sheikhrafi/cotton-leaf-disease`**,
approximately 2 GB.

The archive ships two collections. **Only `Original Dataset` is used.** The
`Augmented Dataset` folder is deleted programmatically before any file is read
since training on it would reproduce the fault in section 3. The loader also
removes the empty wrapper directory left behind after the class folders are
raised because an empty directory is otherwise counted as an eighth class and
breaks the split.

**Composition.** 2,137 image files from 2,137 photographs. Files equal
photographs so this collection carries no offline augmentation.

| Class | Photographs | Test set |
|---|---|---|
| Bacterial Blight | 250 | 51 |
| Curl Virus | 431 | 87 |
| Healthy Leaf | 257 | 52 |
| Herbicide Growth Damage | 280 | 56 |
| Leaf Hopper Jassids | 225 | 46 |
| Leaf Redding | 578 | 117 |
| Leaf Variegation | 116 | 24 |
| **Total** | **2,137** | **433** |

Class imbalance 5.0 to 1, largest against smallest.

**Known defect in the published data.** Five photographs appear under two
different class labels as byte-identical files, for example `CV00019.jpg` in Curl
Virus and `HL00101.jpg` in Healthy Leaf. Neither label can be confirmed correct.
These ten files remain in the data used for the reported results. They represent
0.5 percent of the dataset and are recorded as a limitation rather than silently
removed.

**Split.** 65 percent train, 15 percent validation, 20 percent test, applied
within each class, grouped by photograph. Seed 42. Verified overlap: zero
photographs shared between training and validation, zero between training and
test.

---

## 5. Model configuration

| Setting | Value | Note |
|---|---|---|
| Input size | 224 × 224 | must match `IMG_SIZE` in the application |
| Batch size | 32 | |
| Optimiser | Adam, learning rate 0.001 | |
| Max epochs | 30 | early stopping halts sooner |
| EarlyStopping | monitor `val_loss`, patience 6, restore best weights | the saved model is the best epoch, not the last |
| ReduceLROnPlateau | factor 0.3, patience 3, floor 1e-6 | |
| Seed | 42 | applied to split and weight initialisation |
| Class weights | inverse class frequency | required at 5:1 imbalance |

**Augmentation**, applied on the fly to training data only. Validation and test
data are never augmented. Rotation 25 degrees, zoom 0.2, width and height shift
0.15, shear 0.15, horizontal and vertical flip, brightness 0.8 to 1.2.

**Architecture A, baseline CNN.** The original project's network, retained
unchanged so architecture is the only variable in the comparison. Five
convolutional blocks 16 to 256 filters, max pooling after each, dense 512,
dropout 0.5. **3,673,511 parameters, all trainable.**

**Architecture B, MobileNetV2 transfer.** ImageNet weights, base frozen, global
average pooling, batch normalisation, dense 128, dropout 0.4. **2,427,975
parameters of which 167,431 trainable.**

Architecture B holds fewer total parameters and fits 22 times fewer of them.

---

## 6. Results

Ablation, each row adding one change to the row above. Identical split, identical
433-photograph test set throughout.

| Step | Change added | Epochs | Best val acc | Test acc | Macro F1 | Gain |
|---|---|---|---|---|---|---|
| A | none | 18 | 0.7587 | 0.7298 | 0.6898 | - |
| B | on-the-fly augmentation | 30 | 0.7238 | 0.6905 | 0.6022 | **−0.0876** |
| C | class weights | 30 | 0.8032 | 0.7829 | 0.7589 | +0.1567 |
| D | transfer learning | 21 | 0.9206 | 0.9307 | 0.9250 | +0.1661 |

**Augmentation alone reduced macro F1.** Per-class recall locates the cause. Leaf
Variegation, the smallest class at 116 photographs, fell from 0.583 recall at
step A to **0.125** at step B, meaning 3 of its 24 test photographs were found.
Leaf Redding, the largest at 578, moved the other way, 0.803 to 0.872.
Augmentation widens within-class variation and a small class cannot cover the
widened spread. Class weighting reversed it: Leaf Variegation recall returned to
0.958 at step C.

Class weighting and transfer learning contributed **0.1567 and 0.1661** which
sit 0.0094 apart. Neither change carries the result alone and augmentation
repaid nothing until weighting was in place beside it.

**Per-class F1, step D**

| Class | Precision | Recall | F1 |
|---|---|---|---|
| Bacterial Blight | 0.891 | 0.804 | 0.845 |
| Curl Virus | 0.988 | 0.966 | 0.977 |
| Healthy Leaf | 0.877 | 0.962 | 0.917 |
| Herbicide Growth Damage | 1.000 | 0.964 | 0.982 |
| Leaf Hopper Jassids | 0.863 | 0.957 | 0.907 |
| Leaf Redding | 0.939 | 0.915 | 0.926 |
| Leaf Variegation | 0.885 | 0.958 | 0.920 |

**Error concentration.** Step D misclassified 30 of 433. Eleven of those 30
involve one pair exchanging places: 6 Bacterial Blight predicted as Leaf Redding,
5 Leaf Redding predicted as Bacterial Blight. **That single pair accounts for 37
percent of all errors.** Both conditions present as reddish discolouration so
they share the colour signature the model relies on. Separating them needs lesion
boundary detail which is reduced at 224 pixels.

**Generalisation check.** The saved model was tested against a healthy cotton
leaf from the earlier, unrelated dataset. It returned Healthy Leaf at 99.62
percent confidence on an image from a different source.

**Out-of-distribution behaviour.** Legacy test images from the earlier dataset
misclassify. `bb1.jpeg`, a bacterial blight sample, returns Healthy Leaf at 22.9
percent, below the 60 percent confidence floor so the application flags it as
uncertain rather than reporting it. This is expected behaviour for a model
trained on one controlled collection and is recorded as a limitation.

---

## 7. Hardware

**Board.** ESP32 DevKit, 30 pin, USB-C.

Pin rows as printed on the board:

```
left   3V3  GND  D15  D2   D4   D16  D17  D5   D18  D19  D21  RX0  TX0  D22  D23
right  VIN  GND  D13  D12  D14  D27  D26  D25  D33  D32  D35  D34  VN   VP   EN
```

**Sensors and connections**

| Sensor | Pin on sensor | ESP32 pin | Wire |
|---|---|---|---|
| DHT11 | `+` | 3V3 | red |
| DHT11 | `out` | **GPIO 14** | white |
| DHT11 | `−` | GND | purple |
| Capacitive soil v1.2 | `VCC` | 3V3 | red |
| Capacitive soil v1.2 | `AOUT` | **GPIO 32** | yellow |
| Capacitive soil v1.2 | `GND` | GND | black |

DHT11 silkscreen reads `+ out −`. Soil sensor silkscreen reads `GND VCC AOUT`.

**Why GPIO 32 for the analogue probe.** The ESP32 carries two analogue to
digital converters. ADC2 which serves GPIO 0, 2, 4, 12 to 15 and 25 to 27,
becomes unavailable once the Wi-Fi radio is active. An analogue probe on any of
those pins reads correctly on the bench and then fails silently the moment the
board connects to a network. GPIO 32 is on ADC1 and is unaffected. GPIO 14 is
acceptable for the DHT11 because that sensor uses a digital protocol.

**Soil probe calibration.** Method: probe held in dry air, raw value recorded;
probe stood in water to the printed line, raw value recorded.

| Condition | Raw ADC value |
|---|---|
| Dry air | **4095** |
| In water, to the line | **1648** |

Working range 2,447 counts. Resolution 12 bit, 0 to 4095. Each reading is the
mean of 20 samples taken 5 ms apart because a single analogue sample is noisy.

**Note on the dry figure.** 4095 is the converter ceiling so the probe saturates
the input in open air. Soil, including dry soil, reads below it. A value of
exactly 4095 therefore means "at least as dry as air" rather than a precise
measurement.

**DHT11 specification.** 0 to 50 °C at ±2 °C. 20 to 90 percent relative humidity
at ±5 percent. Minimum 1 second between reads; the firmware uses 2 seconds.

The ±5 percent humidity figure is coarse relative to the humidity bands
associated with bacterial blight development. A DHT22 at ±2 percent would be the
appropriate upgrade.

---

## 8. Firebase

| Item | Value |
|---|---|
| Project ID | `cropify-9980a` |
| Product | Realtime Database, **not** Firestore |
| Region | `asia-southeast1`, Singapore |
| Host | `cropify-9980a-default-rtdb.asia-southeast1.firebasedatabase.app` |
| Path | `/sensors.json` |
| Method | HTTPS **PUT** |
| Rules | test mode |

Note the host form. Databases outside the United States do not use
`firebaseio.com`. A Singapore database resolves at
`<name>.asia-southeast1.firebasedatabase.app` and using the wrong form produces
a DNS failure that reads like a network fault.

**Access approach.** The firmware writes through the REST interface using
`WiFiClientSecure` with `setInsecure()` and `HTTPClient`. No Firebase client
library is used. This keeps the dependency surface to the DHT library alone and
allows the same URL to be verified in a browser which shortens diagnosis
considerably.

**PUT rather than POST.** PUT replaces the value at the path so the database
holds only the most recent reading. POST would append and grow without bound.
Section 9 covers the consequence.

**Payload schema.**

```json
{
  "temperature":   30.3,
  "humidity":      63.1,
  "soil_moisture": 0,
  "soil_raw":      4095,
  "uptime_s":      405
}
```

`soil_moisture` is the calibrated percentage. `soil_raw` is the unprocessed ADC
value, retained so a reading can be re-derived if calibration is revised.
`uptime_s` is seconds since board reset and is used for liveness detection.

**Timing.** Sensors read and printed locally every 2 seconds. Upload every 15
seconds.

**Security position.** Test mode rules permit unauthenticated read and write and
expire 30 days after creation. Acceptable for a demonstration, unacceptable for
deployment. Recorded as a limitation with authentication identified as future
work.

---

## 9. Application

Flask. Model loaded once at start-up rather than per request.

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | home |
| `/aboutapp` | GET | about |
| `/dashboard` | GET | live sensor dashboard |
| `/login`, `/signup` | GET | pages exist, no backend, see section 12 |
| `/prediction` | GET | upload form |
| `/prediction` | POST | classify an uploaded image |
| `/data` | GET | JSON, latest reading from Firebase |
| `/health` | GET | model load state, class list, parameter count |

**Files.** Model at `models/cotton_model.keras`. Labels at
`models/class_names.json`; the order in that file must match the model's output
order or every prediction is mislabelled. Treatment guidance at
`treatment.json`. Uploads written to `static/uploads/`.

**Constants.** `IMG_SIZE = 224` which must equal the training input size.
Confidence floor 0.60; below it the result carries an explicit uncertainty
notice rather than presenting a low-confidence guess as a diagnosis.

**Template contract.** The upload form posts under field name `file`; the route
also accepts `image` or any single uploaded file since the original template
markup was inconsistent. `result.html` expects three variables: `filename`,
`prediction`, `Cure`.

**Liveness detection.** Because Firebase retains only the last reading, a node
that stops uploading leaves a stale value that a naive dashboard would present as
current. The `/data` route records when the board's reported `uptime_s` last
changed and returns `stale_for` in seconds. The dashboard displays a warning
above 60 seconds rather than showing an old value as live.

This is an imperfect substitute for a server-side timestamp which would be the
correct solution. It is sufficient to prevent the dashboard from misreporting an
offline node.

**Dashboard.** Polls `/data` every 2 seconds. Renders temperature, humidity and
soil moisture as filled bars, with a status line carrying the raw soil value and
node uptime. Served from `templates/dashboard.html`.

**Front end.** All pages share `static/css/theme.css`. Single palette, primary
`#2f9e58`. Responsive, with the navigation collapsing to a menu button below 760
pixels. The prediction page shows a progress overlay during inference.

---

## 10. Toolchain

| Component | Version |
|---|---|
| Arduino IDE | 2.3.10 |
| ESP32 board core | 3.3.11 |
| Board selection | ESP32 Dev Module |
| DHT library | DHT sensor library by Adafruit, 1.4.7 |
| Serial monitor | 115200 baud |
| Training | Google Colab, T4 GPU |
| TensorFlow | 2.20.0 in Colab |
| Kaggle authentication | legacy API key, `kaggle.json` |

**A note on the DHT library.** An unrelated library, `AM2302-Sensor` by Frank
Häfele, was installed at one point. It supplies a header named `DHT.h` so the
sketch compiles cleanly and then returns no readings at all. If a DHT sensor
reports `NO READING` on every attempt with no intermittent successes, check which
library is resolving before checking the wiring.

---

## 11. Diagnostic notes worth retaining

**A pin reading exactly 0 differs from a floating pin.** A floating ESP32 analogue
input drifts between roughly 100 and 300 from noise. A pin held at exactly 0 is
being driven to ground which for a sensor output means the sensor is powered but
producing nothing or unpowered. That distinction identified the soil probe fault
faster than continued inspection of the wiring.

**The board carries a single 3V3 pin.** Two sensors sharing it require the
breadboard power rails or one sensor powered from a GPIO pin. A GPIO supplies up
to 40 mA and a DHT11 draws about 2.5 mA so GPIO power is within specification if
needed.

**Breadboard power rails are frequently split at the midpoint.** A jumper in one
half does not reach a sensor in the other. The break is visible as a gap in the
printed red and blue lines.

**Colab sessions do not persist.** Reopening the same notebook allocates a fresh
machine with an empty disk. The trained model must be re-uploaded or kept on
Google Drive. Training takes 25 to 40 minutes; re-uploading takes seconds.

---

## 12. Outstanding

**Written submission**

- Project title on the cover page. Absent and the first objection in all three
  marker reports.
- Author name, student number, supervisor, course, date.
- Objectives rewritten. They currently specify four cotton **diseases** and a 90
  percent accuracy target. The system detects **seven** classes, two of which are
  pests, on a different dataset. Left unchanged, the report describes a different
  project from the one built.
- Abstract rewritten. The existing opening sentences were quoted back by a marker
  as meaningless.
- In-text citations throughout.
- **Every citation verified.** The six drafted for the Experimental Modelling
  section were written without web access and no DOI has been confirmed. Given
  "the reference list seems fake" was a direct quotation against the original
  submission, this is not optional.
- SAR-CLD-2024 cited, with authors, year and version from its Kaggle page.
- Self-evaluation form completed. Currently blank.

**Code and repository**

- Repository updated. It presently contains none of this work.
- Wi-Fi credentials replaced with placeholders before any commit. Git retains
  deleted content in history so a committed password remains recoverable.
- Login and signup pages either completed or removed. The markup exists with no
  backend which reads worse than their absence.
- Dataset removed from git and referenced by Kaggle slug instead. The original
  repository committed 665 MB of images.

**Optional, if time allows**

- Retrain with the five ambiguous duplicate pairs removed, to quantify their
  effect.
- Repeat runs with different seeds, to bound the step B result.
- Field photographs, to test performance outside controlled capture conditions.

---

## 13. Credentials

Not recorded here.

- **Wi-Fi SSID and password** are set in the firmware at the top of
  `stage2_firebase.ino`, in `WIFI_SSID` and `WIFI_PASS`.
- **Kaggle API token** lives at `~/.kaggle/kaggle.json`.
- **Firebase** requires no key in this configuration because test mode rules
  permit unauthenticated access. This is itself the security limitation noted in
  section 8.
