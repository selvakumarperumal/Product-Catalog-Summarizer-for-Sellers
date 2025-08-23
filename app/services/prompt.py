from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate

)
from pydantic import BaseModel, Field
from typing import List


class ProductCatalogSummarizationModel(BaseModel):
    """Model for summarizing product catalog information"""
    row_id : List[int] = Field(..., description="Unique identifier for the product row")
    Summary: List[str] = Field(..., description="List of summaries for each product")
    
class ProductCatalogSummarizationPrompt:
    """Prompt template for summarizing product catalog information"""
    
    def __init__(self) -> None:

        self.system_message = SystemMessagePromptTemplate.from_template(
            """
            You are a {role} for summarizing product catalog information.
            """
        )

        self.human_message = HumanMessagePromptTemplate.from_template(
            """
            Summarize the following List of product catalog information, where i provided data column name rows separated by new line.
            Each row represents a product and its features.
            your task is to summarize the product catalog information based on the provided features. Don't replicate the input text in the output.
            if particular features are missing, then just summarize the available features without throwing an error or returning empty values.
            input:
            column names(Features): 
            {text}
            row values(Values): 
            {csv_data}

            output should be in the format:
            {{
                row_id: [product 1 row_id, product 2 row_id, ...],
                Summary: [Product 1 summary, Product 2 summary, ...]
            }}

            {error_context}
            """
        )

    def get_prompt(self) -> ChatPromptTemplate:
        """Returns the complete prompt template"""
        return ChatPromptTemplate.from_messages(
            [
                self.system_message,
                self.human_message
            ]
        )