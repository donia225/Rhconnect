import os, json, joblib, numpy as np, torch
from transformers import BertTokenizer, BertModel
import tempfile
from typing import Optional
import pandas as pd
import PyPDF2
from docx import Document  # pip install python-docx
import re
from datetime import datetime
import pdfplumber

# Dossier des artefacts
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BERT_DIR = _THIS_DIR

# Charger configs/artefacts
_CFG = json.load(open(os.path.join(_BERT_DIR, "bert_config.json")))
_HF_NAME = _CFG.get("hf_model_name", "bert-base-uncased")
_MAXLEN  = int(_CFG.get("max_length", 128))

_TOKENIZER = BertTokenizer.from_pretrained(_HF_NAME)
_BERT      = BertModel.from_pretrained(_HF_NAME)
_BERT.eval()  # eval mode

_SCALER = joblib.load(os.path.join(_BERT_DIR, "num_scaler.pkl"))
_CLF    = joblib.load(os.path.join(_BERT_DIR, "bert_logreg.pkl"))
_LE     = joblib.load(os.path.join(_BERT_DIR, "label_encoder.pkl"))



# --- .doc (legacy) : nécessite textract (et catdoc/antiword selon OS)
try:
    import textract  # pip install textract
    _HAS_TEXTRACT = True
except Exception:
    _HAS_TEXTRACT = False


def _clean_text(text: str) -> str:
    """Nettoie les espaces/retraits multiples et normalise le texte."""
    if not text:
        return ""
    # Remplace les \r par \n, condense les espaces, strip
    text = text.replace("\r", "\n")
    # Supprime les doublons d'espaces et de nouvelles lignes
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# Charger FR puis fallback EN une seule fois
try:
    import spacy
    _NLP = spacy.load("fr_core_news_md")
except Exception:
    try:
        import spacy
        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        _NLP = None  # au cas où spaCy n'est pas dispo


def _read_pdf_text(path_pdf: str) -> str:
    """Retourne le texte concaténé de toutes les pages."""
    parts = []
    with pdfplumber.open(path_pdf) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t:
                parts.append(t)
    return "\n".join(parts)


def _normalize_whitespace(s: str) -> str:
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{2,}", "\n", s)).strip()


def extract_skills_from_cv(path_pdf: str) -> list[str]:
    # 1) lire le texte brut du PDF
    raw = _read_pdf_text(path_pdf) or ""
    if not raw:
        return []

    txt = raw.replace("\xa0", " ")
    # 2) isoler la section compétences (FR/EN)
    sec_re = re.compile(
        r"(comp[eé]tences(?:\s+techniques)?|skills|technical\s+skills)\s*:?\s*(.*?)"
        r"(?=\n\s*(formation|exp[eé]rience|experience|education|projets?|projects?)\b|$)",
        flags=re.IGNORECASE | re.DOTALL
    )
    blocks = [m.group(2) for m in sec_re.finditer(txt)]
    if not blocks:
        # si on ne trouve pas la section, on travaille sur tout le texte (dégradé)
        blocks = [txt]

    # 3) pattern qui accepte lettres/chiffres/symboles tech
    tech_pat = re.compile(
        r"""
        (?:
            [A-Za-z][A-Za-z0-9\+\#\.\-]{1,}      # ReactJS, TypeScript, .NET, Node.js, C++, C#, HTML5, CSS3
            (?:\s+[A-Za-z][A-Za-z0-9\+\#\.\-]{1,})*  # Spring Boot, Open Stack (on normalisera ensuite)
        )
        """,
        re.VERBOSE
    )

    # 4) mots à ignorer (trop génériques)
    blacklist = {
        "competence", "compétence", "competences", "compétences",
        "technique", "techniques", "technologies", "technologie",
        "developpement", "développement", "logiciel", "logiciels",
        "outils", "outil", "cloud", "langues", "profil", "resume", "cv"
    }

    found, seen = [], set()

    for block in blocks:
        # nettoyer les puces et séparer
        b = block.replace("•", " ").replace("·", " ").replace("|", " ")
        # récupérer toutes les “technos” possibles
        for m in tech_pat.finditer(b):
            token = m.group(0).strip()

            # normalisations légères
            token = re.sub(r"\s{2,}", " ", token)           # espaces multiples -> 1
            token = token.replace("Open Stack", "OpenStack")
            token = token.replace("React Js", "ReactJS")
            token = token.replace("Node Js", "Node.js")
            token = token.replace("SpringBoot", "Spring Boot")

            low = token.lower().strip(" .,")

            # filtrer les génériques et trop courts (sauf C/R)
            if low in blacklist:
                continue
            if len(low) < 2 and token not in {"C", "R"}:
                continue

            if low not in seen:
                seen.add(low)
                found.append(token.strip(" ,."))

    return found[:100]





# ---------- Mapping mois FR/EN ----------
_MONTHS = {
    "jan":1, "janv":1, "janvier":1, "january":1,
    "feb":2, "fev":2, "févr":2, "fevrier":2, "février":2, "february":2,
    "mar":3, "mars":3, "march":3,
    "apr":4, "avr":4, "avril":4, "april":4,
    "may":5, "mai":5,
    "jun":6, "juin":6, "june":6,
    "jul":7, "juil":7, "july":7,
    "aug":8, "aout":8, "août":8, "august":8,
    "sep":9, "sept":9, "septembre":9, "september":9,
    "oct":10, "octobre":10, "october":10,
    "nov":11, "novembre":11, "november":11,
    "dec":12, "decembre":12, "décembre":12, "december":12,
    # tolérance points/accents abrégés
    "jan.":1, "feb.":2, "mar.":3, "apr.":4, "jun.":6, "jul.":7, "aug.":8, "sep.":9, "oct.":10, "nov.":11, "dec.":12,
    "janv.":1, "févr.":2, "avr.":4, "juil.":7
}

def _month_from(s: str) -> int | None:
    s = (s or "").strip().lower()
    s = s.replace("é", "e").replace("û", "u").replace("ô", "o").replace("à", "a").replace("è", "e")
    return _MONTHS.get(s) or _MONTHS.get(s[:3])

def _clamp_years(x: float, lo=0, hi=50) -> int:
    return max(lo, min(hi, int(round(x))))

# ---------- Estimation depuis du texte ----------
def infer_experience_years_from_text(text: str) -> int:
    """
    Estime les années d'expérience à partir du texte d’un CV.
    - Récupère les intervalles datés (mois+année — mois+année / mois—mois année / année—année)
    - Ignore les intervalles dont le contexte ressemble à de la formation/éducation
    - Fusionne les intervalles qui se chevauchent ou sont contigus
    - N'utilise le fallback "X ans" que si aucun intervalle n'a été trouvé
    """
    if not text:
        return 0

    t = text.lower()
    now = datetime.utcnow()
    now_y, now_m = now.year, now.month

    def months_between(y1, m1, y2, m2):
        return max(0, (y2 - y1) * 12 + (m2 - m1))

    # --- petits utilitaires ---
    def looks_like_education(context: str) -> bool:
        edu_kw = (
            "formation", "éducation", "education", "dipl", "licence", "bachelor",
            "master", "msc", "universit", "école", "school", "certificat", "certification"
        )
        c = context.lower()
        return any(k in c for k in edu_kw)

    def add_span(spans, y1, m1, y2, m2, ctx):
        # bornes plausibles
        if not (1950 <= y1 <= now_y and 1 <= m1 <= 12): 
            return
        if m2 < 1 or m2 > 12: 
            return
        if y2 < y1 or (y2 == y1 and m2 < m1):
            return
        # ignore formation
        if looks_like_education(ctx):
            return
        spans.append((y1, m1, y2, m2))

    spans = []

    # 1) "Jan 2019 – Mar 2023" ou "Juil 2018 – présent"
    pat_m_y_m_y = re.compile(
        r"(?P<m1>[a-zéû\.]{3,12})\s+(?P<y1>19\d{2}|20\d{2})\s*[–\-]\s*"
        r"(?P<m2>[a-zéû\.]{3,12}|present|current|now|aujourd'hui|actuel|présent)"
        r"(?:\s*(?P<y2>19\d{2}|20\d{2}))?",
        re.IGNORECASE
    )
    for m in pat_m_y_m_y.finditer(t):
        mo1 = _month_from(m.group("m1"))
        if not mo1:
            continue
        y1 = int(m.group("y1"))
        m2 = m.group("m2")
        if m2 in {"present", "current", "now", "aujourd'hui", "actuel", "présent"}:
            y2, mo2 = now_y, now_m
        else:
            mo2 = _month_from(m2)
            if not mo2:
                continue
            y2 = int(m.group("y2")) if m.group("y2") else y1
        ctx = t[max(0, m.start()-60): m.end()+60]
        add_span(spans, y1, mo1, y2, mo2, ctx)

    # 2) "Juin – Août 2023" (mois — mois année)
    pat_m_m_y = re.compile(
        r"(?P<m1>[a-zéû\.]{3,12})\s*[–\-]\s*(?P<m2>[a-zéû\.]{3,12})\s+(?P<y2>19\d{2}|20\d{2})",
        re.IGNORECASE
    )
    for m in pat_m_m_y.finditer(t):
        mo1 = _month_from(m.group("m1"))
        mo2 = _month_from(m.group("m2"))
        if not (mo1 and mo2):
            continue
        y2 = int(m.group("y2"))
        y1 = y2 if mo1 <= mo2 else y2 - 1
        ctx = t[max(0, m.start()-60): m.end()+60]
        add_span(spans, y1, mo1, y2, mo2, ctx)

    # 3) "2018 – 2022" ou "2017 – présent"
    #    On n’ajoute ces plages que si aucun intervalle mois/année ne couvre déjà l’intervalle,
    #    pour limiter le double comptage.
    pat_y_y = re.compile(
        r"(?P<y1>19\d{2}|20\d{2})\s*[–\-]\s*(?P<y2>19\d{2}|20\d{2}|present|current|now|aujourd'hui|actuel|présent)",
        re.IGNORECASE
    )
    for m in pat_y_y.finditer(t):
        y1 = int(m.group("y1"))
        g2 = m.group("y2")
        y2 = now_y if g2 in {"present", "current", "now", "aujourd'hui", "actuel", "présent"} else int(g2)
        ctx = t[max(0, m.start()-60): m.end()+60]
        # on met comme mois [Jan, Déc] pour approx
        # mais on n’ajoute que si ça n’est pas déjà largement couvert par un span existant
        cand = (y1, 1, y2, 12)
        if not any(
            (y1 > sy1 or (y1 == sy1 and 1 >= sm1)) and
            (y2 < sy2 or (y2 == sy2 and 12 <= sm2))
            for (sy1, sm1, sy2, sm2) in spans
        ):
            add_span(spans, *cand, ctx=ctx)

    # Aucune plage trouvée → fallback "X ans"
    if not spans:
        total_years = 0.0
        for m in re.finditer(r"(\d{1,2})\s*\+?\s*(?:ans?|annees?|years?)", t):
            try:
                total_years += float(m.group(1))
            except Exception:
                pass
        return _clamp_years(total_years, lo=0, hi=50)

    # --- fusion des intervalles qui se chevauchent/ se touchent ---
    # on convertit tout en "mois absolus" pour simplifier
    def to_abs_month(y, m): return y * 12 + (m - 1)

    intervals = sorted((to_abs_month(y1, m1), to_abs_month(y2, m2)) for (y1, m1, y2, m2) in spans)

    merged = []
    for s, e in intervals:
        if not merged:
            merged.append([s, e])
        else:
            ps, pe = merged[-1]
            # marge de 1 mois pour coller les intervalles contigus/qui se chevauchent
            if s <= pe + 1:
                merged[-1][1] = max(pe, e)
            else:
                merged.append([s, e])

    total_months = sum(e - s + 1 for s, e in merged)  # +1 pour inclure le mois de fin
    years = total_months / 12.0
    return _clamp_years(years, lo=0, hi=50)



# ---------- Wrapper PDF ----------
def infer_experience_years_from_cv(path_pdf: str) -> int:
    """Lit un PDF et renvoie l’estimation des années d’expérience."""
    return infer_experience_years_from_text(_read_pdf_text(path_pdf))



def extract_text_from_docx(docx_path: str) -> str:
    doc = Document(docx_path)
    paras = [p.text for p in doc.paragraphs if p.text]
    return _clean_text("\n".join(paras))


def extract_text_from_doc(doc_path: str) -> str:
    if not _HAS_TEXTRACT:
        raise ImportError(
            "Extraction .doc indisponible : installez 'textract' et ses dépendances "
            "(ex. 'antiword' ou 'catdoc' selon le système)."
        )
    raw = textract.process(doc_path)  # retourne bytes
    return _clean_text(raw.decode("utf-8", errors="ignore"))


# ------------------ API principale ------------------

def extract_text_from_file(path: str) -> str:
    """
    Retourne le texte extrait du fichier (pdf/docx/doc).
    Lève ValueError si extension non supportée.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
          return _read_pdf_text(path)
    if ext == ".docx":
        return extract_text_from_docx(path)
    if ext == ".doc":
        return extract_text_from_doc(path)
    raise ValueError(f"Extension non supportée : {ext}. Formats acceptés : .pdf, .docx, .doc")


def extract_text_from_uploaded_file(django_file, *, fallback_ext: Optional[str] = None) -> str:
    """
    Pour un fichier uploadé (InMemoryUploadedFile / TemporaryUploadedFile).
    Écrit un fichier temporaire et appelle extract_text_from_file.
    - fallback_ext : '.pdf' / '.docx' / '.doc' au cas où le nom n'a pas d'extension.
    """
    # Déduire l'extension depuis le nom ou le content_type
    name = getattr(django_file, "name", "") or ""
    ext = os.path.splitext(name)[1].lower()
    if not ext and fallback_ext:
        ext = fallback_ext.lower()

    if not ext:
        # Essai via content_type
        ctype = getattr(django_file, "content_type", "").lower()
        mapping = {
            "application/pdf": ".pdf",
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        }
        ext = mapping.get(ctype, "")

    if ext not in {".pdf", ".docx", ".doc"}:
        raise ValueError("Impossible de déterminer le type de fichier. "
                         "Formats acceptés : .pdf, .docx, .doc")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        for chunk in django_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        return extract_text_from_file(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
@torch.no_grad()
def _embed_cls(text: str) -> np.ndarray:
    """
    Embedding BERT du token [CLS] pour un texte (shape = 768,)
    """
    if not text:
        text = ""
    inputs = _TOKENIZER(text, return_tensors='pt', truncation=True, padding=True, max_length=_MAXLEN)
    outputs = _BERT(**inputs)
    cls_vec = outputs.last_hidden_state[:, 0, :].squeeze(0).cpu().numpy()  # (768,)
    return cls_vec

# =====================  PREDICTIONS  =====================


def predict_from_pdf(path_pdf: str, projects_count: int = 0) -> dict:
    """
    Prédit en lisant DIRECTEMENT le PDF:
    - Extrait le texte et les compétences depuis le fichier
    - Estime les années d'expérience
    - Concatène BERT + features numériques et prédit
    """
    try:
        # 1) lire texte brut
        cv_text = _read_pdf_text(path_pdf)
    except Exception:
        cv_text = ""

    # 2) extraire compétences directement du PDF
    skills = extract_skills_from_cv(path_pdf)

    # 3) extraire années d’expérience depuis le texte
    exp_years = infer_experience_years_from_text(cv_text)

    # 4) embedding BERT sur les compétences (ou texte complet si vide)
    skills_text = ", ".join(skills) if skills else cv_text
    emb = _embed_cls(skills_text)

    # 5) features numériques (expérience + projects_count)
    cols = getattr(_SCALER, 'feature_names_in_', ['Experience (Years)', 'Projects Count'])
    num_df = pd.DataFrame([[int(exp_years), int(projects_count)]], columns=cols)
    num = _SCALER.transform(num_df)

    X = np.hstack([emb.reshape(1, -1), num])

    # 6) prédiction
    label_id = int(_CLF.predict(X)[0])
    proba = float(_CLF.predict_proba(X)[0, label_id]) if hasattr(_CLF, "predict_proba") else None
    label_text = _LE.inverse_transform([label_id])[0]
    mapping = {"Reject": 0, "Hire": 1}
    label_int = mapping.get(label_text, 0)

    return {
        "label": label_int,
        "label_text": label_text,
        "proba": proba,
        "extracted_skills": skills,
        "exp_years": int(exp_years),
    }
