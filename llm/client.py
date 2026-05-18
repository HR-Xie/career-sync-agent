from openai import AsyncOpenAI


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=120.0)

    async def chat(self, system_prompt: str, user_message: str, temperature: float = 1.0) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content or ""

    async def chat_with_image(
        self, system_prompt: str, text: str, image_base64: str, content_type: str = "image/jpeg", temperature: float = 1.0
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{content_type};base64,{image_base64}"},
                        },
                    ],
                },
            ],
        )
        return response.choices[0].message.content or ""
