def analyser_cv(path_pdf: str, competences_attendues: list[str]) -> float:
    import pdfplumber
    import spacy
    nlp = spacy.load("fr_core_news_sm")
    
    with pdfplumber.open(path_pdf) as pdf:
        texte = ''.join([page.extract_text() for page in pdf.pages if page.extract_text()])
    doc = nlp(texte.lower())
    tokens = set([token.lemma_ for token in doc if token.is_alpha])
    nb_matchs = len(set(competences_attendues) & tokens)
    score = round((nb_matchs / len(competences_attendues)) * 100, 2)
    return score
