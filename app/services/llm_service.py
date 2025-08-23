# Standard library imports
import asyncio
import logging
from typing import Any, Tuple

# Third-party imports
import pandas as pd
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSequence
from langchain_google_genai.chat_models import (
    ChatGoogleGenerativeAI,
    ChatGoogleGenerativeAIError,
)

# Local application imports
from app.config import settings
from app.exceptions.errors import (
    LLMAPIKeyError,
    LLMInitializationError,
    LLMProcessingError,
    LLMPromptError,
    LLMServiceError,
    FileProcessingError,
    EmptyFileError,
)
from app.services.file_service import process_csv_to_chunks
from app.services.prompt import (
    ProductCatalogSummarizationModel,
    ProductCatalogSummarizationPrompt,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)


class LLMService:
    """
    A service class to handle all interactions with the Large Language Model (LLM).

    This class is responsible for:
    - Initializing the LLM (e.g., Google Gemini) and required components.
    - Validating API keys and configuration.
    - Defining and running LLM processing pipelines (LCEL).
    - Implementing robust retry logic for API calls.
    - Orchestrating the summarization of product catalogs from files.
    """

    def __init__(self) -> None:
        """
        Initializes the LLMService, setting up the chat model, prompts, and parsers.
        Raises exceptions if the configuration is invalid or initialization fails.
        """
        # --- 1. Initialize Chat Model ---
        try:
            # Validate that the API key is present in the environment settings.
            if not settings.GEMINI_API_KEY:
                raise LLMAPIKeyError("GEMINI_API_KEY is not set in environment variables")

            # Validate that the API key is not a placeholder value.
            if settings.GEMINI_API_KEY == "your_gemini_api_key_here":
                raise LLMAPIKeyError(
                    "GEMINI_API_KEY is not properly configured. Please set your actual API key"
                )

            # Initialize the Google Generative AI chat model with the specified settings.
            self.chat_model = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7,
                api_key=settings.GEMINI_API_KEY,
            )
            logger.info("ChatGoogleGenerativeAI model initialized successfully")

        except ChatGoogleGenerativeAIError as e:
            logger.error(f"Failed to initialize Google Generative AI model: {str(e)}")
            raise LLMInitializationError(f"Google Generative AI initialization failed: {str(e)}")
        except LLMAPIKeyError:
            raise  # Re-raise our custom API key exception to be handled globally.
        except Exception as e:
            logger.error(f"Unexpected error during LLM initialization: {str(e)}")
            raise LLMInitializationError(f"Failed to initialize LLM service: {str(e)}")

        # --- 2. Initialize Prompt and Parser ---
        try:
            # Set up the prompt template for summarization.
            self.prompt = ProductCatalogSummarizationPrompt().get_prompt()
            # Set up the output parser to structure the LLM's response into a Pydantic model.
            self.output_parser = PydanticOutputParser(
                pydantic_object=ProductCatalogSummarizationModel
            )
            logger.info("Prompt and output parser initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize prompt or output parser: {str(e)}")
            raise LLMPromptError(f"Failed to initialize prompt/parser components: {str(e)}")

    async def lcel_pipeline(
        self, role: str, text: str, csv_data: str, error_context: str
    ) -> ProductCatalogSummarizationModel:
        """
        Defines and executes the core LangChain Expression Language (LCEL) pipeline.

        Args:
            role: The role for the AI assistant (e.g., "fashion retail assistant").
            text: The column headers of the product data.
            csv_data: A chunk of CSV data representing product rows.
            error_context: Context from previous failed attempts, used for self-correction.

        Returns:
            The structured output from the LLM as a Pydantic model.

        Raises:
            LLMProcessingError: If the LLM API call fails.
            LLMServiceError: For any other unexpected errors during pipeline execution.
        """
        try:
            # Define the sequence of operations: prompt -> model -> parser.
            runnable = RunnableSequence(
                self.prompt | self.chat_model | self.output_parser
            )

            # Asynchronously invoke the pipeline with the provided input.
            result = await runnable.ainvoke(
                {
                    "role": role,
                    "text": text,
                    "csv_data": csv_data,
                    "error_context": error_context,
                }
            )
            logger.info("LLM processing completed successfully for a chunk.")
            return result

        except ChatGoogleGenerativeAIError as e:
            logger.error(f"Google Generative AI API error: {str(e)}")
            raise LLMProcessingError(f"LLM API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error in LLM pipeline: {str(e)}")
            raise LLMServiceError(f"LLM processing failed: {str(e)}")

    async def run_with_retry(
        self, input_data: dict, attempts: int = 3
    ) -> ProductCatalogSummarizationModel:
        """
        A wrapper that executes the LLM pipeline with a retry mechanism.

        This function attempts to call the LLM up to a specified number of times.
        If a call fails, it waits with exponential backoff and provides the error
        as context to the next attempt, enabling the LLM to self-correct.

        Args:
            input_data: The dictionary of inputs for the `lcel_pipeline`.
            attempts: The maximum number of retry attempts.

        Returns:
            The result from the `lcel_pipeline` upon success.

        Raises:
            LLMProcessingError: If all retry attempts fail.
        """
        error_context = ""
        for attempt in range(1, attempts + 1):
            try:
                # Add the current error context to the input for the next attempt.
                modified_input = {**input_data, "error_context": error_context}
                return await self.lcel_pipeline(**modified_input)
            except Exception as e:
                logger.error(f"LLM pipeline attempt {attempt}/{attempts} failed: {str(e)}")
                # If this was the last attempt, raise a final exception.
                if attempt == attempts:
                    raise LLMProcessingError(f"LLM failed after {attempts} attempts: {str(e)}")
                
                # Build the error context for the next retry to help the model recover.
                error_context = f"Attempt {attempt} failed with error: {str(e)}.\nPlease review the input and provide the output in the correct format."
                
                # Wait before the next retry using exponential backoff (1s, 2s, 4s...).
                await asyncio.sleep(2 ** (attempt - 1))

    async def summarize_product_catalog(self, role: str, file_path: str) -> Any:
        """
        Orchestrates the end-to-end process of summarizing a product catalog from a file.

        Args:
            role: The role for the AI assistant.
            file_path: The path to the CSV file to be summarized.

        Returns:
            A pandas DataFrame containing the summarized product information.
        """
        part2 = ""  # Holds the remainder of a chunk to prepend to the next one.
        summarized_data = pd.DataFrame()

        try:
            # Step 1: Read the file and split it into manageable chunks.
            columns, chunks = process_csv_to_chunks(file_path, chunk_size=20000)

            if not chunks:
                raise EmptyFileError("No data chunks were created. The file might be empty or invalid.")

            # Step 2: Iterate over each chunk and process it with the LLM.
            length_of_chunks = len(chunks)
            for chunk_index, chunk_content in enumerate(chunks):
                # Ensure chunks are split cleanly at line breaks to not cut off a row.
                part1, part2 = process_chunk(chunk=part2 + chunk_content)

                logger.info(f"Processing chunk {chunk_index + 1}/{length_of_chunks}")
                logger.debug(f"Chunk content: {part1[:100]}...")

                if not part1.strip():
                    logger.warning(f"Skipping empty or whitespace-only chunk {chunk_index + 1}.")
                    continue

                # Step 3: Process the chunk using the retry mechanism.
                try:
                    result = await self.run_with_retry(
                        input_data={"role": role, "text": columns, "csv_data": part1}
                    )
                    # Convert the Pydantic model result to a DataFrame.
                    chunk_df = pd.DataFrame(result.model_dump())
                    # Concatenate the chunk's results with the main DataFrame.
                    summarized_data = pd.concat([summarized_data, chunk_df], ignore_index=True)
                except LLMProcessingError as e:
                    logger.error(f"Chunk {chunk_index + 1} failed after all retries: {e}")
                    # Continue to the next chunk instead of stopping the entire process.
                    continue

            logger.info("All chunks processed successfully.")
            return summarized_data

        except FileNotFoundError:
            logger.error(f"File not found at path: {file_path}")
            raise FileProcessingError(f"File not found: {file_path}")
        except EmptyFileError:
            logger.warning(f"File processed but no data chunks were generated: {file_path}")
            raise  # Re-raise to be handled by the global error handler.
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing file {file_path}: {str(e)}")
            raise FileProcessingError(f"Failed to process product catalog: {str(e)}")


def process_chunk(chunk: str) -> Tuple[str, str]:
    """
    Splits a chunk of text at the last newline to avoid cutting off a CSV row.

    Args:
        chunk: The input text chunk.

    Returns:
        A tuple containing the processable part of the chunk and the remainder.
    """
    split_pos = chunk.rfind("\n")
    if split_pos != -1:
        # Everything before the last newline is a complete set of rows.
        part1 = chunk[:split_pos]
        # The remainder will be prepended to the next chunk.
        part2 = chunk[split_pos + 1 :]
    else:
        # If no newline is found, process the whole chunk.
        part1 = chunk
        part2 = ""
    return part1, part2


async def summarize(filepath: str) -> Any:
    """
    A convenience function to easily instantiate and run the summarization service.

    Args:
        filepath: The path to the product catalog file.

    Returns:
        The summarized data as a pandas DataFrame.
    """
    llm_service = LLMService()
    summary = await llm_service.summarize_product_catalog(
        "product catalog summarizer", filepath
    )
    return summary