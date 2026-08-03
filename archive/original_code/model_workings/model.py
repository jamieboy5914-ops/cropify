import os
import cv2
import shutil
from sklearn.model_selection import train_test_split

def splitting_Data(dataset_root, root, test_size=0.2, validation_size=0.2):
    classes = os.listdir(dataset_root)
    print(classes)
    
    # Create directories for train, validation, and test data
    train_root = os.path.join(root, "train")
    validation_root = os.path.join(root, "validation")
    test_root = os.path.join(root, "test")
    
    for dir_path in [train_root, validation_root, test_root]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    for class_name in classes:
        class_path = os.path.join(dataset_root, class_name)
        image_files = [file for file in os.listdir(class_path) if cv2.imread(os.path.join(class_path, file)) is not None]
        
        # Split the data into training and testing sets
        train_files, test_files = train_test_split(image_files, test_size=test_size, random_state=42)
        train_files, val_files = train_test_split(train_files, test_size=validation_size, random_state=42)
        
        
        train_class_dir = os.path.join(train_root, class_name)
        validation_class_dir = os.path.join(validation_root, class_name)
        test_class_dir = os.path.join(test_root, class_name)
        
        for dir_path in [train_class_dir, validation_class_dir, test_class_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        for file in train_files:
            shutil.copy(os.path.join(class_path, file), os.path.join(train_class_dir, file))
        for file in val_files:
            shutil.copy(os.path.join(class_path, file), os.path.join(validation_class_dir, file))
        for file in test_files:
            shutil.copy(os.path.join(class_path, file), os.path.join(test_class_dir, file))
    
    print(f"Data has been successfully split into Train, Validation, and Test: {root}")

    
dataset_root=r"Dataset\NEW_DATA"
root="Dataset\Final Dataset Split"
if not os.path.exists(root):
    os.makedirs(root)
splitting_Data(dataset_root, root, test_size=0.2, validation_size=0.2)

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
from tensorflow.keras.callbacks import ReduceLROnPlateau

# Define paths to the datasets
train_dir = r"D:\JUPYTER_NEW DATA\NEW_DATA\SPLIT\train"
validation_dir = r"D:\JUPYTER_NEW DATA\NEW_DATA\SPLIT\validation"
test_dir = r"D:\JUPYTER_NEW DATA\NEW_DATA\SPLIT\test"

# Set parameters
img_width, img_height = 256, 256
input_shape = (img_width, img_height, 3)
batch_size = 32
epochs = 10
# Define data generators
train_datagen = ImageDataGenerator(
    rescale=1./255,
    shear_range=0.2,
    zoom_range=0.2,
    rotation_range=30,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True,
    vertical_flip=True
)
validation_test_datagen = ImageDataGenerator(rescale=1./255)

train_generator = train_datagen.flow_from_directory(train_dir, target_size=(img_width, img_height),
                                                    batch_size=batch_size, class_mode='categorical',
                                                    shuffle=True)

validation_generator = validation_test_datagen.flow_from_directory(validation_dir, target_size=(img_width, img_height),
                                                                  batch_size=batch_size, class_mode='categorical')


model = Sequential([
    Conv2D(16, (3, 3), activation='relu', input_shape=(img_height, img_width, 3)),
    MaxPooling2D(2, 2),

    Conv2D(32, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),

    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),

    Conv2D(128, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),

    Conv2D(256, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),

    Flatten(),

    Dense(512, activation='relu'),
    Dropout(0.5),
    Dense(4, activation='softmax')
])

model.summary()

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=1e-6)
history = model.fit(train_generator, steps_per_epoch=max(1, train_generator.samples // batch_size),
                    epochs=epochs, validation_data=validation_generator,
                    validation_steps=max(1, validation_generator.samples // batch_size),
                    callbacks=[reduce_lr])

# # Save the class indices to use for later predictions
# class_indices = train_generator.class_indices
# index_to_class = {v: k for k, v in class_indices.items()}

# # Evaluate on the test set
# test_generator = validation_test_datagen.flow_from_directory(test_dir, target_size=(img_width, img_height),
#                                                              batch_size=batch_size, class_mode='categorical', shuffle=False)

# # Make sure we predict on all images
# steps = test_generator.samples // batch_size + (test_generator.samples % batch_size > 0)
# predictions = model.predict(test_generator, steps=steps)

# # Convert predictions to class names
# predicted_classes_indices = np.argmax(predictions, axis=1)
# predicted_classes_names = [index_to_class[idx] for idx in predicted_classes_indices]

# # Output the predictions for each test image
# for i in range(len(predicted_classes_names)):
#     # Get the file path for the current index
#     file_path = test_generator.filepaths[i % len(test_generator.filepaths)]
#     print(f"Image: {file_path.split('/')[-1]} - Class: {predicted_classes_names[i]}")

# # Print the test accuracy
# test_loss, test_accuracy = model.evaluate(test_generator, steps=test_generator.samples // batch_size)
# print(f"Test Accuracy: {test_accuracy}")

class_indices = train_generator.class_indices
index_to_class = {v: k for k, v in class_indices.items()}

test_generator = validation_test_datagen.flow_from_directory(test_dir, target_size=(img_width, img_height),
                                                             batch_size=batch_size, class_mode='categorical', shuffle=False)

steps = test_generator.samples // batch_size + (test_generator.samples % batch_size > 0)
predictions = model.predict(test_generator, steps=steps)
predicted_classes_indices = np.argmax(predictions, axis=1)
predicted_classes_names = [index_to_class[idx] for idx in predicted_classes_indices]


for i in range(len(predicted_classes_names)):
    file_path = test_generator.filepaths[i % len(test_generator.filepaths)]
    print(f"Image: {file_path.split('/')[-1]} - Class: {predicted_classes_names[i]}")

test_loss, test_accuracy = model.evaluate(test_generator, steps=test_generator.samples // batch_size)
print(f"Test Accuracy: {test_accuracy}")

for i, prediction in enumerate(predictions):
    print(f"Image {i}:")
    for class_index, conf in enumerate(prediction):
        class_name = index_to_class[class_index] 
        print(f"    {class_name}: {conf*100:.2f}%")
    print("\n")

from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

true_classes = test_generator.classes

cm = confusion_matrix(true_classes, predicted_classes_indices)

class_names = [index_to_class[i] for i in range(len(index_to_class))]

plt.figure(figsize=(10, 3))
sns.heatmap(cm, annot=True, fmt='5', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
plt.xlabel('Predicted labels')
plt.ylabel('True labels')
plt.title('Confusion Matrix')
plt.show()



plt.plot(history.history['accuracy'],color='red',label='train')
plt.plot(history.history['val_accuracy'],color='blue',label='validation')
plt.title('MODEL ACCURACY')
plt.legend()
plt.show()
plt.plot(history.history['loss'],color='red',label='train')
plt.plot(history.history['val_loss'],color='blue',label='validation')
plt.title('MODEL LOSSES')
plt.legend()
plt.show()

model.save('basemodel.h5')