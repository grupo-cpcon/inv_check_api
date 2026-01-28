import base64
import httpx

async def download_file_base64(url: str, timeout: int = 30) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return base64.b64encode(resp.content).decode()
    except Exception:
        return None