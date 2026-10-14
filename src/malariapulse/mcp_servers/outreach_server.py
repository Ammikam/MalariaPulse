"""MCP server: drafts community health advisories (English / Swahili) and share links.

Drafts only. A human reviews and sends every message: this server never sends anything.
Swahili text must be reviewed by a native speaker / health communication officer before real use.
"""
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("malariapulse-outreach", log_level="WARNING")

TEMPLATES = {
    ("chw", "en"): (
        "MALARIA ALERT for {zone}: risk is {level}. Please: (1) test every fever case with an RDT, "
        "(2) start ACT treatment promptly for positive cases, (3) remind households to sleep under treated nets "
        "every night, (4) report rising cases to the sub-county health office."
    ),
    ("chw", "sw"): (
        "TAHADHARI YA MALARIA, {zone}: hatari ni {level_sw}. Tafadhali: (1) pima kila mgonjwa mwenye homa kwa RDT, "
        "(2) anza dawa ya ACT mara moja kwa watakaopatikana na malaria, (3) wakumbushe kaya zilale ndani ya "
        "chandarua kilichotiwa dawa kila usiku, (4) ripoti ongezeko la wagonjwa kwa ofisi ya afya ya wilaya."
    ),
    ("residents", "en"): (
        "Malaria risk is {level} in {zone}. Sleep under a treated net every night, clear standing water "
        "around your home, and if you or your child has a fever, go to the nearest health facility for a test early."
    ),
    ("residents", "sw"): (
        "Hatari ya malaria ni {level_sw} katika {zone}. Lala ndani ya chandarua kilichotiwa dawa kila usiku, "
        "ondoa maji yaliyotuama karibu na nyumba yako, na ukipata homa wewe au mtoto wako, nenda kituo cha afya "
        "kilicho karibu upimwe mapema."
    ),
}
LEVEL_SW = {"high": "kubwa", "moderate": "ya wastani", "low": "ndogo"}


@mcp.tool()
def draft_advisory(zone: str, risk_level: str, language: str = "en", audience: str = "residents") -> dict:
    """Draft a short public-health advisory for a zone. Draft only: a human must review and send it.

    Args:
        zone: Zone name.
        risk_level: 'high', 'moderate' or 'low'.
        language: 'en' (English) or 'sw' (Swahili).
        audience: 'chw' (community health workers) or 'residents'.
    """
    key = (audience, language)
    if key not in TEMPLATES:
        raise ValueError("audience must be 'chw' or 'residents'; language must be 'en' or 'sw'")
    text = TEMPLATES[key].format(zone=zone, level=risk_level, level_sw=LEVEL_SW.get(risk_level, risk_level))
    return {
        "zone": zone,
        "audience": audience,
        "language": language,
        "text": text,
        "status": "DRAFT: needs human approval",
    }


@mcp.tool()
def make_whatsapp_share_link(message: str) -> dict:
    """Build a WhatsApp click-to-chat link with the message prefilled. A person must tap send.

    Args:
        message: The approved message text.
    """
    return {"url": "https://wa.me/?text=" + quote(message)}


if __name__ == "__main__":
    mcp.run()
