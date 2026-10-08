"""Parse raw RFC 822 email (.eml) into body text plus sender-authentication signals."""
import re
from dataclasses import dataclass, field
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from html import unescape


@dataclass
class EmailMeta:
    from_name: str = ""
    from_addr: str = ""
    reply_to: str = ""
    return_path: str = ""
    subject: str = ""
    spf: str = ""
    dkim: str = ""
    dmarc: str = ""
    links: list[str] = field(default_factory=list)

    @property
    def from_domain(self) -> str:
        return self.from_addr.rsplit("@", 1)[-1].lower() if "@" in self.from_addr else ""

    @property
    def reply_to_domain(self) -> str:
        return self.reply_to.rsplit("@", 1)[-1].lower() if "@" in self.reply_to else ""

    @property
    def auth_failed(self) -> bool:
        return any(v in {"fail", "softfail", "permerror"} for v in (self.spf, self.dkim, self.dmarc))

    @property
    def reply_to_mismatch(self) -> bool:
        return bool(self.reply_to_domain) and self.reply_to_domain != self.from_domain


_AUTH_RX = {k: re.compile(rf"\b{k}=(\w+)", re.I) for k in ("spf", "dkim", "dmarc")}
_HREF_RX = re.compile(r"""href=["']([^"']+)["']""", re.I)
_TAG_RX = re.compile(r"<[^>]+>")


def _html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", html)
    return unescape(_TAG_RX.sub(" ", html))


def parse_eml(raw: bytes) -> tuple[str, EmailMeta]:
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    name, addr = parseaddr(str(msg.get("From", "")))
    meta = EmailMeta(
        from_name=name,
        from_addr=addr,
        reply_to=parseaddr(str(msg.get("Reply-To", "")))[1],
        return_path=parseaddr(str(msg.get("Return-Path", "")))[1],
        subject=str(msg.get("Subject", "")),
    )
    auth = " ".join(str(h) for h in msg.get_all("Authentication-Results", []) or [])
    for key, rx in _AUTH_RX.items():
        m = rx.search(auth)
        if m:
            setattr(meta, key, m.group(1).lower())

    plain, html = "", ""
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        try:
            content = part.get_content()
        except Exception:
            continue
        if ctype == "text/plain" and not plain:
            plain = content
        elif ctype == "text/html" and not html:
            html = content
    if html:
        meta.links = _HREF_RX.findall(html)
    body = plain or _html_to_text(html)

    header = f"From: {name} <{addr}>\nSubject: {meta.subject}\n\n"
    return header + body.strip(), meta
