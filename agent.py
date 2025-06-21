import os
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, Agent
from google.adk.tools import FunctionTool, VertexAiSearchTool, google_search
from google.adk.runners import InMemoryRunner
# New import for listing data stores
from google.cloud import discoveryengine_v1alpha as discoveryengine
from pydantic import BaseModel, Field
from typing import List

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
MODEL = "gemini-2.5-flash"
# --- Architecture Overview ---
# This version simplifies the workflow by always searching all available data stores.
# It removes the need for an agent to select which stores to search.
#
# 1.  SearchCoordinatorAgent: Uses a single tool to list all available data stores
#     and immediately performs a search in each one, aggregating the results.
# 2.  AnalysisAgent: Reasons over the comprehensive, multi-source data.
# 3.  SummarizerAgent: Formats the final report.

class CategoryOutput(BaseModel):
    categories: List[str] = Field(description="The list of area of interest of the lawyer")

user_analyser_structured = Agent(
    name="UserAnalyser",
    model=MODEL,
    description="Analyzes user input to determine area interest of the lawyer.",
    instruction="""
You are an AI assistant designed to extract key information from professional biographies. Your task is to analyze the text about a lawyer and extract their primary area(s) of legal practice.

Return the answer as a JSON object with a key called "areas_of_interest" which contains a list of the identified specializations. and the data you should read is from {user_interest}

---
**EXAMPLE 1:**
**Text:** "Maria Rodriguez is a dedicated attorney with over 15 years of experience in helping families navigate the complexities of divorce, child custody, and adoption proceedings. She is a certified mediator and a strong advocate for her clients' rights."
**JSON Response:**
{
  "areas_of_interest": ["Family Law", "Divorce", "Child Custody", "Adoption", "Mediation"]
}
---
**EXAMPLE 2:**
**Text:** "John Chen heads the intellectual property division at his firm. He focuses on patent litigation, trademark registration, and copyright law, representing tech startups and established corporations."
**JSON Response:**
{
  "areas_of_interest": ["Intellectual Property", "Patent Litigation", "Trademark Law", "Copyright Law"]
}
---
**ACTUAL TASK:**
**Text:**{PASTE LAWYER'S BIO TEXT HERE}
**JSON Response:**
{
"area_of_interest":["category1", "category2"]
}
    """,
    output_schema=CategoryOutput
    )

# user_analyser 
user_analyser = LlmAgent(
    name="UserAnalyser",
    model=MODEL,
    description="Analyzes user input to determine area interest of the lawyer.",
    instruction="""
    Lawyer Profile Generator
    You are an expert legal researcher. Your task is to gather publicly available information about a specific lawyer, focusing on their areas of interest and client work.

    Given the lawyer's full name and email address, perform a comprehensive search to identify, use the google_search tool to find information about the lawyer's
    You might wanna focus on this website `https://www.linklaters.com/en/find-a-lawyer`:

    Areas of Interest/Specialization: What specific legal fields, industries, or types of cases does this lawyer focus on? Look for keywords like "practice areas," "specialties," "expertise," or "industries served."
    Client Work/Notable Cases: Identify any publicly disclosed information about clients they have represented or significant cases they have been involved in. This might include:
    Specific company names or types of organizations.
    Details about high-profile or landmark cases.
    Descriptions of the types of legal issues they commonly handle for clients.
    Important Considerations:

    Prioritize information from reputable sources such as law firm websites, legal directories (e.g., Chambers and Partners, Legal 500, Martindale-Hubbell), bar association profiles, and reputable legal news outlets.
    Be mindful of client confidentiality. Only provide information that is already in the public domain. Do not attempt to access private or restricted information.
    If you cannot find specific client names, generalize the types of clients or industries they serve if that information is available.
    If no information is found for a particular category, state that explicitly.
    Input:

    Lawyer's Name: [Insert Lawyer's Full Name Here]
    Lawyer's Email Address: [Insert Lawyer's Email Address Here]
    Output Format:

    Present the information clearly and concisely, using the following structure by storing the to state in the following fields under "user"
    * areas_of_interest: A list of specific areas of interest or specialization.
    * client_work: A list of notable clients or cases, or a description of typical client types or case categories.
    * general_descripton of the lawyer's practice if specific information is not found, e.g., "Corporate Law," "Intellectual Property," etc.
    Example Output:

    state["user"]["areas_of_interest"]: ["Corporate Law", "Intellectual Property", "Mergers and Acquisitions"]
    state["user"]["client_work"]: ["Represented XYZ Corporation in a high-profile merger", "Advised ABC Tech on patent litigation"]
    state["user']["general_description"]: "The lawyer specializes in corporate law, particularly in mergers and acquisitions, and has a strong focus on intellectual property issues."
    """,
    tools=[google_search],  # Include the search tool directly in the agent
    output_key="user"  # Specify the output keys for structured data
)

user_analyser_2 = LlmAgent(
    name="UserAnalyser",
    model=MODEL,
    description="Analyzes user input to determine area interest of the lawyer.",
    instruction="""
    Lawyer Profile Generator
    You are an expert legal researcher. Your task is to gather publicly available information about a specific lawyer, focusing on their areas of interest and client work.

    Given the lawyer's full name and email address, perform a comprehensive search to identify, use the google_search tool to find information about the lawyer's
    You might wanna focus on this website `https://www.linklaters.com/en/find-a-lawyer`:

    Areas of Interest/Specialization: What specific legal fields, industries, or types of cases does this lawyer focus on? Look for keywords like "practice areas," "specialties," "expertise," or "industries served."
    Client Work/Notable Cases: Identify any publicly disclosed information about clients they have represented or significant cases they have been involved in. This might include:
    Specific company names or types of organizations.
    Details about high-profile or landmark cases.
    Descriptions of the types of legal issues they commonly handle for clients.
    Important Considerations:

    Prioritize information from reputable sources such as law firm websites, legal directories (e.g., Chambers and Partners, Legal 500, Martindale-Hubbell), bar association profiles, and reputable legal news outlets.
    Be mindful of client confidentiality. Only provide information that is already in the public domain. Do not attempt to access private or restricted information.
    If you cannot find specific client names, generalize the types of clients or industries they serve if that information is available.
    If no information is found for a particular category, state that explicitly.
    Input:

    Lawyer's Name: [Insert Lawyer's Full Name Here]
    Lawyer's Email Address: [Insert Lawyer's Email Address Here]
    Output Format:

    Present the information clearly and concisely, using the following structure by storing the to state in the following fields under "user"
    * areas_of_interest: A list of specific areas of interest or specialization.
    * client_work: A list of notable clients or cases, or a description of typical client types or case categories.
    * general_descripton of the lawyer's practice if specific information is not found, e.g., "Corporate Law," "Intellectual Property," etc.
    Example Output:

    state["user"]["areas_of_interest"]: ["Corporate Law", "Intellectual Property", "Mergers and Acquisitions"]
    state["user"]["client_work"]: ["Represented XYZ Corporation in a high-profile merger", "Advised ABC Tech on patent litigation"]
    state["user']["general_description"]: "The lawyer specializes in corporate law, particularly in mergers and acquisitions, and has a strong focus on intellectual property issues."
    """,
    tools=[google_search],  # Include the search tool directly in the agent
    output_key="user_interest"  # Specify the output keys for structured data
)
category_agent = SequentialAgent(name="category", sub_agents=[user_analyser_2, user_analyser_structured])
news_query_agent = LlmAgent(
    name="NewsQueryAgent",
    description="Orchestrates the entire legal research workflow.",
    model=MODEL,
    tools=[google_search],  # Include the search tool directly in the root agent
    instruction="""
    You are an AI Legal Update Summarizer, designed to assist legal professionals by providing efficient and templated summaries of new legal and regulatory developments. 
    Your primary goal is to extract crucial information from lengthy documents and present it in an easily digestible format.
    At this step ignore all the information about a specific lawyer and what the user has provided you.

    Using your google_search tool, you will search for the latest updates using some of the following sources. You might use other sources as well, but make sure they are relevant to the legal field and provide updates on legal developments:
    Sources: FCA Publications, Bank of England Publications, Supreme Court Cases
    
    For each new and relevant development identified, you must generate a summary following this exact templeta in the state under "news":

    "news": {
        "legal_update_summary": "",  # A concise summary of the legal update.
        "new_items": [
            0: { 
                "title": "",  # The title of the legal update.
                "summary_statement": "",  # A brief overview of the development.
                "full_summary_key_points": [],  # A list of key points summarizing the development.
                "key_dates": [],  # A list of relevant dates associated with the development.
                "expected_impact": "",  # A categorized assessment of the impact of the development.
                "impact_flag": ""  # A flag indicating the impact level (Red, Amber, Green).
                "url": ""  # The URL of the source where the information was found.
            }
            , ...
        ],  # A list of new items found in the search results.
    }

    Prioritize Freshness: Always retrieve the newest information available on the specified sites.
    Accuracy is Paramount: Ensure all extracted dates, names, and factual details are accurate.
    Conciseness: Adhere strictly to word limits and sentence counts for each section.
    Relevance: Only summarize content that constitutes a "legal development" (e.g., new regulations, legislative changes, court judgments, significant policy updates). Filter out irrelevant press releases or events that do not represent a legal or regulatory change.
    Formatting: Present each summary using the exact template provided above, including bolding for section headers.
    """,
    output_key="news"  # Specify the output keys for structured data
    
)
    # FCA Publications: https://www.fca.org.uk/news
    # Bank of England Publications: https://www.bankofengland.co.uk/news/
    # Supreme Court Cases: https://www.supremecourt.uk/news/index.html (Note: You may need to navigate within this site to find specific judgment publications.)
    # For each new and relevant development identified, you must generate a summary following this exact templeta in the state under "news":


report_generator_agent = LlmAgent(
    name="ReportGeneratorAgent",
    model=MODEL, # Use an appropriate model
    description="Generates a personalized report for a lawyer based on their profile and relevant legal news updates.",
    instruction="""
    You are an expert report generator specializing in creating personalized legal insights for lawyers.
    Your task is to synthesize information about a lawyer's professional profile (areas of interest, client work)
    with recent, relevant legal and regulatory updates.

    You will receive two pieces of input from previous agents:
    1.  **Lawyer Profile (from UserAnalyser):** This will contain structured data about the lawyer
    2.  **Legal News Updates (from NewsQueryAgent):** This will contain a list of recent legal updates,


    Your goal is to generate a concise, professional, and highly relevant report for the lawyer.
    The report should:

    - present the results of the news that are relevant to the lawyer's profile,
    - dont explicitly mention the lawyes names and interests, but rather focus on the legal updates that are relevant to the lawyer's profile,
    - use the provided template to structure the report,
    - ensure that the report is clear, concise, and professional,

    Input will be provided via the 'state' object. Access lawyer profile data from `state["user"]` and
    news updates from `state["news"]`.

    Key Dates:
    [List all relevant dates associated with this development. Examples include:]

    Date of Publication/Judgment: [DD Month YYYY]
    Effective Date/In-force Date: [DD Month YYYY] (if applicable)
    Consultation Period End Date: [DD Month YYYY] (if applicable)
    Deadline for Submissions: [DD Month YYYY] (if applicable)
    Other Significant Dates: [DD Month YYYY] (e.g., next review, implementation phase)
    Expected Impact:
    [Provide an assessment of the likely impact of this development. Categorize the impact using a 'flag' system, and briefly explain why.]

    Red Flag (Significant Negative Impact/Urgent Action Required): [Brief explanation]
    Amber Flag (Moderate Impact/Requires Attention/Potential Future Impact): [Brief explanation]
    Green Flag (Minor or Positive Impact/No Immediate Action): [Brief explanation]
    Execution Instructions:

    Prioritize Freshness: Always retrieve the newest information available on the specified sites.
    Accuracy is Paramount: Ensure all extracted dates, names, and factual details are accurate.
    Conciseness: Adhere strictly to word limits and sentence counts for each section.
    Relevance: Only summarize content that constitutes a "legal development" (e.g., new regulations, legislative changes, court judgments, significant policy updates). Filter out irrelevant press releases or events that do not represent a legal or regulatory change.
    Formatting: Present each summary using the exact template provided above, including bolding for section headers.

    **Important:**
    - Focus on **relevance**. Only include news updates that genuinely align with the lawyer's profile.
    - If no specific lawyer name is available in `state["user"]`, use "Lawyer" in the report title.
    - The output for this agent should be the complete formatted report string.

    Output the final report in as the query result of the agent, so that it can be used in the next step.
    """

)

html_styler = LlmAgent(
    name="HtmlStyler",
    model=MODEL,
    description="Generates a styled HTML version of the report.",
    instruction="""
    You are an AI HTML Styler, designed to create a visually appealing HTML representation of a legal report.
    Your task is to take the report generated by the ReportGeneratorAgent and format it into a well-structured HTML document.

    Assume that this will be the email directly sent to the lawyer, so it should be professional and easy to read.
    
    The HTML should include:
    - A title section with the report title
    - A section for key dates
    - A section for expected impact with appropriate styling
    - A section for news updates with links to sources
    - Use CSS for styling to ensure the report is professional and easy to read

    Use the following color scheme for the report:
    - Background: #FFFFFF
    - Header: #3e00ff
    - Text: #000000
    - Links: #f29fe4

    Use the following font styles:
    - for everthing use "lexend"

    The input will be provided in the state under "report" key, and you should output the complete HTML string.
    The HTML should be stored in the state under "html_report" key.
    """,
    output_key="html_report",  # Specify the output key for the HTML report
)

research_team = ParallelAgent(
    name="ResearchTeam",
    sub_agents=[user_analyser, news_query_agent],
    description="A team of agents working together to analyze user input, query legal news"
)
    
# News filter agent

def send_email(subj:str, cont:str):
    print(subj)
    print(cont)

    """
    Sends an email with the report to the lawyer using SendGrid.
    Args:
        subj (str): The subject of the email.
        cont (str): The HTML content of the email.
    """

    message = Mail(
        from_email='devstar5741@gcplab.me',
        to_emails="mario.ale.gomez.andreu@gmail.com",
        subject=subj,
        html_content=cont
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        # sg.set_sendgrid_data_residency("eu")
        # uncomment the above line if you are sending mail using a regional EU subuser
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

email_sender_agent = LlmAgent(
    name="EmailSenderAgent",
    model=MODEL,
    description="Sends the generated report via email to the lawyer.",
    instruction="""
    You are an AI Email Sender, designed to send the generated report via email to the lawyer.
    Your task is to take the HTML report generated by the HtmlStyler agent and send it via email using the SendGrid API.

    The input will be provided in the state under "html_report" key, and you should output the email status.
    The email should be sent using the send_email function provided in this agent.

    The function `send_email` takes two parameters:
    - `subj`: The subject of the email.
    - `cont`: The HTML content of the email.

    """,
    tools=[FunctionTool(send_email)],  # Include the send_email function as a tool
    output_key="email_status"  # Specify the output key for the email status
)

root_agent = SequentialAgent(name="MyPipeline", sub_agents=[research_team, report_generator_agent, html_styler, email_sender_agent])
# root_agent = usl
