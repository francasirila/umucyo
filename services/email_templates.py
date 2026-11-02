from html import escape

APP_NAME = "Umucyo"
BRAND = "#2f6f4e"


def _layout(preheader: str, body_html: str) -> str:
    return f"""<!doctype html>
<html>
<body style="margin:0;padding:0;background:#f4f7f5;font-family:Arial,Helvetica,sans-serif;">
  <span style="display:none;opacity:0;color:transparent;height:0;width:0;overflow:hidden;">{escape(preheader)}</span>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f7f5;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#ffffff;border-radius:12px;border:1px solid #e3e8e5;">
        <tr><td style="background:{BRAND};border-radius:12px 12px 0 0;padding:20px 28px;color:#ffffff;font-size:20px;font-weight:bold;">{APP_NAME}</td></tr>
        <tr><td style="padding:28px;color:#25352c;font-size:15px;line-height:1.6;">{body_html}</td></tr>
        <tr><td style="padding:16px 28px 24px;color:#7a8a80;font-size:12px;line-height:1.5;border-top:1px solid #eef2ef;">
          You received this email because of activity on your {APP_NAME} account.
          If this wasn't you, you can safely ignore it.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def render_otp_email(code: str, name: str = "", minutes: int = 10):
    greeting = f"Hi {escape(name)}," if name else "Hi,"
    subject = f"Your {APP_NAME} verification code: {code}"
    text = (
        f"{greeting}\n\nYour {APP_NAME} verification code is {code}.\n"
        f"It expires in {minutes} minutes.\n\nNever share this code with anyone."
    )
    html = _layout(
        f"Your code is {code}. It expires in {minutes} minutes.",
        f"""
        <p style="margin:0 0 12px;">{greeting}</p>
        <p style="margin:0 0 20px;">Use this code to finish signing in:</p>
        <div style="text-align:center;margin:0 0 20px;">
          <span style="display:inline-block;background:#f4f7f5;border:1px dashed {BRAND};border-radius:10px;
                       padding:14px 24px;font-size:32px;font-weight:bold;letter-spacing:8px;color:{BRAND};">{escape(code)}</span>
        </div>
        <p style="margin:0 0 12px;">This code expires in <strong>{minutes} minutes</strong>.</p>
        <p style="margin:0;color:#a12626;font-size:13px;">Never share this code with anyone. {APP_NAME} will never ask you for it.</p>
        """,
    )
    return subject, text, html


def render_invitation_email(link: str, name: str = ""):
    greeting = f"Hi {escape(name)}," if name else "Hi,"
    subject = f"You're invited to join {APP_NAME}"
    text = (
        f"{greeting}\n\nYou've been invited to join {APP_NAME} as an agent.\n"
        f"Set your password here: {link}\n\nThis link can be used once and expires soon."
    )
    html = _layout(
        "Set your password to activate your agent account.",
        f"""
        <p style="margin:0 0 12px;">{greeting}</p>
        <p style="margin:0 0 20px;">You've been invited to join {APP_NAME} as an agent. Set your password to activate your account.</p>
        <div style="text-align:center;margin:0 0 20px;">
          <a href="{escape(link)}" style="display:inline-block;background:{BRAND};color:#ffffff;text-decoration:none;
             padding:13px 28px;border-radius:8px;font-weight:bold;">Set my password</a>
        </div>
        <p style="margin:0 0 6px;font-size:13px;color:#55645b;">Or paste this link into your browser:</p>
        <p style="margin:0;font-size:12px;word-break:break-all;color:#55645b;">{escape(link)}</p>
        """,
    )
    return subject, text, html
  

def render_invitation_email(
    link: str,
    name: str = "",
    collection_point: str = "",
    expires_hours: int = 48,
):
    greeting = f"Hello {escape(name)}," if name else "Hello,"
    text_greeting = f"Hello {name}," if name else "Hello,"
    where_text = f" at {collection_point}" if collection_point else ""
    where_html = f" at <strong>{escape(collection_point)}</strong>" if collection_point else ""

    subject = f"Welcome to {APP_NAME}: set your password"
    text = (
        f"{text_greeting}\n\n"
        f"You have been registered as an agent{where_text} on {APP_NAME}.\n"
        f"Set your password to activate your account:\n{link}\n\n"
        f"This link can be used once and expires in {expires_hours} hours."
    )
    html = _layout(
        "Set your password to activate your agent account.",
        f"""
        <p style="margin:0 0 12px;">{greeting}</p>
        <p style="margin:0 0 20px;">You have been registered as an agent{where_html} on {APP_NAME}.
           Set your password to activate your account.</p>
        <div style="text-align:center;margin:0 0 20px;">
          <a href="{escape(link)}" style="display:inline-block;background:{BRAND};color:#ffffff;text-decoration:none;
             padding:13px 28px;border-radius:8px;font-weight:bold;">Set my password</a>
        </div>
        <p style="margin:0 0 12px;font-size:13px;color:#55645b;">This link can be used once and expires in <strong>{expires_hours} hours</strong>.</p>
        <p style="margin:0 0 6px;font-size:13px;color:#55645b;">Or paste this link into your browser:</p>
        <p style="margin:0;font-size:12px;word-break:break-all;color:#55645b;">{escape(link)}</p>
        """,
    )
    return subject, text, html