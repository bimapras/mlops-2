"""
This is the trainer and tuner module
"""

import os

from typing import NamedTuple, Dict, Text, Any
import tensorflow as tf
import keras_tuner
from keras.utils.vis_utils import plot_model
import tensorflow_transform as tft
from keras_tuner.engine import base_tuner
from keras_tuner import RandomSearch

from transform_module import (
    CATEGORICAL_FEATURES,
    LABEL_KEY,
    NUMERICAL_FEATURES,
    transformed_feature,
)

TunerFnResult = NamedTuple('TunerFnResult',
        [('tuner', base_tuner.BaseTuner),
        ('fit_kwargs', Dict[Text, Any])]
    )


def get_hyperparameters() -> keras_tuner.HyperParameters:
    """Returns hyperparameters for building model"""
    hp = keras_tuner.HyperParameters()
    hp.Int('dense_1', 32, 256, step=32, default=32)
    hp.Int('dense_2', 32, 128, step=32, default=32)
    hp.Int('dense_3', 16, 64, step=16, default=16)
    hp.Float('dropout', 0.1, 0.5, step=0.1, default=0.2)
    hp.Choice('learning_rate', [1e-2, 1e-3], default=1e-3)
    return hp


def get_model(hp, show_summary=True):
    """
    This function defines a Keras model and returns the model as a
    Keras object.
    """

    input_features = []
    for key, dim in CATEGORICAL_FEATURES.items():
        input_features.append(
            tf.keras.Input(shape=(dim,), name=transformed_feature(key))
        )

    for feature in NUMERICAL_FEATURES:
        input_features.append(
            tf.keras.Input(shape=(1,), name=transformed_feature(feature))
        )

    concatenate = tf.keras.layers.concatenate(input_features)
    deep = tf.keras.layers.Dense(hp.get('dense_1'), activation="relu")(concatenate)
    deep = tf.keras.layers.Dense(hp.get('dense_2'), activation="relu")(deep)
    deep = tf.keras.layers.Dense(hp.get('dense_3'), activation="relu")(deep)
    deep = tf.keras.layers.Dropout(hp.get('dropout'))(deep)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid")(deep)

    model = tf.keras.models.Model(inputs=input_features, outputs=outputs)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=hp.get('learning_rate')),
        loss='binary_crossentropy',
        metrics=[tf.keras.metrics.BinaryAccuracy()]
    )

    if show_summary:
        model.summary()

    return model


def gzip_reader_fn(filenames):
    """Loads compressed data"""
    return tf.data.TFRecordDataset(filenames, compression_type='GZIP')


def get_serve_tf_examples_fn(model, tf_transform_output):
    """Returns a function that parses a serialized tf.Example."""

    model.tft_layer = tf_transform_output.transform_features_layer()

    @tf.function
    def serve_tf_examples_fn(serialized_tf_examples):
        """Returns the output to be used in the serving signature."""
        feature_spec = tf_transform_output.raw_feature_spec()
        feature_spec.pop(LABEL_KEY)
        parsed_features = tf.io.parse_example(
            serialized_tf_examples, feature_spec
        )

        transformed_features = model.tft_layer(parsed_features)

        outputs = model(transformed_features)
        return {"outputs": outputs}

    return serve_tf_examples_fn


def input_fn(file_pattern, tf_transform_output, batch_size=64):
    """Generates features and labels for tuning/training.
    Args:
        file_pattern: input tfrecord file pattern.
        tf_transform_output: A TFTransformOutput.
        batch_size: representing the number of consecutive elements of
        returned dataset to combine in a single batch
    Returns:
        A dataset that contains (features, indices) tuple where features
        is a dictionary of Tensors, and indices is a single Tensor of
        label indices.
    """
    transformed_feature_spec = (
        tf_transform_output.transformed_feature_spec().copy()
    )

    dataset = tf.data.experimental.make_batched_features_dataset(
        file_pattern=file_pattern,
        batch_size=batch_size,
        features=transformed_feature_spec,
        reader=gzip_reader_fn,
        label_key=transformed_feature(LABEL_KEY),
    )

    return dataset

def tuner_fn(fn_args):
    """
    Build the tuner using the KerasTuner API.
    Args:
        fn_args: Holds args as name/value pairs.
        - working_dir: working dir for tuning.
        - train_files: List of file paths containing training tf.Example data.
        - eval_files: List of file paths containing eval tf.Example data.
        - train_steps: number of train steps.
        - eval_steps: number of eval steps.
        - schema_path: optional schema of the input data.
        - transform_graph_path: optional transform graph produced by TFT.
    Returns:
        A namedtuple contains the following:
        - tuner: A BaseTuner that will be used for tuning.
        - fit_kwargs: Args to pass to tuner's run_trial function for fitting the
                        model , e.g., the training and validation dataset. Required
                        args depend on the above tuner's implementation.
    """

    # Define tuner
    tuner = RandomSearch(
        get_model,
        objective='val_binary_accuracy',
        max_trials=10,
        hyperparameters=get_hyperparameters(),
        directory=fn_args.working_dir,
        project_name='alzheimer_prediction'
    )

    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor='val_binary_accuracy',
        mode='max',
        verbose=1,
        patience=2,
    )

    tf_transform_output = tft.TFTransformOutput(fn_args.transform_graph_path)

    train_set = input_fn(fn_args.train_files, tf_transform_output, 64)
    eval_set = input_fn(fn_args.eval_files, tf_transform_output, 64)

    return TunerFnResult(
        tuner=tuner,
        fit_kwargs={
            'x': train_set,
            'validation_data': eval_set,
            'steps_per_epoch': fn_args.train_steps,
            'validation_steps': fn_args.eval_steps,
            'callbacks': [early_stop],
            'epochs': 5
        }
    )

def run_fn(fn_args):
    """Train the model based on given args.
    Args:
    fn_args: Holds args used to train the model as name/value pairs.
    """
    tf_transform_output = tft.TFTransformOutput(fn_args.transform_output)

    train_dataset = input_fn(fn_args.train_files, tf_transform_output, 64)
    eval_dataset = input_fn(fn_args.eval_files, tf_transform_output, 64)

    if fn_args.hyperparameters is not None:
        hp = keras_tuner.HyperParameters.from_config(
            fn_args.hyperparameters)
    else:
        hp = get_hyperparameters()

    model = get_model(hp)

    log_dir = os.path.join(os.path.dirname(fn_args.serving_model_dir), "logs")
    tensorboard_callback = tf.keras.callbacks.TensorBoard(
        log_dir=log_dir, update_freq="batch"
    )

    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor='val_binary_accuracy',
        mode='max',
        verbose=1,
        patience=3,
    )

    tf.keras.backend.clear_session()

    model.fit(
        train_dataset,
        steps_per_epoch=fn_args.train_steps,
        validation_data=eval_dataset,
        validation_steps=fn_args.eval_steps,
        callbacks=[tensorboard_callback, early_stop],
        epochs=10
    )

    signatures = {
        "serving_default": get_serve_tf_examples_fn(
            model, tf_transform_output
        ).get_concrete_function(
            tf.TensorSpec(shape=[None], dtype=tf.string, name="examples")
        ),
    }
    model.save(
        fn_args.serving_model_dir, save_format="tf", signatures=signatures
    )

    plot_model(
        model,
        to_file='images/model_plot.png',
        show_shapes=True,
        show_layer_names=True
    )
