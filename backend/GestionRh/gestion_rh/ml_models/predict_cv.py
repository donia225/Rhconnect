import os, json, joblib, numpy as np, torch
from transformers import BertTokenizer, BertModel
import tempfile
from typing import Optional
import pandas as pd
import PyPDF2
from docx import Document  # pip install python-docx
import re, unicodedata
from datetime import datetime
import pdfplumber
import math

#Dossier des artefacts
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BERT_DIR = _THIS_DIR

#Chargement des configs/artefacts
_CFG = json.load(open(os.path.join(_BERT_DIR, "bert_config.json")))
_HF_NAME = _CFG.get("hf_model_name", "bert-base-uncased")
_MAXLEN  = int(_CFG.get("max_length", 128))

_TOKENIZER = BertTokenizer.from_pretrained(_HF_NAME)
_BERT      = BertModel.from_pretrained(_HF_NAME)
_BERT.eval()  # eval mode

_SCALER = joblib.load(os.path.join(_BERT_DIR, "num_scaler.pkl"))
_CLF    = joblib.load(os.path.join(_BERT_DIR, "bert_logreg.pkl"))
_LE     = joblib.load(os.path.join(_BERT_DIR, "label_encoder.pkl"))



try:
    import textract
    _HAS_TEXTRACT = True
except Exception:
    _HAS_TEXTRACT = False

def _degree_rank(text: str) -> int:
    t = (text or "").lower()
    if re.search(r"\b(ph\.?\s*d|doctorat|doctorate)\b", t): return 4
    if re.search(r"\b(master|mast[eè]re|ing[ée]nieur|bac\+5|m\.?eng|b\.?eng)\b", t): return 3
    if re.search(r"\b(licence|bachelor|bac\+3|bac\+4)\b", t): return 2
    if re.search(r"\b(bts|dut|deust|bac\+2)\b", t): return 1
    return 0

def _exp_bucket_and_phrase(years) -> tuple[str, str]:
    try:
        y = float(years)
    except Exception:
    #mapping experience
     y = 0.0
    if y <= 0:   return "aucune",        "aucune"
    if y < 1:    return "moins_1_an",    "moins de 1 an"
    if y < 2:    return "entre_1_2_ans", "1 à 2 ans"
    if y < 5:    return "entre_2_5_ans", "2 à 5 ans"
    if y < 10:   return "entre_5_10_ans","5 à 10 ans"
    return "plus_10_ans", "plus de 10 ans"

def _strip_accents(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")

    #extraction education du texte de cv
_EDU_PATTERNS_NORM = [
    # PhD / Doctorat
    (r"\b(ph\.?\s*d|doctorat|doctorate)\b", "PhD / Doctorat"),
    # MBA
    (r"\b(mba|master\s+of\s+business\s+administration)\b", "MBA"),
    # Diplôme d'ingénieur & variantes (y compris 'cycle d'ingenieur' / 'ecole d'ingenieur')
    (r"\b(diplome\s+d['’]?\s*ingenieur|ingeniorat|ing\.\b|b\.?\s?eng\b|m\.?\s?eng\b|"
     r"master\s+of\s+engineering|cycle\s+d['’]?\s*ingenieur|ecole\s+(?:superieure\s+)?d['’]?\s*ingenieurs?)\b",
     "Diplôme d'ingénieur (Bac+5)"),
    # Master / Maîtrise / Mastère / MSc
    (r"\b(master(?:'s)?|msc|maitrise|mastere)\b", "Master"),
    # Licence / Bachelor (+ pro/app/fonda) – Bac+3/4
    (r"\b(bachelor|licence(?:\s+(?:pro|professionnelle|appliquee|fondamentale))?|bac\+3|bac\+4)\b",
     "Licence / Bachelor"),
    # Bac+2 (BTS/DUT/DEUST/IUT/BTP)
    (r"\b(dut|iut|deust|bts|btp|brevet\s+de\s+technicien(?:\s+superieur)?)\b",
     "Bac+2 (BTS/DUT/DEUST)"),
    # Classes préparatoires
    (r"\b(cpge|classes?\s+preparatoires?|prepa)\b", "Classes préparatoires"),
    # Secondaire
    (r"\b(bac(?:calaureat)?|baccalaureat|high\s*school|secondary\s+school|lycee)\b", "Bac"),
]

_BAC_PLUS_NORM = [
    (r"\bbac\s*\+\s*5\b", "Bac+5 (Master/Ingénieur)"),
    (r"\bbac\s*\+\s*4\b", "Bac+4"),
    (r"\bbac\s*\+\s*3\b", "Bac+3 (Licence)"),
    (r"\bbac\s*\+\s*2\b", "Bac+2 (BTS/DUT)"),
]

def _extract_education_phrase_from_text(text: str, debug: bool = False) -> str:
    """
    Détecte le plus haut niveau d'étude présent dans le CV.
    - Normalisation Unicode + nettoyage séparateurs
    - Recherche dans la zone 'Formation' puis fallback global
    - Motifs robustes pour ingénieur/ingénierie, licence, master, PhD, bac+X, etc.
    """
    if not text:
        return ""

    # 1) normalisation Unicode + minuscules
    t = (text
         .replace("\u2019", "'").replace("\u2018", "'").replace("\u201B", "'")
         .replace("\xa0", " "))
    # retire les accents (NFD -> drop Mn), conserve ponctuation
    t_norm = _strip_accents(t.lower())

    # 2) remplace séparateurs exotiques par espaces + compaction
    def _clean(s: str) -> str:
        s = re.sub(r"[|•·/–—]+", " ", s)           # unify separators
        s = re.sub(r"\s+", " ", s)                 # collapse spaces
        return s.strip()

    t_norm = _clean(t_norm)

    # 3) extraire une zone 'formation' si possible (on prend le GROUPE capturé)
    head = re.search(
        r"(?:\bformation\b|\beducation\b|parcours\s+academique|\betudes?)\s*[:\-]?\s*([\s\S]{0,5000})",
        t_norm, flags=re.IGNORECASE
    )
    zone = _clean(head.group(1)) if head else ""

    if debug:
        sample = zone[:400] if zone else t_norm[:400]
        print("DEBUG[EDU] HEAD_FOUND:", bool(head), "| SAMPLE:", sample)

    # 4) motifs ordonnés (du plus haut au plus bas)
    EDU_PAT = [
        (r"\b(ph\.?\s*d|doctorat|doctorate)\b", "PhD / Doctorat"),
        (r"\bmba\b|\bmaster\s+of\s+business\s+administration\b", "MBA"),
        # Ingénieur & Ingénierie (cycle / diplôme / école d'…)
        (r"\b(cycle\s+d['’]?\s*ingenieur|diplome\s+d['’]?\s*ingenieur|"
         r"ecole\s+(?:superieure\s+)?d['’]?\s*ingenieur(?:s)?|"
         r"d['’]?\s*ingenierie)\b", "Diplôme d'ingénieur (Bac+5)"),
        (r"\b(master|maitrise|mastere|msc)\b", "Master"),
        (r"\b(licence|bachelor|bac\+3|bac\+4)\b", "Licence / Bachelor"),
        (r"\b(bts|dut|deust|bac\+2)\b", "Bac+2 (BTS/DUT/DEUST)"),
        (r"\b(cpge|classes?\s+preparatoires?|prepa)\b", "Classes préparatoires"),
        (r"\b(bac(?:calaureat)?|baccalaureat|lycee|high\s*school|secondary\s+school)\b", "Bac"),
    ]

    # 5) cherche d'abord dans la zone Formation (si trouvée), sinon dans tout le texte
    lookup_spaces = (zone if zone else t_norm)
    for pat, label in EDU_PAT:
        if re.search(pat, lookup_spaces, flags=re.IGNORECASE):
            return label

    # 6) dernier fallback : mentions explicites Bac+X (n’importe où)
    for pat, label in [
        (r"\bbac\s*\+\s*5\b", "Bac+5 (Master/Ingénieur)"),
        (r"\bbac\s*\+\s*4\b", "Bac+4"),
        (r"\bbac\s*\+\s*3\b", "Bac+3 (Licence)"),
        (r"\bbac\s*\+\s*2\b", "Bac+2 (BTS/DUT/DEUST)"),
    ]:
        if re.search(pat, t_norm, flags=re.IGNORECASE):
            return label

    return ""


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


# Chargement FR puis fallback EN une seule fois
try:
    import spacy
    _NLP = spacy.load("fr_core_news_md")
except Exception:
    try:
        import spacy
        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        _NLP = None


def _read_pdf_text(path_pdf: str) -> str:
    """elle retourne le texte concaténé de toutes les pages."""
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
    raw = _read_pdf_text(path_pdf) or ""
    if not raw:
        return []

    # --- 1) normalisation de base (PDF -> texte)
    txt = (raw.replace("\xa0", " ")
              .replace("\u2019", "'").replace("\u2018", "'").replace("\u201B", "'"))
    # séparateurs exotiques -> espace ; compaction
    txt = re.sub(r"[|•·/–—]+", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()

    # version sans accents pour repérer les entêtes
    norm = _strip_accents(txt.lower())

    # --- 2) isoler la section Compétences/Skills
    m = re.search(
        r"(?:\bcompetences?\b|\bskills?\b|technical\s+skills?)\s*[:\-]?\s*(.*?)"
        r"(?=\b(formation|educa|experience|exp[ée]riences?|projets?|projects?|langues?)\b|$)",
        norm, flags=re.IGNORECASE | re.DOTALL
    )
    zone = txt if not m else txt[m.start(1):m.end(1)]

    # --- 3) dictionnaire de technos + heuristiques
    WHITELIST = {
        # langages
        "c", "c++", "c#", "java", "python", "javascript", "typescript", "go", "rust", "php", "ruby",
        # web / frameworks
        "react", "reactjs", "angular", "node.js", "nodejs", "django", "spring", "springboot", ".net", "asp.net",
        # bdd / data
        "sql", "mysql", "postgres", "oracle", "nosql", "mongodb", "redis",
        # pratiques/outils fréquents
        "uml", "git", "scrum", "agile", "docker", "kubernetes", "ansible", "jenkins", "sonarqube", "grafana", "prometheus"
    }
    CANON = {
        "react js": "ReactJS", "reactjs": "ReactJS",
        "node js": "Node.js", "nodejs": "Node.js",
        "springboot": "Spring Boot", "spring boot": "Spring Boot",
        "asp.net": "ASP.NET", ".net": ".NET",
        "typescript": "TypeScript", "javascript": "JavaScript",
    }

    def canon(tok: str) -> str:
        low = _strip_accents(tok.lower())
        return CANON.get(low, tok)

    # tokens tech : au moins une lettre, et souvent un symbole/num
    CAND_RE = re.compile(r"[A-Za-z][A-Za-z0-9\+\#\.\-]{0,}(?:\s+[A-Za-z][A-Za-z0-9\+\#\.\-]{0,})*")

    STOPWORDS = {
        "competence","competences","technique","techniques","technologies","technologie",
        "developpement","développement","logiciel","logiciels","outils","outil",
        "experience","experiences","professionnelle","professionnelles","formation",
        "ingenieur","ingenierie","projet","projets","langues","profil","resume","cv",
        "present","janv","fev","mars","avr","mai","juin","juil","aout","sept","oct","nov","dec"
    }

    found, seen = [], set()
    for m in CAND_RE.finditer(zone):
        tok = m.group(0).strip(" ,.;:/()[]")
        if not tok:
            continue
        low = _strip_accents(tok.lower())

        # heuristique : garder si (dans la whitelist)
        # OU s'il contient un caractère typique tech (+, #, ., chiffre)
        # OU s'il ressemble à une techno connue en 2 mots (react js / node js)
        keep = (
            low in WHITELIST
            or bool(re.search(r"[\+\#\.\d]", tok))
            or low in CANON
        )
        if not keep:
            continue
        if low in STOPWORDS:
            continue

        key = low
        if key not in seen:
            seen.add(key)
            found.append(canon(tok))

    # --- 4) rattrapage explicite pour le langage "C" (souvent perdu)
    if re.search(r"(?<![a-z0-9])c(?![a-z0-9])", _strip_accents(zone.lower())):
        if "C" not in found and "c" not in seen:
            found.insert(0, "C")

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

def _build_offer_description(offre) -> str:
    """
    Texte sémantique de l'offre UNIQUEMENT :
    - titre / description libre
    - required skills
    (PAS d'années ni de diplôme ici)
    """
    def _as_text(x):
        if x is None: return ""
        try:
            if hasattr(x, "all"):
                return ", ".join(map(str, x.all()))
        except Exception:
            pass
        if isinstance(x, (list, tuple, set)):
            return ", ".join(map(str, x))
        return str(x)

    title = _as_text(getattr(offre, "titre", "")) or _as_text(getattr(offre, "job_title", ""))
    desc  = _as_text(getattr(offre, "description", "")) or _as_text(getattr(offre, "details", ""))

    skills_offer = (
        _as_text(getattr(offre, "competences", "")) or
        _as_text(getattr(offre, "skills", "")) or
        _as_text(getattr(offre, "competences_requises", ""))
    )

    parts = []
    if title:  parts.append(title)
    if desc:   parts.append(desc)
    if skills_offer: parts.append(f"required skills: {skills_offer}")
    return " — ".join([p for p in parts if p]).strip()



def _cosine_sim(u: np.ndarray, v: np.ndarray, eps: float = 1e-8) -> float:
    num = float(np.dot(u, v))
    den = (np.linalg.norm(u) * np.linalg.norm(v)) + eps
    return num / den

def _top_skill_sims(skills_list, offer_description, topn: int = 15):
    """
    Retourne les top-n similarités (skill CV ↔ description d'offre) triées décroissantes.
    Format: [(sim, "skill"), ...]
    NB: coûteux (1 embedding BERT par skill) → à utiliser en debug uniquement.
    """
    if not offer_description or not skills_list:
        return []
    emb_offer = _embed_cls(offer_description)
    rows = []
    for s in skills_list or []:
        s = (s or "").strip()
        if not s:
            continue
        sim = float(_cosine_sim(_embed_cls(s), emb_offer))
        rows.append((sim, s))
    rows.sort(key=lambda x: x[0], reverse=True)
    return rows[:topn]


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

def predict_from_pdf_with_offer(path_pdf: str,
                                offre_obj=None,
                                offer_description: str | None = None,
                                projects_count: int = 0,
                                debug_topn: int = 0,
                                debug_print: bool = False):
    """
    Inférence alignée sur l'entraînement 'offer-aware':
      X = [emb_cv | emb_offer | cos(skills,desc) | num_scaled(Years, Projects, EduRank)]
    """
    # ---- 1) Lire texte + extractions CV ----
    try:
        cv_text = _read_pdf_text(path_pdf) or ""
    except Exception:
        cv_text = ""
    skills = extract_skills_from_cv(path_pdf)
    exp_years = infer_experience_years_from_text(cv_text)
    edu_phrase = _extract_education_phrase_from_text(cv_text)
    edu_rank = _degree_rank(edu_phrase)

    # ---- 2) Description d'offre sémantique ----
    if offer_description is None:
        offer_description = _build_offer_description(offre_obj) if offre_obj is not None else ""

    # ---- 3) Embeddings + cosinus principal ----
    skills_text = ", ".join(skills) if skills else cv_text
    emb_cv    = _embed_cls(skills_text)         # (768,)
    emb_offer = _embed_cls(offer_description)   # (768,)
    cos_sk_desc = _cosine_sim(emb_cv, emb_offer)

    # ---- 4) Numériques -> scaler (même colonnes/ordre qu'au train) ----
    cols = getattr(_SCALER, 'feature_names_in_', ['Experience (Years)', 'Projects Count', 'EduRank'])
    num_df = pd.DataFrame(
        [[int(exp_years), int(projects_count), float(edu_rank)]],
        columns=cols
    )
    num = _SCALER.transform(num_df)  # (1,3)

    # ---- 5) Concat EXACTEMENT comme au train ----
    X = np.hstack([
        emb_cv.reshape(1, -1),               # 768
        emb_offer.reshape(1, -1),            # 768
        np.array([[float(cos_sk_desc)]], float),  # 1
        num                                  # 3   => 1540
    ])

    # ---- 6) Prédiction ----
    label_id = int(_CLF.predict(X)[0])
    proba = float(_CLF.predict_proba(X)[0, label_id]) if hasattr(_CLF, "predict_proba") else None
    label_text = _LE.inverse_transform([label_id])[0]
    mapping = {"Reject": 0, "Hire": 1}
    label_int = mapping.get(label_text, 0)

    # ---- 7) Sortie ----
    out = {
        "label": label_int,
        "label_text": label_text,
        "proba": proba,
        "extracted_skills": skills,
        "exp_years": int(exp_years),
        "edu_phrase": edu_phrase,
        "edu_rank": int(edu_rank),
        "cos_sim_skills_desc": float(cos_sk_desc),
        "offer_description_used": offer_description
    }
    if debug_print and debug_topn > 0:
        out["top_skill_sims"] = _top_skill_sims(skills, offer_description, topn=debug_topn)
    return out
