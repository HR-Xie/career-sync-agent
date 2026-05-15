import logging
from llm.client import LLMClient

logger = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self, primary: LLMClient, fallback: LLMClient | None = None, max_retries: int = 3):
        self.primary = primary
        self.fallback = fallback
        self.max_retries = max_retries

    async def _try_call(self, client: LLMClient, method: str, *args, **kwargs) -> str:
        for attempt in range(self.max_retries):
            try:
                fn = getattr(client, method)
                return await fn(*args, **kwargs)
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
        raise RuntimeError("Unexpected: all retries exhausted")

    async def chat(self, system_prompt: str, user_message: str) -> str:
        try:
            return await self._try_call(self.primary, "chat", system_prompt, user_message)
        except Exception as e:
            logger.error(f"Primary LLM failed: {e}")
            if self.fallback:
                logger.info("Switching to fallback LLM")
                return await self._try_call(self.fallback, "chat", system_prompt, user_message)
            raise

    async def chat_with_image(self, system_prompt: str, text: str, image_base64: str, content_type: str = "image/jpeg") -> str:
        # Vision tasks use Kimi as primary, DeepSeek as fallback
        vision_primary = self.fallback or self.primary
        vision_fallback = self.primary if self.fallback else None
        try:
            return await self._try_call(vision_primary, "chat_with_image", system_prompt, text, image_base64, content_type)
        except Exception as e:
            logger.error(f"Vision LLM (Kimi) failed: {e}")
            if vision_fallback:
                logger.info("Falling back to DeepSeek for vision")
                return await self._try_call(vision_fallback, "chat_with_image", system_prompt, text, image_base64, content_type)
            raise
