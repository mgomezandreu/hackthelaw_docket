import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from agent import root_agent, category_agent, research_team
from google.adk.runners import Runner 
from google.adk.sessions import InMemorySessionService
from google.genai import types # For creating message Content/Parts
from pydantic import BaseModel, Field
from typing import List
from groq import Groq
from google import genai
from google.genai import types
import wave

load_dotenv()
app = Flask(__name__)

class CategoryOutput(BaseModel):
    categories: List[str] = Field(description="The list of area of interest of the lawyer")

current_session_id = "session_search_all_001" 
# --- Session Management ---
# Key Concept: SessionService stores conversation history & state.
# InMemorySessionService is simple, non-persistent storage for this tutorial.
session_service = InMemorySessionService()
APPNAME = "thedocket"
# --- Run the Application ---
async def returning_everything(agent, initial_message):
# Create the specific session where the conversation will happen
    runner = Runner(agent=agent, app_name=APPNAME, session_service=session_service)
    session = await session_service.create_session(
        app_name=APPNAME,
        user_id="example_legal_analyst",
        session_id=current_session_id
    )
    print(session)

    # Instantiate the runner ONCE at the start of your application
    
    print("-" * 30)
    
    # Use a fixed session ID for this single execution flow.
    # This ensures the InMemoryRunner knows which session to work with.
    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=initial_message)])

    try:
        # We need to provide the project_id and the query to the search tool.
        async for event in runner.run_async(user_id=session.user_id, session_id=session.id, new_message=content):
            # You can uncomment the line below to see *all* events during execution
            # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

            # Key Concept: is_final_response() marks the concluding message for the turn.
            if event.is_final_response():
                print("-" * 30)
                print("--- Agent Workflow Complete ---")
                if event.content and event.content.parts:
                    # Assuming text response in the first part
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                    final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                # Add more checks here if needed (e.g., specific error codes)
                return(final_response_text)

                break # Stop processing events once the final response is found

    except Exception as e:
        print(f"\nAn error occurred during the agent workflow: {e}")
        return "failed", 404
        # Optionally, you might want to reset the runner or session state here
        # if you were running multiple sessions or had more complex error recovery.
# --- Run the Application ---
# Basic health check endpoint
@app.route('/')
def root():
    """
    A simple health check endpoint.
    """
    return "Service is up and running!"

@app.route('/categories', methods=['POST'])
async def categories_post():
    print(request.args)
    name = request.args.get("name")
    firm = request.args.get("firm")
    initial_message =  f"Tell me about lawyer {name} from {firm}"
    print(initial_message)
    result = await returning_everything(category_agent,initial_message)
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": """
    You are an AI assistant designed to extract key information from professional biographies. Your task is to analyze the text about a lawyer and extract their primary area(s) of legal practice. Return the answer as a JSON object with a key called 'areas_of_interest'. always respond with valid JSON objects that match this structure:

        {
        "areas_of_interest": ["string"]
        }
Your response should ONLY contain the JSON object and nothing else.
""",
            },
            {
                "role":"user",
                "content":result
            },
        ],
        response_format={"type": "json_object"}
    )

    return (response.choices[0].message.content)


@app.route('/report', methods=['POST'])
async def report_post():
    name = request.args.get("name")
    firm = request.args.get("firm")

    initial_message =  f"Tell me about lawyer {name} from {firm} and what current event could effect her current practice area from reputable news source "
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        print("Please set the GOOGLE_CLOUD_PROJECT environment variable.")
    else:
        return await returning_everything(root_agent, initial_message)
        # Instantiate the runner ONCE at the start of your application
@app.route('/podcast', methods=['POST'])
async def podcast():
    # name = request.args.get("name")
    # firm = request.args.get("firm")
    name = "leanne banfield"
    firm = "linkslater"

    initial_message =  f"Tell me about lawyer {name} from {firm} and what current event could effect her current practice area from reputable news source "
    sources = await returning_everything(research_team, initial_message)
    print(sources)
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": """
                    **Persona:** You are Alex, Leanne's assistant

                    **Task:** Write a complete podcast script for a 5-minute episode (650-750 words). The script must be based **exclusively** on the information provided in the "Data Sources" section below. Do not introduce any external information or facts.

                    **Script Structure and Formatting:**
                    Your script must follow this format precisely:
                    1. Hi {target individual's name}
                    2. here is your digest for the day
                    3. please choose and select the data source where it is good and valuable and then produce it as a personal assitant podcast format
                    
                    
                    ---
                    **Data Sources:**
                    user input
                    ---

                    **Podcast Script that is suitable for reading by speech to text api**
                """,
            },
            {
                "role":"user",
                "content":sources
            },
        ],

    )
    result = response.choices[0].message.content
    # Set up the wave file to save the output:
    # def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    #     with wave.open(filename, "wb") as wf:
    #         wf.setnchannels(channels)
    #         wf.setsampwidth(sample_width)
    #         wf.setframerate(rate)
    #         wf.writeframes(pcm)

    # client = genai.Client(api_key=
    # "AIzaSyDfT0QYWewRwMJ50ZdxatsOfa6txaqRvZM")
    # a = "4"
    # prompt = f"TTS the following text as a podcast:{result}"
    # response = client.models.generate_content(
    # model="gemini-2.5-flash-preview-tts",
    # contents=prompt,
    # config=types.GenerateContentConfig(
    #     response_modalities=["AUDIO"],
    #     speech_config=types.SpeechConfig(
    #         voice_config=types.VoiceConfig(
    #             prebuilt_voice_config=types.PrebuiltVoiceConfig(
    #             voice_name='Kore',
    #             )
    #         )
    #     ),
    # )
    # )

    # data = response.candidates[0].content.parts[0].inline_data.data

    # file_name='out.wav'
    # wave_file(file_name, data) # Saves the file to current directory
    # # Open a file for writing. If the file doesn't exist, it will be created.
    
        
    return result


    

if __name__ == '__main__':
    # Cloud Run will set the PORT environment variable.
    # For local development, you can set a default.
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
