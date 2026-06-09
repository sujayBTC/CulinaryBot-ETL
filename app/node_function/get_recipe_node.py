import httpx
from logger import logger

def get_recipe_node(state):
    
    url = "http://localhost:8000"
    
    recipe = httpx.get(
        url=url
        )
    
    print("recipe===>",recipe)
    
    logger.info(f"fetch recipe {recipe.status_code}")
    
    return state
    