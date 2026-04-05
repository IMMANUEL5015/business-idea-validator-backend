import json
from openai import OpenAI
from fastapi import HTTPException
from helpers.config import settings
from helpers.business_idea_criteria import criteria

client = OpenAI(api_key=settings.ai_secret_key)

HIGH_INTELLIGENCE_MODEL = "gpt-4-turbo"

LOW_COST_MODEL = "gpt-3.5-turbo"

def validate_idea(title: str, description: str) -> dict:
    criteria_messages = [
        {
            "role": "system",
            "content": (
                f"Evaluation Criterion {i + 1}: {criterion.strip()} "
                "Using your internal knowledge and by searching the internet for current evidence, "
                "assess whether this business idea passes or fails this criterion. "
                "Look for real market data, competitor examples, consumer trends, and any other "
                "evidence that supports or challenges this criterion as it applies to the idea."
            ),
        }
        for i, criterion in enumerate(criteria)
    ]

    response = client.chat.completions.create(
        model=HIGH_INTELLIGENCE_MODEL,
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert business analyst specializing in the European SME market. "
                    "Your job is to objectively evaluate business ideas and give honest, data-informed assessments. "
                    "You have access to the internet and must search for real-world evidence when evaluating ideas."
                ),
            },
            {
                "role": "system",
                "content": (
                    "You will evaluate the business idea provided by the user against a set of specific criteria. "
                    "Each criterion will be given to you as a separate instruction. "
                    "Weigh all criteria equally when computing your final score. "
                    "An idea that passes all criteria should score close to 100. "
                    "An idea that fails multiple criteria should score significantly lower."
                ),
            },
            *criteria_messages,
            {
                "role": "system",
                "content": (
                    "After evaluating the idea against all criteria, respond only with valid JSON "
                    "containing exactly these four fields: "
                    "\"score\" (a float between 0 and 100 reflecting how well the idea passed all criteria), "
                    "\"risks\" (a string summarising the key risks uncovered across all criteria), "
                    "\"opportunities\" (a string summarising the key market opportunities identified), "
                    "\"ai_feedback\" (a string with your overall honest assessment, based on each provided criteria, but without explicitly referencing each criteria number in your response"
                    "the idea passed and failed, and a clear recommendation on whether to proceed). "
                    "Do not include any text outside the JSON object."
                ),
            },
            {
                "role": "user",
                "content": f"Business Idea Title: {title}\n\nDescription: {description}",
            },
        ],
    )

    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="The system was unable to validate your idea. Please try again.",
        )

def generate_business_plan(title: str, description: str, validation: dict) -> dict:
    response = client.chat.completions.create(
        model=HIGH_INTELLIGENCE_MODEL,
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior business consultant with deep expertise in the European SME market. "
                    "You create detailed, actionable business plans that are grounded in real market realities."
                ),
            },
            {
                "role": "system",
                "content": (
                    "The user will provide a business idea along with its prior validation results "
                    "(score, identified risks, and opportunities). "
                    "Use this context to generate a comprehensive and realistic business plan tailored to the European market."
                ),
            },
            {
                "role": "system",
                "content": (
                    "Respond only with valid JSON containing exactly these fields: "
                    "\"executive_summary\" (string), "
                    "\"problem_statement\" (string), "
                    "\"proposed_solution\" (string), "
                    "\"target_market\" (string), "
                    "\"unique_value_proposition\" (string), "
                    "\"revenue_model\" (string), "
                    "\"go_to_market_strategy\" (string), "
                    "\"competitive_landscape\" (string), "
                    "\"risks_and_mitigation\" (string), "
                    "\"financial_outlook\" (string), "
                    "\"next_steps\" (string). "
                    "Do not include any text outside the JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Business Idea Title: {title}\n\n"
                    f"Description: {description}\n\n"
                    f"Validation Score: {validation.get('score')}/100\n"
                    f"Identified Risks: {validation.get('risks')}\n"
                    f"Identified Opportunities: {validation.get('opportunities')}\n"
                    f"Overall AI Feedback: {validation.get('ai_feedback')}"
                ),
            },
        ],
    )

    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="The system was unable to generate a business plan. Please try again.",
        )

def summarize_conversations(messages: list) -> str:
    formatted = "\n".join(
        f"{'User' if m.role.value == 'user' else 'AI'}: {m.message}"
        for m in messages
    )

    response = client.chat.completions.create(
        model=LOW_COST_MODEL,
        temperature=0.5,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise summarizer. "
                    "Respond only with valid JSON containing a single field: "
                    "\"summary\" (a string). Do not include any text outside the JSON object."
                ),
            },
            {
                "role": "system",
                "content": (
                    "The user will give you a conversation history between a user and an AI business advisor. "
                    "Summarize the key points, decisions, and insights from the conversation in no more than 150 words. "
                    "Focus on what was discussed about the business idea — not conversational filler."
                ),
            },
            {
                "role": "user",
                "content": formatted,
            },
        ],
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
        return parsed.get("summary", "")
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="The system was unable to summarize the conversation. Please try again.",
        )

def chat(
    title: str,
    description: str,
    summary: str,
    recent_messages: list,
    validation,
    business_plan,
    user_message: str,
) -> str:
    validation_context = (
        f"Validation Score: {validation.score}/100\n"
        f"Risks: {validation.risks}\n"
        f"Opportunities: {validation.opportunities}\n"
        f"Overall Feedback: {validation.ai_feedback}"
        if validation else
        "No validation has been run on this idea yet."
    )

    business_plan_context = (
        "\n".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in business_plan.content.items())
        if business_plan else
        "No business plan has been generated for this idea yet."
    )

    history_context = (
        f"Here is a summary of the earlier conversation:\n{summary}"
        if summary else
        "There is no prior conversation history."
    )

    history_messages = [
        {
            "role": "user" if m.role.value == "user" else "assistant",
            "content": m.message,
        }
        for m in recent_messages
        if m.message != user_message
    ]

    system_messages = [
        {
            "role": "system",
            "content": (
                "You are an expert AI business advisor specializing in the European SME market. "
                "You are helping a user refine and develop their business idea through conversation. "
                "Be insightful, honest, and practical in your responses."
            ),
        },
        {
            "role": "system",
            "content": (
                f"The business idea you are advising on is:\n"
                f"Title: {title}\n"
                f"Description: {description}"
            ),
        },
        {
            "role": "system",
            "content": f"Validation results for this idea:\n{validation_context}",
        },
        {
            "role": "system",
            "content": f"Business plan for this idea:\n{business_plan_context}",
        },
        {
            "role": "system",
            "content": history_context,
        },
        {
            "role": "system",
            "content": (
                "Respond conversationally and helpfully. "
                "Your response should be clear, concise, and directly relevant to what the user has asked. "
                "Do not repeat information the user already knows unless they ask for it."
            ),
        },
    ]

    response = client.chat.completions.create(
        model=HIGH_INTELLIGENCE_MODEL,
        temperature=0.7,
        messages=system_messages + history_messages + [{"role": "user", "content": user_message}],
    )

    return response.choices[0].message.content