from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from data_pipelines.llm.model import llm
from data_pipelines.llm.state_manager import State
from langgraph.types import Command

class RecipeKeywords(BaseModel):
    keywords: list[str]

def recipe_llm_process(state: State):
    recipe = state["recipe"]
    current_recipe_index = state.get("current_recipe_index", 0)
    

    prompt1 = """
        Your expert in find a keyword from the data.
        
        Your going to do alalyse the data and find out the what are the keyword you can figerout
        
        step:
            1.you have to analyse the data and find the keywords like this dish for breakfast, it's non-veg dish...
            2.don't add duplicate's and don't add same meaning keywords
            3.if you find out any new keyword is not in the existing_keywords then only add in the list otherwise skip it.
            
        input:
            sample keyword : ["breakfast", "non-veg", "veg", "diabetes"]
        
        output:
            sample output: ["breakfast", "non-veg", "veg", "diabetes",....]
            
        existing_keywords = {existing_keywords}
    """
    
    
    structured_llm = llm.with_structured_output(RecipeKeywords)

    response = structured_llm.invoke(
        [
            SystemMessage(content=prompt1),
            HumanMessage(content=recipe),   
        ]
    )
    
    print("llm response====>", response)

    
    # result = response.get("keywords", [])
    result = response.keywords


    return Command(
        update ={
            "processed_data" : result,
            "current_chunk_index": current_recipe_index+1
        },
        goto="chunk_orchestrator"
    )
