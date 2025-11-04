import os
import re
import json
import uuid
import logging
from typing import List, Dict, Any, Optional

import google.generativeai as genai
import chromadb
from django.conf import settings

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


logger = logging.getLogger("ml") 

SCHEMA_EXPECTED = r"""RETOURNE UNIQUEMENT du JSON avec ce schéma :
{{
  "decision": "Hire" | "Reject",
  "match_scores": {{"skills": int, "education": int, "experience": int, "overall": int}},
  "missing_requirements": [string],
  "evidence": {{"skills": [string], "education": [string], "experience": [string]}},
  "notes": string
}}"""



_RX_MON_YEAR = re.compile(r"\b([A-Za-zéèêàùûîôç\.]{3,10})\s*\.?\s*(20\d{2}|19\d{2})\b", re.I)
_RX_MM_YYYY  = re.compile(r"\b(0?[1-9]|1[0-2])[/\-](20\d{2}|19\d{2})\b")
_RX_YYYY     = re.compile(r"\b(20\d{2}|19\d{2})\b")
_RX_SPAN     = re.compile(r"\s*(?:-|–|—|to|au|jusqu(?:’|')?à|->|→)\s*", re.I)


#changer l'api key dans .env
API_KEY = settings.GOOGLE_API_KEY
if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY manquante (.env)")
genai.configure(api_key=API_KEY)

EMBEDDINGS = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")



def _read_pdf(path: str) -> str:
    import fitz  
    doc = fitz.open(path)
    out = [p.get_text("text") for p in doc]
    return "\n".join(out).strip()


def extract_text_any(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _read_pdf(path)
    raise ValueError("Formats supportés: .pdf")


#changer la version de gemini
def make_llm(model: str = "gemini-2.0-flash", temperature: float = 0.0, max_output_tokens: int = 2048):
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        model_kwargs={"response_mime_type": "application/json",
                      "language": "fr",}
    )

def build_vectorstore_from_text(text: str, resume_id: str) -> Chroma:
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=180)
    chunks = splitter.split_text(text)
  
    docs = [Document(page_content=c, metadata={"source": "resume", "resume_id": resume_id}) for c in chunks]
    client = chromadb.EphemeralClient()
    return Chroma.from_documents(
        documents=docs,
        embedding=EMBEDDINGS,
        client=client,
        collection_name=f"resume-{resume_id}",
    )


SECTION_PATTERNS = [
    r"\bcomp[eé]tences?\b",
    r"\bskills?\b",
    r"\btechnolog(?:ie|y|ies)\b|\boutils?\b",
    r"\bstack\b",
    r"\blangages?\b|\bprogramming languages?\b",
]

EXP_SECTION_PATTERNS = [
    r"\bexp[eé]riences?\b",
    r"\bwork\s*experience\b",
    r"\bemployment\s+history\b",
    r"\bprofessional\s+experience\b",
    r"\bstages?\b",
    r"\bintern(?:ship)?s?\b",
    r"\bprojets?\s+(acad[eé]miques?|professionnels?)\b",
]
EDU_SECTION_PATTERNS = [
    r"\bformations?\b",
    r"\b[ée]ducation\b",
    r"\bdipl[oô]mes?\b",
    r"\bparcours\s+acad[eé]mique\b",
    r"\buniversit[eé]|\b[ée]cole\b",
]



def extract_priority_sections(resume_text: str, resume_id: str) -> List[Document]:
    blocks = re.split(r"\n{2,}", resume_text)
    priority: List[Document] = []
    for i, b in enumerate(blocks):
        header = b.strip().lower()
        if any(re.search(p, header) for p in SECTION_PATTERNS):
            snip = b.strip()
            if i + 1 < len(blocks):
                snip = snip + "\n\n" + blocks[i + 1].strip()
            priority.append(
                Document(
                    page_content=snip[:1800],
                    metadata={"source": "resume-priority", "section": "skills", "resume_id": resume_id},
                )
            )
    return priority[:3]

def extract_experience_snippets(resume_text: str, resume_id: str) -> List[Document]:
    lines = resume_text.splitlines()
    snippets = []


    for i, line in enumerate(lines):
        low = line.strip().lower()
        if any(re.search(p, low, flags=re.I) for p in EXP_SECTION_PATTERNS):
            snip = "\n".join(lines[i:i+12]).strip()  
            if snip:
                snippets.append(Document(
                    page_content=snip[:1800],
                    metadata={"source":"resume-priority","section":"experience","resume_id":resume_id},
                ))

 
    for i, line in enumerate(lines):
        L = line.strip()
        low = L.lower()
        has_sep = (" - " in L) or ("–" in L) or ("—" in L) or (" au " in low) or (" to " in low) or ("jusqu" in low)
        has_date = _RX_MM_YYYY.search(L) or _RX_MON_YEAR.search(L) or _RX_YYYY.search(L)
        if has_sep and has_date:
            start = max(0, i-2); end = min(len(lines), i+4)
            snip = "\n".join(lines[start:end]).strip()
            if snip:
                snippets.append(Document(
                    page_content=snip[:1800],
                    metadata={"source":"resume-priority","section":"experience","resume_id":resume_id},
                ))

 
    seen, outdocs = set(), []
    for d in snippets:
        k = d.page_content.strip()
        if k and k not in seen:
            seen.add(k); outdocs.append(d)
            logger.info("EXP snippets kept: %d", len(outdocs))
    return outdocs[:5]

def extract_education_snippets(resume_text: str, resume_id: str) -> List[Document]:
    blocks = re.split(r"\n{2,}", resume_text)
    out = []
    for b in blocks:
        low = b.strip().lower()
        if any(re.search(p, low) for p in EDU_SECTION_PATTERNS):
            out.append(Document(page_content=b.strip()[:1800],
                metadata={"source":"resume-priority","section":"education","resume_id":resume_id}))
    return out[:3]



PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Tu es un évaluateur d'embauche très strict.
Utilise UNIQUEMENT le contexte du CV fourni. Pour chaque dimension (compétences, éducation, expérience),
si aucune preuve textuelle n'existe dans le contexte, note 0 pour cette partie.

Calcule des scores 0–100 : compétences, éducation, expérience. overall = 0.5*skills + 0.25*education + 0.25*experience.
Règle de décision :
- Si overall < 70 OU une dimension < 50 => "Reject"
- Sinon => "Hire"

RETOURNE UNIQUEMENT du JSON avec ce schéma :
{{
  "decision": "Hire" | "Reject",
  "match_scores": {{"skills": int, "education": int, "experience": int, "overall": int}},
  "missing_requirements": [string],
  "evidence": {{"skills": [string], "education": [string], "experience": [string]}},
  "notes": string
}}

Exige des extraits du contexte dans evidence. N'invente rien.
Les explications dans le champ "notes" doivent être rédigées uniquement en FRANÇAIS, 
dans un style professionnel et clair.
"""),
    ("human", """OFFRE D'EMPLOI :
{input}

CONTEXTE CV (extraits récupérés) :
{context}
"""),
])

def evaluate_candidate(job_offer_text: str, resume_file_path: str) -> Dict[str, Any]:
  
    resume_text = extract_text_any(resume_file_path)
    if not resume_text:
        return {"error": "Impossible d'extraire du texte du CV."}

    logger.info("evaluate_candidate: offer_len=%s, resume_path=%s", len(job_offer_text or ""), resume_file_path)
    logger.info("resume_text_len=%s", len(resume_text or ""))



    resume_id = str(uuid.uuid4())
    vs = build_vectorstore_from_text(resume_text, resume_id)


    priority_docs = (
    extract_priority_sections(resume_text, resume_id) +
    extract_experience_snippets(resume_text, resume_id) +
    extract_education_snippets(resume_text, resume_id)  
)

  
    retriever = vs.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 12,
            "fetch_k": 64,
            "lambda_mult": 0.6,
            "filter": {"resume_id": resume_id},
        },
    )
    try:
        retrieved = retriever.invoke(job_offer_text)  
    except AttributeError:
        retrieved = retriever.get_relevant_documents(job_offer_text)  

  
    seen, ordered_docs = set(), []
    for d in priority_docs + retrieved:
        key = d.page_content.strip()
        if key and key not in seen:
            seen.add(key)
            ordered_docs.append(d)

 
    context_text = "\n\n".join(d.page_content for d in ordered_docs)
    MAX_CTX_CHARS = 20000
    if len(context_text) > MAX_CTX_CHARS:
        context_text = context_text[:MAX_CTX_CHARS]


    job_offer_text = _to_text(job_offer_text).strip()
    context_text   = _to_text(context_text).strip()

    logger.info(
        "Prompt vars check: input_len=%s, context_len=%s, input_type=%s, context_type=%s",
        len(job_offer_text), len(context_text),
        type(job_offer_text).__name__, type(context_text).__name__,
    )

    if not job_offer_text:
        raise ValueError("INVALID_PROMPT_INPUT: empty job_offer_text (vérifie _build_offer_description(offre))")
    if not context_text:
        context_text = "Aucun extrait pertinent n'a pu être extrait du CV."

    llm = make_llm()
    chain = PROMPT | llm | StrOutputParser()

    logger.info("PROMPT vars: %s", PROMPT.input_variables)
    logger.info("len(input)=%s len(context_text)=%s", len(job_offer_text or ""), len(context_text or ""))
    print("=== SCHEMA ATTENDU POUR LA SORTIE IA ===\n" + SCHEMA_EXPECTED)
    try:
        raw = chain.invoke({"input": job_offer_text, "context": context_text})
        logger.info("RAW model output (first 800): %s", str(raw)[:800])
    except Exception:
        logger.exception("Prompt error during LLM invoke")
        raise


    try:
        out: Dict[str, Any] = _lenient_json_load(str(raw))
    except Exception as e:
        logger.error("Model JSON parse failed: %s\nRaw (first 1200): %s", e, str(raw)[:1200])
        raise ValueError(f"Invalid model JSON: {e}")
    decision = str(out.get("decision", "")).strip()
    scores   = out.get("match_scores", {}) or {}
    missing  = out.get("missing_requirements", []) or []
    evidence = out.get("evidence", {}) or {}
    notes    = out.get("notes", "") or ""
    logger.info(
    "AI decision=%s | overall=%s | scores=%s",
    decision, scores.get("overall"), scores
)


    logger.info("AI missing_requirements (%d): %s",
            len(missing), json.dumps(missing, ensure_ascii=False)[:600])


    preview = {
    "skills": (evidence.get("skills") or [])[:3],
    "education": (evidence.get("education") or [])[:3],
    "experience": (evidence.get("experience") or [])[:3],
}
    logger.info("AI evidence (preview): %s", json.dumps(preview, ensure_ascii=False))

    logger.info("AI notes: %s", notes if notes else "<vide>")


    try:
        vs.delete(where={"resume_id": resume_id})
    except Exception:
        pass

    return out








def _strip_code_fences(s: str) -> str:
    """Retire les blocs Markdown ``` ... ``` ou ```json ... ```."""
    t = s.strip()
    if t.startswith("```"):
        nl = t.find("\n")
        if nl != -1:
            t = t[nl + 1:]
        if t.endswith("```"):
            t = t[:-3]
    return t.strip()

def _extract_first_json_object(s: str) -> Optional[str]:
    """Extrait le premier objet JSON équilibré { ... } sans regex récursive (gère quotes/escapes)."""
    in_str = False
    esc = False
    depth = 0
    start = -1
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
            continue
        else:
            if ch == '"':
                in_str = True
            elif ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start != -1:
                        return s[start:i + 1]
    return None

def _lenient_json_load(raw: str) -> Dict[str, Any]:
    """
    1) enlève ```json ... ```
    2) essaie json.loads direct
    3) sinon, extrait le premier objet JSON équilibré et le parse
    """
    txt = _strip_code_fences(raw)
    try:
        return json.loads(txt)
    except Exception:
        pass
    blk = _extract_first_json_object(txt)
    if blk is not None:
        return json.loads(blk)
    raise ValueError("No valid JSON object found in model output")

def _to_text(x) -> str:
    """Force toute entrée en str (évite INVALID_PROMPT_INPUT)."""
    if x is None:
        return ""
    if isinstance(x, bytes):
        try:
            return x.decode("utf-8", "ignore")
        except Exception:
            return x.decode(errors="ignore")
    if isinstance(x, str):
        return x
    try:
        return str(x)
    except Exception:
        return json.dumps(x, ensure_ascii=False)




