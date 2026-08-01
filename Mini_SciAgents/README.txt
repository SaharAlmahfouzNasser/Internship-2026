1. PREREQUISITES
Run this command in your terminal to install the necessary packages:

pip install google-genai pydantic networkx

2. SET ENVIRONMENT KEY (RUN EVERY TIME)
You must set your Gemini API key in your terminal before running the script.

For Windows (PowerShell):
$env:GEMINI_API_KEY="AIzaSyAfYiCUuw4ByVEd3UgX7EjA0dSG-VucnE8"

3. CONFIGURATION SWITCH
Open mini_sciagents.py and set the MOCK_MODE variable at the top:

MOCK_MODE = True  -> Tests the script code locally tonight without using any API tokens.

MOCK_MODE = False -> Connects to live Gemini servers tomorrow to generate real scientific text.

4. RUN THE SYSTEM
Execute the controller script from your terminal:

python mini_sciagents.py

5. EXPECTED DELIVERABLE
The system will run 3 concept pairs and automatically write your results data to a file in the same folder named:

sciagents_3_pair_evaluation.json