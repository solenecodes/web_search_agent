import json
import os
import random

import requests
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request

load_dotenv()

app = Flask(__name__)

# Global state
questions = []
current_q_idx = 0
score = 0
agent = None
project_client = None

# AI-102 topics for deep certification questions
AI102_TOPICS = [
    "Azure OpenAI Service SDK authentication methods quotas and TPM limits",
    "Azure AI Vision Custom Vision model training limits and SDK Python integration",
    "Azure Cognitive Search indexing limits skillsets and Python SDK",
    "Azure Bot Service channels configuration quotas and SDK integration",
    "Azure AI Language CLU intent recognition limits and best practices",
    "Azure AI Document Intelligence prebuilt layout model specifications",
    "Azure AI Foundry Prompt Flow SDK agent orchestration and limits",
    "Azure Content Safety text moderation API limits and SDK Python",
    "Azure Speech Service real-time transcription quotas and SDK",
    "Azure Translator Service character limits and custom models"
]

def query_mcp_docs(topic):
    """
    Query Microsoft Learn documentation via MCP-like endpoint
    In production, this would connect to actual Microsoft Learn MCP server
    """
    # Simulated MCP call - in production, use proper MCP protocol
    try:
        # For demo: search Microsoft Learn docs API
        search_url = f"https://learn.microsoft.com/api/search?search={requests.utils.quote(topic)}&locale=en-us"
        headers = {"Accept": "application/json"}
        resp = requests.get(search_url, headers=headers, timeout=5)

        if resp.ok:
            results = resp.json().get("results", [])[:3]
            docs_summary = "\n".join([f"- {r.get('title', '')}: {r.get('description', '')[:200]}"
                                     for r in results if r.get('title')])
            return docs_summary if docs_summary else "No specific docs found."
        return "MCP search unavailable - using agent knowledge."
    except Exception as e:
        return f"MCP unavailable - using agent knowledge. ({str(e)[:50]})"

def init_azure_agent():
    """Initialize Azure AI Agent with MCP tool integration"""
    global agent, project_client

    try:
        # Azure AI Project Client setup
        credential = DefaultAzureCredential()
        connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
        endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")

        if connection_string:
            project_client = AIProjectClient.from_connection_string(
                credential=credential,
                conn_str=connection_string
            )
        elif endpoint:
            # Use endpoint-based initialization
            project_client = AIProjectClient(
                endpoint=endpoint,
                credential=credential
            )
        else:
            print("⚠️  No Azure AI credentials found in .env")
            print("📋 App will use fallback mode with sample questions")
            print("💡 To enable AI agent: Add AZURE_AI_PROJECT_ENDPOINT or AZURE_AI_PROJECT_CONNECTION_STRING to .env")
            return False

        # Define MCP tool for querying Microsoft Learn docs
        mcp_tool = FunctionTool(
            name="query_microsoft_learn",
            description="Query Microsoft Learn documentation for accurate AI-102 certification information including SDK specs, limits, quotas, and best practices",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The AI-102 topic to search in Microsoft Learn docs"
                    }
                },
                "required": ["topic"]
            }
        )

        # Create agent with tools
        agent = project_client.agents.create_agent(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"),
            name="ai102-quiz-generator",
            instructions="""You are an expert AI-102 certification quiz generator.

Your role:
1. Generate challenging, exam-level questions on Azure AI services
2. Focus on: SDK implementation (Python/C#), quotas/limits, specs, edge cases, best practices
3. Use the query_microsoft_learn tool to fetch current documentation
4. Create varied question types: multiple-choice (4 options A-D), true/false, short answer
5. Ensure questions are SPECIFIC with real values (e.g., "What is the default TPM limit for GPT-3.5-turbo?")
6. Always provide detailed explanations with references

Question format (JSON array):
[{
  "type": "multi|tf|short",
  "question": "Detailed question text",
  "options": ["A) option", "B) option", "C) option", "D) option"],  // for multi-choice only
  "correct": "B) correct answer text",  // exact match required
  "explanation": "Why this is correct, with specifics"
}]

CRITICAL: Generate NEW random questions each time. Never repeat. Focus on deep technical details.""",
            tools=[mcp_tool.definitions[0]]
        )

        print(f"✅ Azure AI Agent initialized: {agent.id}")
        return True

    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        print("📝 Make sure your .env has proper Azure AI credentials")
        return False

def generate_questions_with_agent(num_questions, topic=None):
    """Generate quiz questions using Azure AI Agent with MCP"""
    global agent, project_client

    if not agent:
        if not init_azure_agent():
            # Return fallback questions if agent fails
            return generate_fallback_questions(num_questions)

    try:
        # Select random topic if not specified
        selected_topic = topic if topic else random.choice(AI102_TOPICS)

        # Query MCP docs first
        docs_context = query_mcp_docs(selected_topic)

        # Create thread
        thread = project_client.agents.create_thread()

        # Create message with context
        prompt = f"""Generate exactly {num_questions} NEW random AI-102 certification questions on this topic:
"{selected_topic}"

Context from Microsoft Learn:
{docs_context}

Requirements:
- Mix of types: multiple-choice (4 options), true/false, short answer
- Deep technical: SDK code examples, specific limits (e.g., "1000 TPM"), quotas, edge cases
- Each question must be exam-level difficulty
- Return ONLY valid JSON array, no markdown formatting

Format:
[{{"type": "multi", "question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct": "B) ...", "explanation": "..."}},
 {{"type": "tf", "question": "...", "correct": "true", "explanation": "..."}},
 {{"type": "short", "question": "...", "correct": "exact answer", "explanation": "..."}}]"""

        message = project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=prompt
        )

        # Run the agent
        run = project_client.agents.create_run(
            thread_id=thread.id,
            assistant_id=agent.id
        )

        # Poll for completion
        while run.status in ["queued", "in_progress", "requires_action"]:
            import time
            time.sleep(1)
            run = project_client.agents.get_run(thread_id=thread.id, run_id=run.id)

            # Handle tool calls if needed
            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for tool_call in tool_calls:
                    if tool_call.function.name == "query_microsoft_learn":
                        args = json.loads(tool_call.function.arguments)
                        result = query_mcp_docs(args.get("topic", ""))
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": result
                        })

                if tool_outputs:
                    run = project_client.agents.submit_tool_outputs_to_run(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

        if run.status == "completed":
            # Get messages
            messages = project_client.agents.list_messages(thread_id=thread.id)

            # Extract assistant's response
            for msg in messages.data:
                if msg.role == "assistant":
                    content = msg.content[0].text.value

                    # Parse JSON (remove markdown if present)
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif content.startswith("```"):
                        content = content.split("```")[1].split("```")[0].strip()

                    questions = json.loads(content)
                    print(f"✅ Generated {len(questions)} questions via agent")
                    return questions

        print("⚠️ Agent run failed, using fallback")
        return generate_fallback_questions(num_questions)

    except Exception as e:
        print(f"❌ Question generation error: {e}")
        return generate_fallback_questions(num_questions)

def generate_fallback_questions(num_questions):
    """Enhanced fallback questions with diverse AI-102 topics"""
    question_pool = [
        # Azure OpenAI
        {
            "type": "multi",
            "question": "What is the default token-per-minute (TPM) limit for Azure OpenAI GPT-3.5-turbo in Standard deployment?",
            "options": ["A) 1,000 TPM", "B) 10,000 TPM", "C) 120,000 TPM", "D) 240,000 TPM"],
            "correct": "C) 120,000 TPM",
            "explanation": "Azure OpenAI Standard deployment for GPT-3.5-turbo has a default quota of 120K tokens per minute."
        },
        {
            "type": "multi",
            "question": "Which Python package is used to interact with Azure OpenAI Service?",
            "options": ["A) azure-ai-openai", "B) openai", "C) azure-openai-sdk", "D) azureopenai"],
            "correct": "B) openai",
            "explanation": "The 'openai' package is used with Azure OpenAI by configuring azure_endpoint and api_version parameters."
        },
        # Custom Vision
        {
            "type": "tf",
            "question": "Azure Custom Vision supports training models with less than 5 images per tag.",
            "correct": "false",
            "explanation": "False. Azure Custom Vision requires a minimum of 5 images per tag for model training to ensure adequate learning."
        },
        {
            "type": "short",
            "question": "What is the maximum number of tags allowed per project in Azure Custom Vision Free tier?",
            "correct": "2",
            "explanation": "The Free tier allows 2 projects maximum. Standard tier supports more."
        },
        # Cognitive Search
        {
            "type": "short",
            "question": "In Azure Cognitive Search, what is the maximum number of indexes allowed in a Basic tier?",
            "correct": "15",
            "explanation": "Basic tier allows up to 15 indexes. Standard tier allows 50, while Free tier allows 3."
        },
        {
            "type": "multi",
            "question": "Which skillset in Azure Cognitive Search extracts key phrases from text?",
            "options": ["A) EntityRecognitionSkill", "B) KeyPhraseExtractionSkill", "C) LanguageDetectionSkill", "D) SentimentSkill"],
            "correct": "B) KeyPhraseExtractionSkill",
            "explanation": "KeyPhraseExtractionSkill identifies and extracts key phrases from text content during indexing."
        },
        # Document Intelligence
        {
            "type": "tf",
            "question": "Azure AI Document Intelligence prebuilt invoice model can extract line items from invoices.",
            "correct": "true",
            "explanation": "True. The prebuilt invoice model extracts invoice fields including line items, totals, and vendor information."
        },
        {
            "type": "multi",
            "question": "What is the maximum file size for Azure Document Intelligence API?",
            "options": ["A) 5 MB", "B) 50 MB", "C) 500 MB", "D) 5 GB"],
            "correct": "C) 500 MB",
            "explanation": "Azure Document Intelligence supports files up to 500 MB for PDF and image files."
        },
        # Bot Service
        {
            "type": "short",
            "question": "Which protocol does Azure Bot Service use for communication?",
            "correct": "HTTP",
            "explanation": "Azure Bot Service uses HTTP/HTTPS for the Bot Framework Protocol communication."
        },
        {
            "type": "tf",
            "question": "Azure Bot Service supports deployment to Microsoft Teams channel without additional configuration.",
            "correct": "true",
            "explanation": "True. Microsoft Teams is a supported channel that can be enabled directly in Azure portal."
        },
        # Language Service
        {
            "type": "multi",
            "question": "In Azure AI Language, what is the maximum number of characters per document for sentiment analysis?",
            "options": ["A) 1,000", "B) 5,120", "C) 10,000", "D) 125,000"],
            "correct": "B) 5,120",
            "explanation": "Azure AI Language Service has a limit of 5,120 characters per document for sentiment analysis."
        },
        {
            "type": "short",
            "question": "What is the acronym for the Azure service that handles conversational language understanding?",
            "correct": "CLU",
            "explanation": "CLU stands for Conversational Language Understanding, part of Azure AI Language."
        },
        # Speech Service
        {
            "type": "tf",
            "question": "Azure Speech Service batch transcription supports audio files up to 24 hours in length.",
            "correct": "true",
            "explanation": "True. Batch transcription can process audio files up to 24 hours long."
        },
        {
            "type": "multi",
            "question": "Which audio format is recommended for best Speech-to-Text accuracy in Azure?",
            "options": ["A) MP3 128kbps", "B) WAV 16kHz 16-bit", "C) AAC 44.1kHz", "D) FLAC 48kHz"],
            "correct": "B) WAV 16kHz 16-bit",
            "explanation": "WAV format at 16kHz sample rate with 16-bit depth is optimal for speech recognition accuracy."
        },
        # Content Safety
        {
            "type": "multi",
            "question": "Azure Content Safety API returns severity scores on what scale?",
            "options": ["A) 0-10", "B) 0-100", "C) 0-6", "D) 1-5"],
            "correct": "C) 0-6",
            "explanation": "Azure Content Safety returns severity scores from 0 (safe) to 6 (high severity) for each category."
        },
        # Translator
        {
            "type": "short",
            "question": "How many characters can be translated in a single request to Azure Translator?",
            "correct": "50000",
            "explanation": "Azure Translator allows up to 50,000 characters per request across all text elements."
        }
    ]

    # Randomly select questions without replacement
    selected = random.sample(question_pool, min(num_questions, len(question_pool)))

    # If more questions requested than available, repeat randomly
    while len(selected) < num_questions:
        selected.append(random.choice(question_pool))

    return selected[:num_questions]

# ============ FLASK ROUTES ============

@app.route("/", methods=["GET", "POST"])
def home():
    global questions, current_q_idx, score

    if request.method == "POST":
        num = int(request.form.get("num_questions", 5))
        num = max(1, min(20, num))  # Clamp to 1-20
        topic = request.form.get("topic", "").strip()

        # Generate questions
        questions = generate_questions_with_agent(num, topic if topic else None)
        current_q_idx = 0
        score = 0

        return quiz()

    # Show home page
    topics_options = "".join([f'<option value="{t}">{t}</option>' for t in AI102_TOPICS[:5]])
    return render_template_string(HTML_HOME, topics=topics_options)

@app.route("/quiz")
def quiz():
    global current_q_idx, questions

    if not questions or current_q_idx >= len(questions):
        return '<script>alert("No quiz loaded!"); window.location.href="/";</script>'

    q = questions[current_q_idx]
    return render_template_string(HTML_QUIZ, question=q, idx=current_q_idx+1, total=len(questions))

@app.route("/answer", methods=["POST"])
def answer():
    global current_q_idx, score, questions

    user_ans = request.json.get("answer", "").strip()
    q = questions[current_q_idx]

    # Check if correct
    correct_ans = q.get("correct", "").strip()
    is_correct = (user_ans.lower() == correct_ans.lower())

    if is_correct:
        score += 1

    current_q_idx += 1
    done = current_q_idx >= len(questions)

    return jsonify({
        "correct": is_correct,
        "correct_answer": correct_ans,
        "explanation": q.get("explanation", "No explanation available."),
        "score": score,
        "total": len(questions),
        "done": done
    })

# ============ HTML TEMPLATES ============

HTML_HOME = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-102 Quiz Agent - Matrix Mode</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: #000;
            color: #00ff00;
            font-family: 'Courier New', Courier, monospace;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }

        /* Matrix rain effect background */
        #matrix-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            opacity: 0.3;
        }

        .container {
            position: relative;
            z-index: 1;
            max-width: 600px;
            width: 100%;
            background: rgba(0, 0, 0, 0.9);
            border: 2px solid #0078D4;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 0 30px rgba(0, 120, 212, 0.5);
        }

        h1 {
            color: #0078D4;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2em;
            text-shadow: 0 0 10px #00ff00;
        }

        .subtitle {
            text-align: center;
            color: #00ff00;
            margin-bottom: 30px;
            font-size: 0.9em;
        }

        label {
            display: block;
            margin: 20px 0 8px 0;
            color: #00ff00;
            font-size: 1.1em;
        }

        input, select {
            width: 100%;
            padding: 12px;
            background: #001122;
            border: 1px solid #0078D4;
            color: #00ff00;
            font-family: 'Courier New', Courier, monospace;
            font-size: 1em;
            border-radius: 5px;
        }

        input:focus, select:focus {
            outline: none;
            border-color: #00ff00;
            box-shadow: 0 0 10px rgba(0, 255, 0, 0.3);
        }

        button {
            width: 100%;
            padding: 15px;
            margin-top: 30px;
            background: #0078D4;
            color: #fff;
            border: none;
            font-family: 'Courier New', Courier, monospace;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            border-radius: 5px;
            transition: all 0.3s;
        }

        button:hover {
            background: #005a9e;
            box-shadow: 0 0 20px rgba(0, 120, 212, 0.8);
            transform: translateY(-2px);
        }

        .info {
            margin-top: 20px;
            padding: 15px;
            background: rgba(0, 120, 212, 0.1);
            border-left: 3px solid #0078D4;
            color: #00ff00;
            font-size: 0.9em;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <canvas id="matrix-canvas"></canvas>

    <div class="container">
        <h1>🤖 AI-102 Quiz Agent</h1>
        <p class="subtitle">Azure AI Certification Prep - Powered by Azure AI Agents + MCP</p>

        <form method="POST">
            <label>📊 Number of Questions (1-20):</label>
            <input type="number" name="num_questions" min="1" max="20" value="5" required>

            <label>🎯 Topic (optional - leave blank for random):</label>
            <select name="topic">
                <option value="">🎲 Random AI-102 Topic</option>
                {{ topics|safe }}
            </select>

            <button type="submit">🚀 Generate Quiz & Start</button>
        </form>

        <div class="info">
            <strong>💡 What to expect:</strong><br>
            • Deep technical questions on Azure AI services<br>
            • SDK specs, quotas, limits, and edge cases<br>
            • Questions generated dynamically via AI agent<br>
            • Real Microsoft Learn documentation context
        </div>
    </div>

    <script>
        // Matrix rain effect
        const canvas = document.getElementById('matrix-canvas');
        const ctx = canvas.getContext('2d');

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()';
        const fontSize = 14;
        const columns = canvas.width / fontSize;
        const drops = Array(Math.floor(columns)).fill(1);

        function drawMatrix() {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = '#00ff00';
            ctx.font = fontSize + 'px monospace';

            for (let i = 0; i < drops.length; i++) {
                const text = letters[Math.floor(Math.random() * letters.length)];
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);

                if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                    drops[i] = 0;
                }
                drops[i]++;
            }
        }

        setInterval(drawMatrix, 35);

        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
    </script>
</body>
</html>
"""

HTML_QUIZ = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-102 Quiz - Question {{ idx }}/{{ total }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: #000;
            color: #00ff00;
            font-family: 'Courier New', Courier, monospace;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            position: relative;
        }

        #matrix-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            opacity: 0.2;
        }

        .quiz-container {
            position: relative;
            z-index: 1;
            max-width: 800px;
            width: 100%;
            background: rgba(0, 0, 0, 0.95);
            border: 2px solid #0078D4;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 0 40px rgba(0, 120, 212, 0.6);
        }

        .progress {
            text-align: center;
            color: #0078D4;
            font-size: 1.2em;
            margin-bottom: 20px;
            font-weight: bold;
        }

        .question {
            color: #fff;
            font-size: 1.3em;
            line-height: 1.6;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0, 120, 212, 0.1);
            border-left: 4px solid #0078D4;
        }

        .options {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .option-btn {
            width: 100%;
            padding: 15px 20px;
            background: #001133;
            border: 2px solid #00ff00;
            color: #00ff00;
            font-family: 'Courier New', Courier, monospace;
            font-size: 1.1em;
            text-align: left;
            cursor: pointer;
            border-radius: 5px;
            transition: all 0.3s;
        }

        .option-btn:hover {
            background: #0078D4;
            color: #000;
            border-color: #0078D4;
            transform: translateX(10px);
            box-shadow: 0 0 15px rgba(0, 120, 212, 0.8);
        }

        input[type="text"] {
            width: 100%;
            padding: 15px;
            background: #001122;
            border: 2px solid #0078D4;
            color: #00ff00;
            font-family: 'Courier New', Courier, monospace;
            font-size: 1.1em;
            border-radius: 5px;
            margin-bottom: 15px;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: #00ff00;
            box-shadow: 0 0 15px rgba(0, 255, 0, 0.3);
        }

        .submit-btn {
            width: 100%;
            padding: 15px;
            background: #0078D4;
            border: none;
            color: #fff;
            font-family: 'Courier New', Courier, monospace;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            border-radius: 5px;
            transition: all 0.3s;
        }

        .submit-btn:hover {
            background: #005a9e;
            box-shadow: 0 0 20px rgba(0, 120, 212, 1);
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
        }

        .modal-content {
            background: #000;
            margin: 10% auto;
            padding: 30px;
            border: 2px solid #0078D4;
            border-radius: 10px;
            max-width: 600px;
            box-shadow: 0 0 50px rgba(0, 120, 212, 0.8);
        }

        .modal h2 {
            color: #0078D4;
            margin-bottom: 20px;
        }

        .modal p {
            color: #00ff00;
            line-height: 1.8;
            margin: 10px 0;
        }

        .modal button {
            margin-top: 20px;
            padding: 12px 30px;
            background: #0078D4;
            border: none;
            color: #fff;
            font-family: 'Courier New', Courier, monospace;
            font-size: 1.1em;
            cursor: pointer;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <canvas id="matrix-canvas"></canvas>

    <div class="quiz-container">
        <div class="progress">Question {{ idx }} / {{ total }}</div>

        <div class="question">{{ question.question }}</div>

        {% if question.type == "multi" %}
        <div class="options">
            {% for opt in question.options %}
            <button class="option-btn" onclick="submitAnswer('{{ opt }}')">{{ opt }}</button>
            {% endfor %}
        </div>

        {% elif question.type == "tf" %}
        <div class="options">
            <button class="option-btn" onclick="submitAnswer('true')">✅ TRUE</button>
            <button class="option-btn" onclick="submitAnswer('false')">❌ FALSE</button>
        </div>

        {% else %}
        <input type="text" id="short-answer" placeholder="Type your answer here..." onkeypress="if(event.key==='Enter') submitShortAnswer()">
        <button class="submit-btn" onclick="submitShortAnswer()">Submit Answer</button>
        {% endif %}
    </div>

    <div id="feedback-modal" class="modal">
        <div class="modal-content">
            <h2 id="result-title"></h2>
            <p><strong>Your answer:</strong> <span id="user-answer"></span></p>
            <p><strong>Correct answer:</strong> <span id="correct-answer"></span></p>
            <p><strong>Explanation:</strong></p>
            <p id="explanation"></p>
            <p><strong>Score:</strong> <span id="score"></span></p>
            <button onclick="nextQuestion()">Continue</button>
        </div>
    </div>

    <script>
        // Matrix effect (same as home page)
        const canvas = document.getElementById('matrix-canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()';
        const fontSize = 14;
        const columns = canvas.width / fontSize;
        const drops = Array(Math.floor(columns)).fill(1);

        function drawMatrix() {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#00ff00';
            ctx.font = fontSize + 'px monospace';

            for (let i = 0; i < drops.length; i++) {
                const text = letters[Math.floor(Math.random() * letters.length)];
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);
                if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
                drops[i]++;
            }
        }
        setInterval(drawMatrix, 35);

        // Quiz logic
        async function submitAnswer(answer) {
            const response = await fetch('/answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answer: answer })
            });

            const data = await response.json();
            showFeedback(answer, data);
        }

        function submitShortAnswer() {
            const answer = document.getElementById('short-answer').value.trim();
            if (!answer) {
                alert('Please enter an answer!');
                return;
            }
            submitAnswer(answer);
        }

        function showFeedback(userAnswer, data) {
            const modal = document.getElementById('feedback-modal');
            document.getElementById('result-title').textContent = data.correct ? '✅ Correct!' : '❌ Incorrect';
            document.getElementById('result-title').style.color = data.correct ? '#00ff00' : '#ff0000';
            document.getElementById('user-answer').textContent = userAnswer;
            document.getElementById('correct-answer').textContent = data.correct_answer;
            document.getElementById('explanation').textContent = data.explanation;
            document.getElementById('score').textContent = `${data.score} / ${data.total}`;

            modal.style.display = 'block';
            window.currentData = data;
        }

        function nextQuestion() {
            if (window.currentData.done) {
                alert(`Quiz Complete! Final Score: ${window.currentData.score}/${window.currentData.total}`);
                window.location.href = '/';
            } else {
                window.location.reload();
            }
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    print("🚀 Starting AI-102 Quiz Agent...")
    print("📍 Initializing Azure AI Agent...")

    init_azure_agent()

    print("🌐 Flask server starting at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop")

    app.run(host="127.0.0.1", port=5000, debug=True)
