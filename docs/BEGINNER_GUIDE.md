# Beginner guide: running your experiments from zero

Written for someone who has never used Google Colab, Python or Kaggle. Keep this
open beside your browser and work through it in order.

Nothing here requires GitHub. GitHub only stores your code. Training happens in
Google Colab. They are separate jobs, so ignore GitHub until the very end.

---

## Words you will meet

| Word | What it means |
|---|---|
| **Google Colab** | A free website that runs Python code for you, using Google's computers. Like Google Docs, but for code. |
| **Notebook** | A file ending `.ipynb` holding a list of steps. Yours is `TRAIN_IN_COLAB.ipynb`. |
| **Cell** | One block inside a notebook. Grey blocks are code you run. White blocks are text you read. |
| **Runtime** | The computer Google lends you for the session. |
| **GPU** | A fast chip for training models. Free on Colab. Without it, training takes hours instead of minutes. |
| **Dataset** | Your folders of leaf photographs. |
| **Kaggle** | A website hosting public datasets. |
| **Slug** | A dataset's short address on Kaggle, like `owner/name`. |
| **Epoch** | One pass of the model through all your training images. |
| **Training set** | Images the model learns from. |
| **Test set** | Images kept hidden, used once at the end to measure real performance. |
| **Data leakage** | When test images are secretly also in training. It makes results meaningless. |

---

## Stage 1 — Get your accounts ready

**1.1 Google account.** You almost certainly have one. If not, make one at
accounts.google.com.

**1.2 Kaggle account.** Go to **kaggle.com** and sign up. Signing in with Google
is fastest.

**1.3 Get your Kaggle key.** This lets the notebook download data on your behalf.

1. Sign in at kaggle.com
2. Click your profile picture, top right
3. Click **Settings**
4. Scroll down to the **API** section
5. Click **Create New Token**
6. A file called `kaggle.json` downloads, probably to your Downloads folder

Leave it there. You will upload it in Stage 3.

`kaggle.json` is a password in file form. Do not email it, do not put it on
GitHub, do not paste its contents into a chat.

---

## Stage 2 — Open the notebook in Colab

**2.1** Unzip `cotton-disease-fyp.zip` on your computer. Inside, open the
`notebooks` folder. The file you want is `TRAIN_IN_COLAB.ipynb`.

**2.2** Go to **colab.research.google.com** in your browser.

**2.3** A window appears offering recent notebooks. Click the **Upload** tab, then
**Browse**, then choose `TRAIN_IN_COLAB.ipynb`.

If no window appears, click **File** then **Upload notebook**.

**2.4** The notebook opens. You will see a long page of grey and white blocks.
Read the white ones. Run the grey ones.

**2.5 Turn the GPU on. Do not skip this.**

1. Click **Runtime** in the top menu
2. Click **Change runtime type**
3. Under *Hardware accelerator* choose **T4 GPU**
4. Click **Save**

**2.6 How to run a cell.** Click anywhere inside a grey cell, then press
**Shift** and **Enter** together. Output appears underneath.

While a cell is running you see a spinning circle to its left. Wait for it to
stop before running the next one. Work top to bottom and never skip a cell.

**Important:** if you close the tab or your laptop sleeps for a long stretch,
Colab throws away the session and you start again. Keep the tab open and the
laptop awake until Stage 7 finishes.

---

## Stage 3 — Cell 1: install, import, configure

Run it. You want to see a GPU name printed. If it says `NONE`, go back to step 2.5.

Before running, set two things in this cell:

- `DATASET` — your Kaggle slug. Get it from the dataset page: click the **three
  dots** next to Download, choose **Copy API command**, and take the part after `-d`.
- `EXPECTED` — the class folder names, copied exactly from the Kaggle Data Explorer.

Everything else is already set. Note `IMG = 224`, which matches your report. The
old code used 256, and that mismatch was one of the inconsistencies against you.

---

## Stage 3.5 — Audit candidate datasets before you commit

Do this before Stage 4, because most cotton datasets on Kaggle are padded with
augmented copies and you cannot tell from the page.

**3.5.1** Upload `notebooks/CHECK_DATASET_IN_COLAB.ipynb` to Colab. Three cells,
no GPU needed.

**3.5.2** Search kaggle.com for `cotton leaf disease`, `cotton pest` or
`cotton disease detection`. Open anything promising, check the **Data** tab, and
copy two or three slugs.

**3.5.3** Put the slugs in `CANDIDATES` in Cell 2, then run all three cells.

**3.5.4** Read each report card. This is what a padded dataset looks like:

```
class                            files   photographs
Aphids                             520            40
Army worm                          520            40
Bacterial Blight                   520            40
Healthy                            520            40
TOTAL                             2080           160

identical duplicate files : 111
VERDICT
  Padded with augmented copies: about 13 files per photograph.
  Real size is 160 photographs, not 2080 images.
```

**3.5.5 How to choose,** in order of importance:

1. Reject anything with **duplicates across classes**. One photograph carrying two
   labels corrupts both training and testing.
2. Compare the **photographs** column, never **files**. 5000 files from 300
   photographs is smaller than 900 files from 900 photographs.
3. Check the class names. If they differ from your current four, that is fine, but
   your title, aim and objectives must be rewritten to name the classes you
   actually detect. A marker already criticised the title for not matching the work.
4. Above about 3x imbalance, report macro F1 rather than accuracy.
5. Do not merge two datasets. Kaggle uploads often repackage the same images.

**3.5.6** Write down the slug, class names, photograph count, file count,
duplicate count and imbalance ratio. All of it goes in your report.

---

## Stage 4 — Cell 2: download and keep only real photographs

Run it, and pick your `kaggle.json` when the button appears.

Watch for a line saying it removed processed copies. Some datasets ship an
`Augmented Dataset` beside an `Original Dataset`, and this cell deletes the
augmented one. If you are using such a dataset and you do **not** see that line,
stop and tell me, because training on the augmented folder is the exact mistake
being undone.

**Errors you might hit**

- `403 Forbidden` — open the dataset page in a browser once, accept its terms, run again
- `404 Not Found` — the slug is wrong, recheck it character by character
- `Could not find the expected class folders` — a folder tree is printed. Edit
  `EXPECTED` in Cell 1 to match those names exactly, then re-run

---

## Stage 5 — Cell 3: the counts and the split

**This is the most important cell.** Run it and read all the output.

Two columns are printed. **files** is how many image files exist. **photographs**
is how many distinct photographs they came from. If files is much larger, the
dataset was padded with saved copies.

It also reports byte-identical duplicates. Duplicates across classes are serious,
because one photograph would carry two different labels.

Then it splits, keeping every copy of one photograph inside one split, and
verifies it:

```
LEAKAGE VERIFICATION
  photographs shared between train and validation: 0 of 24
  photographs shared between train and test: 0 of 32

  RESULT: NO LEAKAGE - safe to train and report
```

**Those zeros are the point.** Screenshot this. It is your direct answer to the
criticism about technical merit. Write the counts down too.

If it says `LEAKAGE PRESENT`, stop and send me the filenames you saw.

---

## Stage 6 — Cell 4: images and class weights

Run it. It prints how many training images each class has and the weight applied.

Weights matter when one class has far more images than another, because without
them a model can score well by favouring the biggest class. If the imbalance ratio
is above 3, the cell tells you to report macro F1 rather than plain accuracy. Note
the ratio down.

---

## Stage 7 — Cells 5, 6 and 7: training

**Cell 5** defines both models and the evaluation function. The notes above it list
four faults in your old evaluation code that this fixes. Read them, because they
are likely viva questions.

**Cell 6** trains your own CNN. **Cell 7** trains MobileNetV2.

You will see lines like:

```
Epoch 4/30
43/43 ━━━━━━━━ 25s - accuracy: 0.7367 - val_accuracy: 0.8654
```

- `accuracy` is on images it is learning from
- `val_accuracy` is on images held back, and **that is the number that matters**

Training stops by itself when validation loss stops improving, so it may end well
before epoch 30. That is EarlyStopping working, not a fault.

Each cell finishes with a per-class table. **Screenshot both.**

MobileNetV2 should clearly beat your own CNN. That gap is your experimental
finding.

---

## Stage 8 — Cell 8: figures, tables and download

Run it. It draws three figures, prints two tables, saves the better model, and
downloads `training_output.zip`.

- **Figure 1** accuracy and loss curves
- **Figure 2** confusion matrices
- **Figure 3** model comparison, overall and per class

**How to read a confusion matrix.** Rows are the true class, columns are the
guess. The diagonal is correct. Find the largest off-diagonal number and note which
two classes it joins. One sentence about that in your discussion shows you examined
your own results instead of quoting a headline figure.

---

## Stage 9 — Keep your evidence

`training_output.zip` holds your figures, raw metrics and trained model. **Keep it
safe. It is your proof.**

Also keep, in one folder:

- the Cell 3 counts screenshot
- the Cell 3 leakage verification screenshot
- both per-class results tables

---

## Stage 10 — Writing the Experimental Modelling section

The marker said this section was your weakest. It failed because it described
nothing you had actually done. Here is the shape it should take. Fill the gaps
with your own numbers.

**10.1 Aim.** State plainly what the experiment tests. For example: whether
transfer learning outperforms a CNN trained from scratch on a small cotton leaf
dataset, and what effect grouping the data split has on the validity of the
result.

**10.2 The data problem you found.** Report that the dataset holds ___ files
built from only ___ original photographs, roughly ___ files per photograph.
Explain that a random file-level split allowed variants of one photograph into
both training and testing, so the earlier accuracy measured memorisation. Give
the overlap figure from Cell 7 and state that the corrected split reduced it to
zero.

**10.3 Method.** Give the split proportions, image size 224, batch size 32,
Adam optimiser, learning rate, and the augmentation applied on the fly during
training only. Say explicitly that validation and test images were never
augmented, and why.

**10.4 The two models.** Describe your CNN with its layer counts and parameter
total. Describe MobileNetV2 with its total and trainable parameter counts.
Explain that freezing the base keeps features learned from a much larger image
collection, which suits a small dataset.

**10.5 Results.** Insert the results table. Insert Figures 1, 2 and 3 with
numbers and captions, and refer to each in the text. Report accuracy and macro
F1 together, and explain that accuracy alone can hide a class the model always
gets wrong.

**10.6 Discussion.** Answer these in prose:

- Which model won, by how much, on which measure
- Why transfer learning helps when data is scarce
- Which class scored worst, which class it was confused with, and a plausible
  visual reason
- What the training curves show about overfitting, and which callback addressed it

**10.7 Limitations.** Be honest and specific. Only ___ original photographs per
class. The test set holds ___ photographs expanded by augmentation, so those
files are not independent samples and the accuracy is less precise than the file
count suggests. All images were captured under controlled conditions, so
performance on real field photographs is untested.

**10.8 Objective check.** Your objective set a target of 90 percent accuracy.
State the figure you actually reached and whether the objective was met, partly
met or not met. If it was not met, say so and explain why. A stated shortfall
with a reason scores far better than an unsupported claim of success, which is
exactly what went wrong last time.

---

## When something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| `No GPU` | Runtime is on CPU | Runtime, Change runtime type, T4 GPU, Save, then rerun Cell 1 |
| `KeyError: 'kaggle.json'` | File was renamed on download | Rename it to exactly `kaggle.json`, rerun Cell 3 |
| `403 Forbidden` | Dataset terms not accepted | Open the dataset page once in a browser, then rerun Cell 4 |
| `404 Not Found` | Slug is wrong | Recheck the part of the URL after `/datasets/` |
| `Could not find the expected class folders` | Folder names differ | Edit `EXPECTED` in Cell 5 to match the printed tree |
| `LEAKAGE PRESENT` | Photo groups crossed splits | Stop. Send me the filenames from Cell 6 |
| `NameError: name 'groups_per_class' is not defined` | A cell was skipped | Run cells from the top in order |
| Session disconnected | Tab closed or laptop asleep | Reconnect and run from Cell 1 again |
| Training accuracy stuck near 0.25 | Model is guessing | Tell me. Something is wrong with the labels |

---

## What to do after training

1. Tell me the numbers from Cell 6, Cell 7 and both results tables
2. I will help you turn them into the Experimental Modelling section
3. Only then worry about GitHub, the website and the ESP32 hardware

One stage at a time. Do not try to do everything in one sitting.
