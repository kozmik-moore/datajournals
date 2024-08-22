from os import makedirs
from os.path import exists
from shutil import rmtree

from flask import current_app

from datajournals.base_methods import create_init_tables_function, create_init_tags_function
from datajournals.models.healthdb import HealthRecord, HealthDescriptorTag, HealthEmotionTag, HealthGlucoseRecord, \
    HealthCardioRecord, \
    HealthPainRecord, HealthWeightRecord, HealthNote, HealthAttachment

models = (HealthRecord,
          HealthDescriptorTag,
          HealthEmotionTag,
          HealthGlucoseRecord,
          HealthCardioRecord,
          HealthPainRecord,
          HealthWeightRecord,
          HealthNote,
          HealthAttachment
          )
table_names = ('health_record_descriptors',
               'health_record_emotions'
               )
init_health_tables = create_init_tables_function(models=models, table_names=table_names, pseudodb_name='healthdb')

tags_dict = {
    HealthDescriptorTag: (
        'sensation',
        'hospital visit',
        'allergies',
        'advice',
        'drugs',
        'recreational substance use',
        'quick record'
    ),
    HealthEmotionTag: (
        'happy',
        'sad',
        'angry',
        'upset',
        'anxious',
        'disappointed',
        'excited',
        'pleased'
    )
}

init_default_health_tags = create_init_tags_function(tags_dict=tags_dict)


def init_health_attachments_store(delete_files=False):
    """
    Create directory for health attachments, if it doesn't exist; empty it, if it does.
    USE WITH CAUTION.
    :return: None
    """
    attachments_path = current_app.config['HEALTH_ATTACHMENTS_DIR']
    if exists(attachments_path):
        if delete_files or \
                input('Delete files from health attachments folder? ').strip() in ['y', 'Y', 'yes', 'Yes', 'YES', '1']:
            rmtree(attachments_path)
            message = f'Deleting health attachments directory at {attachments_path}'
            current_app.logger.warning(message)

    else:
        message = f'Creating health attachments directory at {attachments_path}'
        current_app.logger.warning(message)
    makedirs(attachments_path)
