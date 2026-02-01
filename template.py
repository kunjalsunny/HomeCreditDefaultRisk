import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.DEBUG)

project_name = 'HomeCreditDefaultRisk'


list_of_files = [
    # --- project / package ---
    f"{project_name}/__init__.py",
    f"{project_name}/logger.py",
    f"{project_name}/exception.py",

    f"{project_name}/src/__init__.py",

    f"{project_name}/src/components/__init__.py",
    f"{project_name}/src/components/data_ingestion.py",
    f"{project_name}/src/components/data_transformation.py",
    f"{project_name}/src/components/data_validation.py",
    f"{project_name}/src/components/model_trainer.py",
    f"{project_name}/src/components/model_evaluation.py",

    f"{project_name}/src/pipelines/__init__.py",
    f"{project_name}/src/pipelines/training_pipeline.py",
    f"{project_name}/src/pipelines/batch_prediction_pipeline.py",

    f"{project_name}/configs/config.yaml",
    f"{project_name}/config/schema.yaml",
    f"{project_name}/config/params.yaml",
    

]

for filepath in list_of_files:
    filepath = Path(filepath)

    filedir, filename = os.path.split(filepath)

    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
        logging.info(f"Creating directory: {filedir} for the file {filename}")

    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
        with open(filepath, "w") as f:
            pass
        logging.info(f"Creating empty file: {filepath}")
    else:
        logging.info(f"{filename} already exists")
