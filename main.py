import os 
from agent import root_agent
import asyncio
from google.adk.runners import Runner 
from google.adk.sessions import InMemorySessionService
from google.genai import types # For creating message Content/Parts
current_session_id = "session_search_all_001" 
# --- Session Management ---
# Key Concept: SessionService stores conversation history & state.
# InMemorySessionService is simple, non-persistent storage for this tutorial.
session_service = InMemorySessionService()
APPNAME = "thedocket"
# --- Run the Application ---
async def returning_everything(agent, message):
# Create the specific session where the conversation will happen
    runner = Runner(agent=agent, app_name=APPNAME, session_service=session_service)
    session = await session_service.create_session(
        app_name=APPNAME,
        user_id="example_legal_analyst",
        session_id=current_session_id
    )
    print(session)

    # Instantiate the runner ONCE at the start of your application
    
    # "Tell me about lawyer Maryam Adamji from linklaters and what current event could effect her current practice area from reputable news source "
    
    print("-" * 30)
    
    # Use a fixed session ID for this single execution flow.
    # This ensures the InMemoryRunner knows which session to work with.
    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=message)])

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
                print(final_response_text)

                break # Stop processing events once the final response is found

    except Exception as e:
        print(f"\nAn error occurred during the agent workflow: {e}")
        # Optionally, you might want to reset the runner or session state here
        # if you were running multiple sessions or had more complex error recovery.

if __name__ == "__main__":
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        print("Please set the GOOGLE_CLOUD_PROJECT environment variable.")
    else:
        asyncio.run(returning_everything(root_agent, ))