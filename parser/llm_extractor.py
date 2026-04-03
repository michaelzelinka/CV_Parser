import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def extract_structured_cv(text: str):
    prompt = {
        "cv_text": text,
        "instructions": "Extract structured CV data."
    }

    response = await client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "type": "input_text",
                "text": f"Extract the following fields:\n"
                        f"- name\n- email\n- phone\n- years_experience\n"
                        f"- technologies (list)\n- languages (list)\n- seniority"
            },
            {
                "type": "input_text",
                "text": text
            }
        ]
    )

    return response.output_text
