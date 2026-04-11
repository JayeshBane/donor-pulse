import requests
from config import settings


async def get_llm_reponse(prompt):

    ACCOUNT_ID = settings.cloudflare_account_id
    AUTH_TOKEN = settings.cloudflare_auth_token
    # prompt = "Tell me all about PEP-8"
    response = requests.post(
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/meta/llama-3.2-3b-instruct",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        json={
        "messages": [
            {"role": "system", "content": "You are a friendly assistant"},
            {"role": "user", "content": prompt}
        ]
        }
    )
    result = response.json()
    return result