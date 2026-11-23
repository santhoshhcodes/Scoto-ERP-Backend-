import os
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import dotenv_values
from src.core.config import settings


def _get_smtp_credentials():
    """Dynamically fetch latest SMTP credentials from .env to ensure fresh credentials."""
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_file = os.path.join(backend_root, ".env")
    env_vals = dotenv_values(env_file) if os.path.exists(env_file) else {}

    host = env_vals.get("SMTP_HOST") or settings.SMTP_HOST or "smtp.gmail.com"
    try:
        port = int(env_vals.get("SMTP_PORT") or settings.SMTP_PORT or 587)
    except ValueError:
        port = 587

    user = (env_vals.get("SMTP_USER") or settings.SMTP_USER or "").strip()
    raw_pwd = env_vals.get("SMTP_PASSWORD") or settings.SMTP_PASSWORD or ""
    pwd = str(raw_pwd).replace(" ", "").replace('"', '').replace("'", "").strip()
    from_addr = env_vals.get("SMTP_FROM") or settings.SMTP_FROM or f"Scoto ERP System <{user}>"

    return host, port, user, pwd, from_addr


def send_otp_email(to_email: str, user_name: str, otp_code: str, purpose: str = "Reset Password") -> bool:
    try:
        host, port, user, pwd, from_addr = _get_smtp_credentials()

        if not user or not pwd:
            print("[Mail Error] SMTP_USER or SMTP_PASSWORD is not configured in .env!")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Scoto ERP - Your OTP Code for {purpose}"
        msg["From"] = from_addr
        msg["To"] = to_email.strip()

        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #333; max-width: 500px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #4338ca; margin-bottom: 8px;">Scoto ERP Security Verification</h2>
            <p>Hello <b>{user_name}</b>,</p>
            <p>You have requested an OTP code for <b>{purpose}</b>.</p>
            <div style="background-color: #f1f5f9; padding: 15px; text-align: center; border-radius: 6px; margin: 20px 0;">
                <span style="font-size: 28px; font-weight: bold; letter-spacing: 6px; color: #1e293b;">{otp_code}</span>
            </div>
            <p style="color: #64748b; font-size: 13px;">This code is valid for <b>10 minutes</b>. If you did not make this request, please report it to your System Admin.</p>
        </div>
        """
        msg.attach(MIMEText(html_content, "html"))

        context = ssl.create_default_context()

        # Primary attempt: Configured Host & Port (587 STARTTLS)
        try:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(user, pwd)
                server.sendmail(user, to_email.strip(), msg.as_string())
            return True
        except Exception as primary_err:
            print(f"[Mail Notice] Port {port} connect failed: {primary_err}. Attempting SSL fallback on Port 465...")
            # Fallback attempt: Port 465 (Direct SSL)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=20) as server:
                server.login(user, pwd)
                server.sendmail(user, to_email.strip(), msg.as_string())
            return True

    except Exception as e:
        print(f"[Mail Error] Failed to send email: {e}")
        return False
