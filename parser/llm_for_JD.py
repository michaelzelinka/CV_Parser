async def extract_structured_jd(text: str):
    if not text:
        return {}

    response = await client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "type": "input_text",
                "text": "Extract role requirements, required skills, nice-to-have skills, seniority."
            },
            {
                "type": "input_text",
                "text": text
            }
        ]
    )

    return response.output_text
