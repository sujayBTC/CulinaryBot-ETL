from app.db.database import get_database_session
from app.db.db_services import DBRecordService
from app.model.models import Recipe
from app.schemas.recipe import Recipe

async def fetch_recipe():
   async for db in get_database_session(): 
        response = DBRecordService.fetch_records(
            db=db,
            model=Recipe,
        )
        pass