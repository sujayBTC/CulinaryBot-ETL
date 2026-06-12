from data_pipelines.tasks.keyword_pipeline import keyword_pipeline
from data_pipelines.tasks.recipe_ingest import recipe_ingest

recipe_ingest.delay()
print("Triggered recipe Ingest =======================================>")

keyword_pipeline.delay()
print("Keyword Pipeline Ingest =======================================>")
