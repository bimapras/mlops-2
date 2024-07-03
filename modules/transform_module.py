"""
This is the transform module
"""
import tensorflow as tf
import tensorflow_transform as tft

CATEGORICAL_FEATURES = {
    'Gender' : 2,
    'Ethnicity' : 4,
    'EducationLevel' : 4,
    'Smoking' : 2,
    'FamilyHistoryAlzheimers' : 2,
    'CardiovascularDisease' : 2,
    'Diabetes' : 2,
    'Depression' : 2,
    'HeadInjury' : 2,
    'Hypertension' : 2,
    'MemoryComplaints' : 2,
    'BehavioralProblems' : 2,
    'Confusion' : 2,
    'Disorientation' : 2,
    'PersonalityChanges' : 2,
    'DifficultyCompletingTasks' : 2,
    'Forgetfulness' : 2
}

NUMERICAL_FEATURES = {
    'Age',
    'BMI',
    'AlcoholConsumption',
    'PhysicalActivity',
    'DietQuality',
    'SleepQuality',
    'SystolicBP',
    'DiastolicBP',
    'CholesterolTotal',
    'CholesterolLDL',
    'CholesterolHDL',
    'CholesterolTriglycerides',
    'MMSE',
    'FunctionalAssessment',
    'ADL'
}

LABEL_KEY = 'Diagnosis'

def transformed_feature(key):
    '''Rename transformed features'''
    return key + '_xf'

def preprocessing_fn(inputs):
    '''
    Preprocess input features into transformed features
    
    Args:
        inputs: map from feature keys to raw  features.
        
    Return:
        outputs: map from feature keys to transformed features.
    '''
    outputs = {}
    for feature, num_labels in CATEGORICAL_FEATURES.items():
        one_hot = tf.one_hot(inputs[feature], depth=num_labels)
        outputs[transformed_feature(feature)] = tf.reshape(one_hot, [-1, num_labels])

    for feature in NUMERICAL_FEATURES:
        outputs[transformed_feature(feature)] = tft.scale_to_0_1(inputs[feature])

    outputs[transformed_feature(LABEL_KEY)] =  tf.cast(inputs[LABEL_KEY], tf.int64)

    return outputs
