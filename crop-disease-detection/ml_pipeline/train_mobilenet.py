"""
Trains the primary MobileNetV3Small classifier via transfer learning.

Expects a directory structure like:
    dataset/clean/
        tomato_early_blight/
        tomato_late_blight/
        potato_early_blight/
        potato_late_blight/
        healthy/
        ...

Class folder names MUST match keys in backend/app/data/diseases.json.

Outputs (written to backend/app/ml/weights/, matching config.py's paths):
    model.keras           - the trained model
    class_indices.json    - {"0": "tomato_early_blight", "1": "healthy", ...}

Usage:
    python train_mobilenet.py --dataset dataset/clean --epochs 30
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV3Small
from tensorflow.keras.preprocessing.image import ImageDataGenerator

IMAGE_SIZE = (224, 224)
BACKEND_WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "backend" / "app" / "ml" / "weights"


def build_model(num_classes: int) -> keras.Model:
    base_model = MobileNetV3Small(
        input_shape=(*IMAGE_SIZE, 3),
        include_top=False,
        weights="imagenet",
        pooling="avg",
    )
    base_model.trainable = False  # freeze for initial transfer-learning phase

    inputs = keras.Input(shape=(*IMAGE_SIZE, 3))
    x = base_model(inputs, training=False)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy", keras.metrics.Precision(name="precision"),
                  keras.metrics.Recall(name="recall")],
    )
    return model


def build_generators(dataset_dir: Path, batch_size: int):
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=20,
        width_shift_range=0.15,
        height_shift_range=0.15,
        zoom_range=0.15,
        horizontal_flip=True,
        brightness_range=[0.85, 1.15],
        validation_split=0.2,  # 80/20 train/val split from the same clean folder
        fill_mode="nearest",
    )

    train_gen = train_datagen.flow_from_directory(
        dataset_dir,
        target_size=IMAGE_SIZE,
        batch_size=batch_size,
        class_mode="categorical",
        subset="training",
        shuffle=True,
        seed=42,
    )
    val_gen = train_datagen.flow_from_directory(
        dataset_dir,
        target_size=IMAGE_SIZE,
        batch_size=batch_size,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
        seed=42,
    )
    return train_gen, val_gen


def evaluate_and_report(model: keras.Model, val_gen, class_names: list[str]) -> None:
    val_gen.reset()
    predictions = model.predict(val_gen, verbose=0)
    y_pred = predictions.argmax(axis=1)
    y_true = val_gen.classes

    print("\n--- Classification report (validation set) ---")
    print(classification_report(y_true, y_pred, target_names=class_names, zero_division=0))

    print("--- Confusion matrix (validation set) ---")
    print(confusion_matrix(y_true, y_pred))


def main(dataset_dir: Path, epochs: int, batch_size: int) -> None:
    BACKEND_WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    train_gen, val_gen = build_generators(dataset_dir, batch_size)
    class_names = sorted(train_gen.class_indices, key=lambda k: train_gen.class_indices[k])
    num_classes = len(class_names)
    print(f"Found {num_classes} classes: {class_names}")

    model = build_model(num_classes)
    model.summary()

    checkpoint_path = BACKEND_WEIGHTS_DIR / "model.keras"
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.2, patience=3, min_lr=1e-6
        ),
        keras.callbacks.ModelCheckpoint(
            str(checkpoint_path), monitor="val_accuracy", save_best_only=True
        ),
    ]

    model.fit(train_gen, validation_data=val_gen, epochs=epochs, callbacks=callbacks)

    # Ensure best checkpoint is what's actually on disk even if the final
    # epoch wasn't the best (ModelCheckpoint already handles this, but we
    # reload explicitly before evaluating to be certain).
    model = keras.models.load_model(checkpoint_path)

    evaluate_and_report(model, val_gen, class_names)

    class_indices_path = BACKEND_WEIGHTS_DIR / "class_indices.json"
    index_to_class = {str(i): name for i, name in enumerate(class_names)}
    with open(class_indices_path, "w", encoding="utf-8") as f:
        json.dump(index_to_class, f, indent=2)

    print(f"\nModel saved to:          {checkpoint_path}")
    print(f"Class indices saved to:  {class_indices_path}")
    print(
        "\nIMPORTANT: verify every key in class_indices.json exists in "
        "backend/app/data/diseases.json before serving predictions."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=Path("dataset/clean"), type=Path)
    parser.add_argument("--epochs", default=30, type=int)
    parser.add_argument("--batch-size", default=32, type=int)
    args = parser.parse_args()

    if not args.dataset.exists():
        raise SystemExit(f"Dataset path does not exist: {args.dataset}")

    main(args.dataset, args.epochs, args.batch_size)
