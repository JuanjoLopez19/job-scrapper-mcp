import asyncio
import json
import os
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict, List, Optional

import nest_asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

# Import logger from utils
from shared.utils import logger, save_output

nest_asyncio.apply()

# Load environment variables
load_dotenv()


class MCPOpenAIClient:
    """Client for interacting with OpenAI models using MCP tools."""

    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize the OpenAI MCP client.

        Args:
            model: The OpenAI model to use.
        """
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai_client = AsyncOpenAI()
        self.model = model
        self.stdio: Optional[Any] = None
        self.write: Optional[Any] = None
        logger.info(f"Initialized MCPOpenAIClient with model: {model}")

    async def connect_to_server(self, server_script_path: str = "server.py"):
        """Connect to an MCP server.

        Args:
            server_script_path: Path to the server script.
        """
        logger.info(f"Connecting to MCP server: {server_script_path}")
        
        # Server configuration
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
        )

        # Connect to the server
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        # Initialize the connection
        await self.session.initialize()

        # List available tools
        tools_result = await self.session.list_tools()
        logger.info("Connected to server with tools:")
        for tool in tools_result.tools:
            logger.info(f"  - {tool.name}: {tool.description}")

    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from the MCP server in OpenAI format.

        Returns:
            A list of tools in OpenAI format.
        """
        tools_result = await self.session.list_tools()
        logger.debug(f"Retrieved {len(tools_result.tools)} tools from MCP server")
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools_result.tools
        ]

    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available MCP tools.

        Args:
            query: The user query.

        Returns:
            The response from OpenAI.
        """
        logger.info(f"Processing query with MCP tools: {query[:50]}...")
        
        # Get available tools
        tools = await self.get_mcp_tools()

        # Initial OpenAI API call
        logger.debug("Making initial OpenAI API call")
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto",
        )

        # Get assistant's response
        assistant_message = response.choices[0].message

        # Initialize conversation with user query and assistant response
        messages = [
            {"role": "user", "content": query},
            assistant_message,
        ]

        # Handle tool calls if present
        if assistant_message.tool_calls:
            logger.info(f"Found {len(assistant_message.tool_calls)} tool calls to process")
            # Process each tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                logger.info(f"Executing tool call: {tool_name}")
                # Execute tool call
                try:
                    result = await self.session.call_tool(
                        tool_name,
                        arguments=json.loads(tool_call.function.arguments),
                    )
                    logger.debug(f"Tool {tool_name} executed successfully")

                    # Add tool response to conversation
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result.content[0].text,
                        }
                    )
                except Exception as e:
                    error_msg = f"Error executing tool {tool_name}: {str(e)}"
                    logger.error(error_msg)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": error_msg,
                        }
                    )

            # Get final response from OpenAI with tool results
            logger.debug("Getting final response from OpenAI with tool results")
            final_response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="none",  # Don't allow more tool calls
            )

            logger.info("Generated final response with tool results")
            return final_response.choices[0].message.content

        # No tool calls, just return the direct response
        logger.info("No tool calls needed, returning direct response")
        return assistant_message.content
        
    async def direct_chat_query(self, messages: List[Dict[str, str]]) -> str:
        """Send messages directly to the OpenAI API without using tools.
        
        Args:
            messages: The conversation messages.
            
        Returns:
            The response from OpenAI.
        """
        logger.info(f"Making direct chat query with {len(messages)} messages")
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            logger.debug("Direct chat query completed successfully")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in direct chat query: {str(e)}")
            raise

    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up client resources")
        await self.exit_stack.aclose()
        logger.debug("Client resources cleaned up successfully")


def read_cv_file() -> str:
    """Read the user's CV from the file."""
    cv_path = Path("user_data/cv.txt")
    logger.info(f"Reading CV file from {cv_path}")
    
    try:
        if cv_path.exists():
            with open(cv_path, "r", encoding="utf-8") as f:
                content = f.read()
                logger.info(f"CV file read successfully ({len(content)} characters)")
                return content
        else:
            logger.warning(f"CV file not found at {cv_path}")
            return "CV file not found at user_data/cv.txt"
    except Exception as e:
        logger.error(f"Error reading CV file: {str(e)}")
        return f"Error reading CV file: {str(e)}"


async def job_application_assistant():
    """Flujo completo del asistente para aplicaciones de empleo."""
    logger.info("Starting job application assistant workflow")
    client = MCPOpenAIClient()
    
    # Paso 1: Obtener URL de la oferta de empleo del usuario
    job_url = input("\nIntroduce la URL de la oferta de empleo: ")
    logger.info(f"User provided job URL: {job_url}")
    
    # Paso 2: Extraer detalles del empleo usando job_offer_scrapper.py
    logger.info("STEP 1: Extracting job details")
    print("\n--- PASO 1: EXTRAYENDO DETALLES DE LA OFERTA DE EMPLEO ---")
    await client.connect_to_server("job_offer_scrapper.py")
    query = f"Busca esta oferta de empleo: {job_url}\nPor favor, extrae la descripción completa del trabajo, requisitos, responsabilidades y cualquier información sobre beneficios y cultura de la empresa."
    
    logger.info("Querying job details from URL")
    job_details_response = await client.process_query(query)
    logger.info("Job details extracted successfully")
    
    print("\nDetalles de la oferta de empleo:")
    print(job_details_response)
    
    # Extraer el nombre de la empresa de la respuesta
    logger.info("Extracting company name from job details")
    company_name_query = f"""
    Basándote en los detalles de la oferta de empleo a continuación, ¿cuál es el nombre de la empresa que ofrece esta posición? Devuelve solo el nombre de la empresa.
    
    Detalles de la oferta de empleo:
    {job_details_response}
    """
    company_name = await client.direct_chat_query([{"role": "user", "content": company_name_query}])
    logger.info(f"Extracted company name: {company_name}")
    print(f"\nEmpresa: {company_name}")
    
    # Paso 3: Investigar la empresa usando internet_search_tool.py
    logger.info("STEP 2: Researching company information")
    print("\n--- PASO 2: INVESTIGANDO LA EMPRESA ---")
    await client.connect_to_server("mcp_tools/internet_search_tool.py")
    search_query = f"""
    Háblame sobre la empresa {company_name}, sus principales actividades, y cómo se relaciona con la oferta de empleo que he encontrado. Proporciona un resumen de su misión, visión y valores.
    Además, incluye información sobre la organización, cultura y cualquier otro dato relevante que pueda ayudarme a entender mejor la empresa.
    """
    
    logger.info(f"Searching for information about company: {company_name}")
    company_report = await client.process_query(search_query)
    logger.info("Company research completed successfully")
    
    print("\nInformación de la empresa:")
    print(company_report)
    
    # Guardar el informe de la empresa en un archivo
    logger.info("Saving company report to file")
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    try:
        save_output("company_report.txt", company_report)
        logger.info("Company report saved successfully")
    except Exception as e:
        logger.error(f"Failed to save company report: {str(e)}")
    
    print("\nInforme de la empresa guardado en outputs/company_report.txt")

    # Paso 4: Generar carta de presentación usando los detalles del empleo y el CV
    logger.info("STEP 3: Generating cover letter")
    print("\n--- PASO 3: GENERANDO CARTA DE PRESENTACIÓN ---")
    cv_content = read_cv_file()
    
    cover_letter_instructions = f"""
    Crea una carta de presentación personalizada para el trabajo descrito a continuación. Usa la información de mi CV y adapta la carta específicamente a esta posición y empresa.
    
    ## Detalles de la oferta de empleo:
    {job_details_response}
        
    ## Mi CV:
    {cv_content}
    
    La carta de presentación debe:
    1. Ser profesional y atractiva
    2. Resaltar mis habilidades y experiencias relevantes
    3. Explicar por qué soy un buen candidato para esta posición
    4. Mostrar entusiasmo por el puesto y la empresa
    5. Usar un formato formal de carta de negocios
    """
    
    logger.info("Generating personalized cover letter")
    cover_letter = await client.direct_chat_query([{"role": "user", "content": cover_letter_instructions}])
    logger.info("Cover letter generated successfully")
    
    print("\nCarta de presentación:")
    print(cover_letter)
    
    # Guardar la carta de presentación en un archivo
    logger.info("Saving cover letter to file")
    try:
        save_output("cover_letter.txt", cover_letter)
        logger.info("Cover letter saved successfully")
    except Exception as e:
        logger.error(f"Failed to save cover letter: {str(e)}")
    
    print("\nCarta de presentación guardada en outputs/cover_letter.txt")
    
    # Paso 5: Generar posibles preguntas de entrevista
    logger.info("STEP 4: Generating interview questions")
    print("\n--- PASO 4: GENERANDO PREGUNTAS DE ENTREVISTA ---")
    interview_query = f"""
    Basándote en la descripción del trabajo y mi CV, genera 10 posibles preguntas de entrevista que podría enfrentar y explica por qué cada pregunta es relevante considerando mi experiencia y los requisitos del trabajo.
    
    ## Detalles de la oferta de empleo:
    {job_details_response}
    
    ## Mi CV:
    {cv_content}
    
    Para cada pregunta, proporciona:
    1. La pregunta en sí
    2. Por qué el entrevistador podría hacer esta pregunta
    3. Una breve guía sobre cómo podría responderla
    """
    
    logger.info("Generating potential interview questions")
    interview_questions = await client.direct_chat_query([{"role": "user", "content": interview_query}])
    logger.info("Interview questions generated successfully")
    
    print("\nPosibles preguntas de entrevista:")
    print(interview_questions)
    
    # Guardar las preguntas de entrevista en un archivo
    logger.info("Saving interview questions to file")
    try:
        save_output("interview_questions.txt", interview_questions)
        logger.info("Interview questions saved successfully")
    except Exception as e:
        logger.error(f"Failed to save interview questions: {str(e)}")
    
    print("\nPreguntas de entrevista guardadas en outputs/interview_questions.txt")
    
    # Paso 6: Proporcionar un resumen del paquete de aplicación
    logger.info("Job application package completed")
    print("\n--- PAQUETE DE APLICACIÓN COMPLETO ---")
    print("\nTodos los materiales han sido generados y guardados en el directorio outputs.")
    
    await client.cleanup()
    logger.info("Job application assistant workflow completed successfully")


if __name__ == "__main__":
    logger.info("Starting application")
    asyncio.run(job_application_assistant())
