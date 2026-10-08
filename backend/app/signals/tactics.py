"""Rule-based persuasion-tactic tagger.

Each tactic is a set of regexes over lower-cased text. Matches are merged with the
tactics returned by the LLM extractor (when available) in the pipeline.
"""
import re

from app.signals.context import first_affirmative_match

TACTICS = [
    "authority",
    "urgency",
    "fear_threat",
    "secrecy",
    "payment_demand",
    "pii_request",
    "advance_fee",
    "too_good",
]

TACTIC_LABELS = {
    "authority": "Claims to be an official",
    "urgency": "Pressures you to act now",
    "fear_threat": "Threatens arrest, deportation or visa loss",
    "secrecy": "Tells you not to tell anyone",
    "payment_demand": "Demands payment in an unusual way",
    "pii_request": "Asks for SSN, passport or bank details",
    "advance_fee": "Asks you to pay a fee up front",
    "too_good": "Too good to be true",
}

_RAW = {
    "authority": [
        r"\b(officer|agent|inspector|deputy|sergeant|lieutenant|special agent)\b",
        r"\b(badge|case|reference|warrant)\s*(number|no\.?|#|id)\b",
        r"\b(department of homeland security|homeland security|immigration and customs|u\.?s\.? immigration|federal (agent|government|court))\b",
        r"\b(ice|uscis|dhs|sevp|fbi|irs|ssa|cbp)\b.{0,30}\b(office|department|officer|agent|division|headquarters|field office)\b",
        r"\bthis is (a call|an official|the) .{0,30}(government|immigration|federal|police)\b",
    ],
    "urgency": [
        r"\b(immediately|urgent(ly)?|right away|right now|as soon as possible|asap)\b",
        r"\bwithin (the next )?\d+\s*(minutes?|mins?|hours?|hrs?)\b",
        r"\b(today|tonight) (only|before|by)\b",
        r"\b(final|last) (notice|warning|chance|reminder)\b",
        r"\b(expires?|deadline) (in|today|tonight)\b",
        r"\bdo not (hang up|disconnect|end this call)\b",
        r"\b(today|tonight|now)\b.{0,40}\b(or|otherwise|before)\b.{0,40}\b(deport\w*|arrest\w*|terminat\w*|cancel\w*|lock\w*|lose|expel\w*|escalat\w*)\b",
        r"\b(in|within) (\d+|one|two|three) ?(h|hrs?|hours?)\b",
    ],
    "fear_threat": [
        r"\b(deport(ed|ation)?|removal proceedings|arrest(ed)?|warrant|detain(ed)?|jail|prison|handcuff)\b",
        r"\b(sevis|visa|status|i-20|f-?1|opt|ead)\b.{0,40}\b(terminat\w*|cancel\w*|revok\w*|suspend\w*|invalid\w*|blacklist\w*)\b",
        r"\b(terminat\w*|cancel\w*|revok\w*)\b.{0,40}\b(sevis|visa|status|i-20|f-?1|opt)\b",
        r"\b(legal action|criminal charges?|lawsuit|penalt(y|ies)|fined)\b",
        r"\b(money laundering|drug trafficking|identity (fraud|theft) investigation)\b",
        r"\b(out of status|remove you|remove me|removal|be removed|lose (your|my) (status|visa|ead|opt|i-20)|freeze (your|my) (bank )?accounts?|expulsion|expelled)\b",
        r"\b(officers?|police|agents?) (will|would) (come|visit|be sent)\b",
    ],
    "secrecy": [
        r"\b(do not|don't|dont|never) (tell|inform|contact|discuss|share|talk to|speak to|mention)\b.{0,40}\b(anyone|anybody|school|university|dso|advisor|adviser|family|friends|parents|police|bank|isss|office)\b",
        r"\b(keep (this|it) (confidential|secret|private)|strictly confidential|gag order)\b",
        r"\b(stay on the (line|phone)|do not hang up|if (i|you) hang up)\b",
        r"\b(not to|don't|do not) (call|tell|contact) (anyone|anybody|your school|the school)\b",
        r"\b(sealed|confidential|secret) (case|investigation|matter)\b",
        r"\b(resolve|settle) (this|it) privately\b",
    ],
    "payment_demand": [
        r"\b(gift ?cards?|itunes|apple card|google play card|steam card|amazon card)\b",
        r"\b(bitcoin|btc|crypto(currency)?|usdt|tether|ethereum|bitcoin atm|crypto atm|wallet address)\b",
        r"\b(wire transfer|western union|moneygram|zelle|cash ?app|venmo)\b",
        r"\b(pay|send|deposit|transfer)\b.{0,30}\b(fine|fee|bond|penalty|deposit|security deposit|clearance)\b",
        r"\b(fine|fee|bond|penalty)\b.{0,30}\$\s?\d",
        r"\b(prepaid (debit )?card|card number and pin|bitcoin machine)\b",
        r"\btransfer (your|my) (savings|money|funds)\b",
    ],
    "pii_request": [
        r"\b(ssn|social security( number)?|passport( number)?|i-94|a-number|alien (registration )?number|sevis id)\b.{0,40}\b(confirm|verify|provide|send|share|give|read|need)\b",
        r"\b(confirm|verify|provide|send|share|give|read|need)\b.{0,40}\b(ssn|social security|passport|i-94|a-number|sevis id|date of birth|bank (login|account)|card number|online banking)\b",
        r"\b(photo|picture|scan|copy) of (your )?(passport|id|i-20|ead|visa|ssn card)\b",
        r"\b(photos?|pictures?|scans?|scanned cop(y|ies)|selfie)\b.{0,30}\b(passport|i-20|visa|social security card|driver'?s license)\b",
        r"\b(which bank|bank (name|statement|details|information)|how much money)\b",
    ],
    "advance_fee": [
        r"\b(registration|processing|training|onboarding|placement|verification|sponsorship|application|e-?verify|i-?983) (fee|charge|cost|payment)\b",
        r"\b(pay|purchase|buy)\b.{0,40}\b(equipment|starter kit|training|certification|employer letter|offer letter|i-?983|opt letter|sponsorship)\b",
        r"\b(deposit|top[- ]?up|recharge)\b.{0,40}\b(unlock|withdraw|commission|earnings|tasks?|account balance|level)\b",
        r"\b(reimburse(d|ment)?|deposit (this|the) check|mobile deposit)\b.{0,60}\b(send|transfer|buy|purchase|vendor|equipment)\b",
        r"\b(send|mail|receive)\b.{0,20}\bchecks?\b.{0,60}\b(buy|purchase|supplies|equipment|vendor|send the rest|keep)\b",
        r"(\bpay\b|\bfee\b|\$\s?\d).{0,60}\b(offer letter|employment (verification )?letter|experience letter|paystubs?|i-?983|e-?verify|bench|onboarding|background check)\b",
        r"\b(offer letter|experience letter|i-?983|e-?verify|bench)\b.{0,60}(\bfee\b|\$\s?\d|\bprice\b|\bpackage\b|\bpay\b)",
        r"\bpay (your|my) own salary\b|\b(stop|pause|freeze) the (unemployment )?clock\b|\bno need to (actually )?work\b",
        r"\b(upfront|up-front|reserve your seat|activate your (employee|account))\b",
    ],
    "too_good": [
        r"\$\s?\d{2,4}\s*(\+\s*)?(per|/|a)\s*(day|hour|hr)\b.{0,40}\b(no experience|easy|simple|from home|part[- ]time|flexible)\b",
        r"\b(no experience (needed|required)|no interview|hired immediately|guaranteed (job|income|placement|approval|profit))\b",
        r"\b(pre-?approved|100% approval|interview (was )?conducted (via|by|over) (text|chat))\b",
        r"\$\s?\d{2,4}\s*-\s*\$?\d{2,4}\s*(per day|a day|daily|/day)",
        r"\b(earn|make)\b.{0,20}\$\s?\d{2,5}.{0,30}\b(daily|a day|per day|per week|weekly)\b",
        r"\b(like|rate|review|boost|optimi[sz]e)\b.{0,30}\b(videos?|products?|apps?|hotels?|orders?)\b.{0,40}\b(earn|commission|paid)\b",
        r"\b(you (have been|were|are) (selected|chosen|approved)|congratulations)\b.{0,60}\b(job|position|scholarship|grant|prize|offer)\b",
    ],
}

PATTERNS = {k: [re.compile(p, re.I) for p in v] for k, v in _RAW.items()}


def tag_tactics(text: str) -> dict[str, list[str]]:
    """Return {tactic: [matched snippets]} for tactics that fire."""
    found: dict[str, list[str]] = {}
    for tactic, rxs in PATTERNS.items():
        hits = []
        for rx in rxs:
            m = first_affirmative_match(rx, text)
            if m:
                hits.append(m.group(0)[:80])
        if hits:
            found[tactic] = hits
    return found
