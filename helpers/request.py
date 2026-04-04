import httpx
from helpers.config import settings


async def send_login_email(to: str, code: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2>Your Login Code</h2>
        <p>Use the code below to sign in to <strong>Business Idea Validator</strong>:</p>
        <h1 style="letter-spacing: 6px; font-size: 40px;">{code}</h1>
        <p>This code expires in <strong>10 minutes</strong>. Do not share it with anyone.</p>
    </div>
    """
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://mail.tribearc.com/api/campaigns/send_now.php",
            data={
                "api_key": settings.email_api_key,
                "from_name": "Business Idea Validator",
                "from_email": "no-reply@businessideavalidator.com",
                "reply_to": "support@businessideavalidator.com",
                "subject": "Your Login Code",
                "html_text": html,
                "emails": to,
                "send_campaign": "1",
            },
        )
