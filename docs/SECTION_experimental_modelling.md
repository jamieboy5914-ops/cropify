# Experimental Modelling and Design Approach

Draft section for the dissertation. Written in APA 7th style since the existing
reference list follows that format. All figures come from the completed
ablation run.

**Verify every citation before submission.** These were written without web
access so each DOI needs checking against the live record. One reference for the
dataset has to come from the Kaggle page since the version number and the
authors are not recorded here.

---

## 6.1 Aim of the experimental work

Two questions drive this chapter. The first asks whether the way a dataset is
divided changes what a reported accuracy figure means while the second asks
whether a network starting from features learned on a large general image
collection beats a network trained from scratch on a cotton leaf dataset of
around two thousand photographs.

Both questions came out of a fault found at the earlier stage of this project.
An accuracy figure of 92 percent had been reported. No check had been made on
whether the test images were new to the model. Section 6.2 shows why that check
matters.

## 6.2 Dataset audit and the leakage problem

Auditing came before any training. Counting image files gives one number.
Counting the distinct photographs those files came from gives a second number
and the two diverge whenever a dataset has been padded with rotated or zoomed
copies saved as separate files.

The dataset used at interim stage held 2080 image files. Those files came from
160 photographs, 40 per class, each expanded into thirteen variants with names
such as `rotation_35.jpg` and `zoom_35.jpg`. Splitting those 2080 files at
random treated each variant as an unrelated image. A grouping check found all
156 test photographs present in the training set too. Every test image was a
transformed copy of a leaf the model had seen during training. An accuracy
measured that way reports how well a model recalls images it has seen. It does
not estimate performance on a new leaf. Kapoor and Narayanan (2023) trace the
same fault across 294 published papers in seventeen fields and find that leakage
inflates reported performance without leaving any trace in the results
themselves which is why the earlier figure could not be defended in the oral
examination.

SAR-CLD-2024 was chosen to replace it. The dataset ships two collections side by
side, one named Original Dataset and one named Augmented Dataset. The original
was used and the augmented copy was deleted before any file was read. Auditing
it returned 2137 image files from 2137 distinct photographs across seven classes
so this collection carries no offline augmentation and each file holds a
separate leaf. Table 6.1 gives the class counts.

**Table 6.1 Photographs per class in the original collection of SAR-CLD-2024**

| Class | Photographs | Share of dataset |
|---|---|---|
| Bacterial Blight | 250 | 11.7% |
| Curl Virus | 431 | 20.2% |
| Healthy Leaf | 257 | 12.0% |
| Herbicide Growth Damage | 280 | 13.1% |
| Leaf Hopper Jassids | 225 | 10.5% |
| Leaf Redding | 578 | 27.0% |
| Leaf Variegation | 116 | 5.4% |
| **Total** | **2137** | **100%** |

The largest class holds five times as many photographs as the smallest. That
ratio matters for how results are reported and Section 6.3 explains the
correction applied.

Hashing every file surfaced a second problem. Five photographs appear under two
different class labels as byte-identical files, for example `CV00019.jpg` in
Curl Virus and `HL00101.jpg` in Healthy Leaf. Neither label can be confirmed as
the correct one. This is a fault in the published dataset and not in the work
reported here and Section 6.7 states how it limits the findings.

## 6.3 Experimental design

Photographs were grouped before the split. Whole groups were then assigned to
one subset. Proportions were 65 percent for training, 15 percent for validation
and 20 percent for testing, applied within each class so the class balance holds
across all three subsets. A verification step counted how many photographs
appeared on both sides of the split. The count was zero for training against
validation and zero for training against testing.

Images were resized to 224 by 224 pixels, matching the figure stated in the
methodology. The earlier code used 256 and that mismatch would have reduced
accuracy once the model was placed behind the web application because the
application resizes to a different figure.

Augmentation was applied while images were fed to the model instead of being
saved to disk. Rotation reached 25 degrees, zoom 20 percent and shifts 15
percent. Shear, horizontal and vertical flips and brightness variation between
0.8 and 1.2 were used alongside these. Validation and test images received no
augmentation since performance has to be measured on the images as captured.

Class weights were set inverse to class frequency so a photograph from Leaf
Variegation carries five times the weight of one from Leaf Redding in the loss
and without that correction a model can reach a fair accuracy while ignoring the
smallest class. Sokolova and Lapalme (2009) show that accuracy and macro
averaged measures diverge as class sizes grow apart because accuracy alone hides
the performance of small classes which is the reason macro F1 is reported
alongside accuracy throughout this chapter.

Training used Adam at a learning rate of 0.001 with a batch size of 32 and a
maximum of 30 epochs. Two callbacks were attached. EarlyStopping watched
validation loss with patience of six epochs and restored the weights from the
best epoch so the saved model is not the overfitted final one. ReduceLROnPlateau
cut the learning rate by a factor of 0.3 after three epochs without improvement.
A fixed seed of 42 was set for the split and for weight initialisation.

## 6.4 Model architectures

The first architecture is the one built at interim stage. It was kept unchanged
so any difference between the two models can be attributed to architecture
alone. Five convolutional blocks run from 16 filters to 256 with max pooling
after each. A dense layer of 512 units with dropout at 0.5 sits before the
output and Srivastava et al. (2014) introduced that dropout to reduce co-
adaptation between units. Co-adaptation matters here because all 3,673,511
parameters are fitted from 1400 training photographs. Nothing in the network
starts from prior knowledge.

The second architecture uses MobileNetV2 as a frozen feature extractor, followed
by global average pooling, batch normalisation, a dense layer of 128 units and
dropout at 0.4. Sandler et al. (2018) designed MobileNetV2 with inverted
residual blocks and linear bottlenecks to cut parameter count while holding
accuracy and the weights used here come from training on ImageNet. Freezing the
base means 2,427,975 parameters are present while 167,431 are fitted. The
transfer model holds fewer total parameters than the network trained from
scratch and fits 22 times fewer of them.

Moyazzoma et al. (2021) reached 90.38 percent on five crops in Bangladesh using
MobileNetV2 as a feature extractor which suggests the approach suits small
agricultural datasets. Islam et al. (2023) took a different route on cotton by
fine tuning a full network instead of freezing a base. The disagreement between
those two studies concerns how much of the pretrained network to retrain and it
turns on dataset size since fine tuning needs more images to avoid destroying
the pretrained features. With 2137 photographs the frozen approach was chosen
for the work reported here.

## 6.5 Results

Four configurations were trained on the identical split. Each adds one change to
the row above it. Table 6.2 reports the outcome on the held-out test set of 433
photographs.

**Table 6.2 Effect of each change, added one at a time**

| Step | Change added | Epochs | Best validation accuracy | Test accuracy | Macro F1 | Gain in macro F1 |
|---|---|---|---|---|---|---|
| A | none | 18 | 0.7587 | 0.7298 | 0.6898 | - |
| B | on-the-fly augmentation | 30 | 0.7238 | 0.6905 | 0.6022 | -0.0876 |
| C | class weights | 30 | 0.8032 | 0.7829 | 0.7589 | +0.1567 |
| D | transfer learning | 21 | 0.9206 | 0.9307 | 0.9250 | +0.1661 |

Augmentation on its own lowered macro F1 by 0.0876. That result runs against the
expectation set out in Section 6.3 so it needs an explanation and not a
footnote.

Per-class recall locates the cause. Leaf Variegation holds 116 photographs and
24 of them sit in the test set. Its recall fell from 0.583 at step A to 0.125 at
step B, meaning the model found 3 of those 24. Leaf Redding holds 578
photographs and moved the other way, from 0.803 to 0.872. Augmentation widens
the variation inside each class because every image arrives rotated, shifted or
shifted in brightness and a class with 116 photographs cannot cover that widened
spread while a class with 578 can. The optimiser met a harder problem with the
same total loss to minimise so it moved capacity toward the classes that repaid
the effort.

Class weighting reversed the collapse. Leaf Variegation recall rose from 0.125
to 0.958 at step C and its F1 rose from 0.200 to 0.754. Macro F1 across all
seven classes gained 0.1567.

Transfer learning added a further 0.1661 which brings the total improvement from
step A to step D to 0.2352.

Two conclusions follow. Class weighting and transfer learning contributed
amounts that sit 0.0094 apart so neither change carries the result on its own.
Augmentation repaid nothing until weighting was in place beside it which means
the two changes interact and cannot be judged one at a time. Reporting
augmentation as a standalone improvement would have hidden that interaction.

Step D converged in fewer epochs. Early stopping halted it at epoch 21 while
restoring epoch 15, where step C ran the full 30 epochs and restored epoch 29.
Neither model overfitted since training accuracy of 0.9195 sat below validation
accuracy of 0.9206 in the transfer run.

Table 6.3 gives per-class F1 at every step.

**Table 6.3 Per-class F1 across the four steps**

| Class | Test photographs | A | B | C | D |
|---|---|---|---|---|---|
| Bacterial Blight | 51 | 0.571 | 0.487 | 0.610 | 0.845 |
| Curl Virus | 87 | 0.762 | 0.728 | 0.851 | 0.977 |
| Healthy Leaf | 52 | 0.667 | 0.607 | 0.674 | 0.917 |
| Herbicide Growth Damage | 56 | 0.923 | 0.889 | 0.927 | 0.982 |
| Leaf Hopper Jassids | 46 | 0.513 | 0.484 | 0.635 | 0.907 |
| Leaf Redding | 117 | 0.797 | 0.819 | 0.861 | 0.926 |
| Leaf Variegation | 24 | 0.596 | 0.200 | 0.754 | 0.920 |

Every class except Leaf Redding lost F1 at step B which matches the account
given above. Transfer learning then helped most where step C performed worst.
Leaf Hopper Jassids gained 0.272, Healthy Leaf gained 0.243 and Bacterial Blight
gained 0.235. Herbicide Growth Damage moved from 0.927 to 0.982 for a gain of
0.055 because it had less room left to gain. Pretrained edge and texture filters
supply discrimination that 1400 training photographs cannot produce from scratch
and that shortfall bites hardest on the classes with the least distinct
appearance.

## 6.6 Error analysis

Step D misclassified 30 of the 433 test photographs. Eleven of those 30 errors
involve one pair of classes swapping places. Six Bacterial Blight photographs
were labelled Leaf Redding and five Leaf Redding photographs were labelled
Bacterial Blight so this single pair accounts for 37 percent of all errors.

Bacterial blight lesions on cotton show reddish brown margins as tissue dies and
leaf reddening produces reddish discolouration across the blade so the two
conditions share the colour signature the model depends on. Separating them
needs lesion shape and boundary detail instead of colour distribution and at 224
by 224 pixels that detail is reduced.

The remaining errors spread across the other classes. Curl Virus reached 84
correct from 87, Healthy Leaf 50 from 52, Herbicide Growth Damage 54 from 56,
Leaf Hopper Jassids 44 from 46 and Leaf Variegation 23 from 24. Herbicide Growth
Damage reached precision of 1.000 so every prediction of that class was correct.

## 6.7 Limitations

Five constraints bound these findings.

The dataset holds 2137 photographs for seven classes. Zekiwos et al. (2021)
reported 96.4 percent on cotton using k-fold cross-validation, above the 93.07
percent reached here and part of that difference may come from cross-validation
using every photograph for testing across folds instead of holding one fifth
back. A single split was used here so the figures carry no confidence interval.

Leaf Variegation contributes 24 photographs to the test set so its F1 of 0.920
rests on 24 decisions. A change in two of those decisions moves the figure by
around 0.04.

The five ambiguous duplicate pairs identified in Section 6.2 remain in the data
used for these runs. They affect 10 files out of 2137. That is 0.5 percent of
the dataset and some of those files will have landed on opposite sides of the
split. Removing them and retraining would settle how much they matter.

Photographs in SAR-CLD-2024 were captured under controlled conditions at a
consistent 500 by 500 pixels. Khan et al. (2023) collected maize images in wet
and dry field conditions with background clutter and argued that controlled
datasets overstate field performance so the figures here should be read as an
upper bound and not as an expected result on a phone camera in a field.

No field images were captured for this project so the gap Khan et al. (2023)
identified remains open in this work.

Each configuration was trained once. Step B lost 0.0876 of macro F1 and the size
of that loss cannot be separated from run to run variation without repeated
seeds. The direction of the effect is supported by the per-class recall pattern
in Section 6.5 and not by the single figure alone.

## 6.8 Objectives against results

The objective set a target of 90 percent accuracy for the classification model.
Step D reached 93.07 percent accuracy with macro F1 of 0.9250. Those figures
come from 433 held-out photographs on a split verified to hold no shared
photographs. The objective is met and that verification is what separates this
figure from the 92 percent reported at interim stage.

---

## References for this section

**Check every entry against the live record before submission.** These were
written without web access and could contain errors.

Kapoor, S., & Narayanan, A. (2023). Leakage and the reproducibility crisis in
machine-learning-based science. *Patterns*, 4(9), 100804.
https://doi.org/10.1016/j.patter.2023.100804

Khan, F., Zafar, N., Tahir, M. N., Aqib, M., Waheed, H., & Haroon, Z. (2023). A
mobile-based system for maize plant leaf disease detection and classification
using deep learning. *Frontiers in Plant Science*, 14, 1079366.
https://doi.org/10.3389/fpls.2023.1079366

Moyazzoma, R., Hossain, M. A. A., Anuz, M. H., & Sattar, A. (2021). Transfer
learning approach for plant leaf disease detection using CNN with pre-trained
feature extraction method MobileNetV2. In *2021 2nd International Conference on
Robotics, Electrical and Signal Processing Techniques (ICREST)* (pp. 526-529).
IEEE. https://doi.org/10.1109/ICREST51555.2021.9331214

Sandler, M., Howard, A., Zhu, M., Zhmoginov, A., & Chen, L. C. (2018).
MobileNetV2. Inverted residuals and linear bottlenecks. In *Proceedings of the
IEEE Conference on Computer Vision and Pattern Recognition* (pp. 4510-4520).
https://doi.org/10.1109/CVPR.2018.00474

Sokolova, M., & Lapalme, G. (2009). A systematic analysis of performance measures
for classification tasks. *Information Processing and Management*, 45(4),
427-437. https://doi.org/10.1016/j.ipm.2009.03.002

Srivastava, N., Hinton, G., Krizhevsky, A., Sutskever, I., & Salakhutdinov, R.
(2014). Dropout. A simple way to prevent neural networks from overfitting.
*Journal of Machine Learning Research*, 15(1), 1929-1958.

**Still needed.** A citation for SAR-CLD-2024 itself. Take the authors, the year
and the version from the Kaggle page and check whether the uploader lists a
journal article for the dataset since dataset papers often appear in *Data in
Brief*.

---

## What to do with this draft

1. Paste Step B's accuracy and macro F1 into Table 6.2 and work out the two gain
   figures. Send them to me if you want the surrounding sentences adjusted since
   the claim about transfer learning being the largest single gain depends on
   Step B being smaller.
2. Insert Figures 1 to 4 where the tables sit, then number and caption each one
   and refer to each in the text.
3. Decide whether to remove the five ambiguous pairs and retrain. Section 6.7
   states the position taken if you leave them.
4. Verify all six citations, then add the dataset citation.
