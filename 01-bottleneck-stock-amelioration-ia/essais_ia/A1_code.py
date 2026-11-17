"""
Contrôle qualité des données : erp.xlsx, web.xlsx, liaison.xlsx

Usage : python controle_qualite.py
Prérequis : pip install pandas openpyxl

Le script affiche les problèmes trouvés dans la console et les exporte
dans rapport_qualite.xlsx (une feuille de synthèse + une feuille par problème).
Le numéro "ligne_excel" correspond à la ligne dans le fichier Excel d'origine
(ligne 1 = en-tête).
"""

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paramètres
# ---------------------------------------------------------------------------
DOSSIER = Path(".")
FICHIERS = {
    "erp": DOSSIER / "erp.xlsx",
    "web": DOSSIER / "web.xlsx",
    "liaison": DOSSIER / "liaison.xlsx",
}
COLONNES_ATTENDUES = {
    "erp": ["product_id", "onsale_web", "price", "stock_quantity",
            "stock_status", "purchase_price"],
    "web": ["sku", "virtual", "downloadable", "rating_count", "average_rating",
            "total_sales", "tax_status", "tax_class", "post_author", "post_date",
            "post_date_gmt", "post_content", "product_type", "post_title",
            "post_excerpt", "post_status", "comment_status", "ping_status",
            "post_password", "post_name", "post_modified", "post_modified_gmt",
            "post_content_filtered", "post_parent", "guid", "menu_order",
            "post_type", "post_mime_type", "comment_count"],
    "liaison": ["id_web", "product_id"],
}
# Valeurs autorisées : à ajuster si votre ERP utilise d'autres libellés
STATUTS_STOCK = {"instock", "outofstock"}
# Écart maximal toléré entre une date locale et sa version GMT (France : 1 h ou 2 h)
ECART_GMT_MAX = pd.Timedelta(hours=2)
# Colonnes de texte long, exclues des aperçus et de l'export
TEXTE_LIBRE = {"post_content", "post_excerpt", "post_content_filtered"}
MAX_EXEMPLES = 5
EXPORT = DOSSIER / "rapport_qualite.xlsx"

PROBLEMES = []


# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------
def titre(texte):
    print("\n" + "=" * 80 + f"\n{texte}\n" + "=" * 80)


def signaler(fichier, controle, lignes, colonnes=None, gravite="erreur",
             apercu=MAX_EXEMPLES):
    """Enregistre et affiche un problème s'il concerne au moins une ligne."""
    if lignes is None or len(lignes) == 0:
        return
    PROBLEMES.append({"fichier": fichier, "gravite": gravite,
                      "controle": controle, "nb": len(lignes), "lignes": lignes})
    print(f"\n[{gravite.upper()}] {fichier} — {controle} : {len(lignes)} ligne(s)")
    if colonnes:
        colonnes = [c for c in ["ligne_excel"] + colonnes if c in lignes.columns]
        colonnes = list(dict.fromkeys(colonnes))
        vue = lignes[colonnes]
    else:
        vue = lignes.drop(columns=[c for c in TEXTE_LIBRE | {"cle"}
                                   if c in lignes.columns])
    print(vue.head(apercu).to_string(index=False) if apercu else vue.to_string(index=False))


def colonne(df, nom):
    """Renvoie la colonne si elle existe, sinon une série vide (évite les KeyError)."""
    return df[nom] if nom in df.columns else pd.Series(None, index=df.index, dtype=object)


def norm_cle(serie):
    """Normalise un identifiant : 4054.0 -> '4054', espaces retirés, vide -> None."""
    def f(v):
        if pd.isna(v):
            return None
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        v = str(v).strip()
        return v or None
    return serie.map(f)


def numerique(df, nom, fichier):
    """Convertit une colonne en nombre et signale les valeurs non numériques."""
    brut = colonne(df, nom)
    conv = pd.to_numeric(brut, errors="coerce")
    signaler(fichier, f"{nom} : valeur non numérique",
             df[brut.notna() & conv.isna()], [nom])
    return conv


def atypiques(serie):
    """Valeurs hors de [Q1 - 1,5 IQR ; Q3 + 1,5 IQR]."""
    q1, q3 = serie.quantile([0.25, 0.75])
    iqr = q3 - q1
    return (serie < q1 - 1.5 * iqr) | (serie > q3 + 1.5 * iqr)


def charger(nom, chemin):
    df = pd.read_excel(chemin)
    df.columns = df.columns.astype(str).str.strip()
    df.insert(0, "ligne_excel", range(2, len(df) + 2))
    return df


# ---------------------------------------------------------------------------
# Contrôles communs aux trois fichiers
# ---------------------------------------------------------------------------
def controles_generiques(nom, df):
    titre(f"{nom.upper()} — contrôles généraux")
    donnees = [c for c in df.columns if c != "ligne_excel"]
    print(f"{len(df)} lignes, {len(donnees)} colonnes")

    attendues = COLONNES_ATTENDUES[nom]
    manquantes = [c for c in attendues if c not in df.columns]
    en_trop = [c for c in donnees if c not in attendues]
    signaler(nom, "Colonnes attendues absentes",
             pd.DataFrame({"colonne": manquantes}), apercu=None)
    signaler(nom, "Colonnes non prévues", pd.DataFrame({"colonne": en_trop}),
             gravite="info", apercu=None)

    if len(df) == 0:
        signaler(nom, "Fichier vide", pd.DataFrame({"fichier": [nom]}))
        return

    signaler(nom, "Lignes entièrement dupliquées",
             df[df.duplicated(subset=donnees, keep=False)])

    nb_na = df[donnees].isna().sum()
    table_na = pd.DataFrame({"colonne": nb_na.index, "manquantes": nb_na.values,
                             "pct": (nb_na.values / len(df) * 100).round(1)})
    table_na = table_na[table_na["manquantes"] > 0].sort_values("manquantes",
                                                                ascending=False)
    signaler(nom, "Valeurs manquantes par colonne", table_na,
             gravite="info", apercu=None)

    vides = [c for c in donnees if df[c].isna().all()]
    signaler(nom, "Colonnes entièrement vides", pd.DataFrame({"colonne": vides}),
             gravite="avertissement", apercu=None)

    constantes = [c for c in donnees
                  if c not in vides and df[c].nunique(dropna=True) == 1]
    signaler(nom, "Colonnes à valeur unique (peu informatives)",
             pd.DataFrame({"colonne": constantes,
                           "valeur": [df[c].dropna().iloc[0] for c in constantes]}),
             gravite="info", apercu=None)

    for c in df[donnees].select_dtypes(include="object").columns:
        if c in TEXTE_LIBRE:
            continue
        texte = df[c].dropna()
        texte = texte[texte.map(lambda v: isinstance(v, str))]
        mal = texte[texte != texte.str.strip()]
        signaler(nom, f"{c} : espaces en début ou fin de valeur",
                 df.loc[mal.index], [c], gravite="avertissement")


# ---------------------------------------------------------------------------
# ERP
# ---------------------------------------------------------------------------
def controles_erp(erp):
    f = "erp"
    titre("ERP — contrôles métier")
    erp["cle"] = norm_cle(colonne(erp, "product_id"))
    cle = erp["cle"]

    signaler(f, "product_id manquant", erp[cle.isna()])
    signaler(f, "product_id en double",
             erp[cle.notna() & cle.duplicated(keep=False)].sort_values("cle"),
             ["product_id", "price", "stock_quantity", "stock_status"])

    onsale = numerique(erp, "onsale_web", f)
    signaler(f, "onsale_web différent de 0 ou 1",
             erp[onsale.notna() & ~onsale.isin([0, 1])], ["product_id", "onsale_web"])

    prix = numerique(erp, "price", f)
    achat = numerique(erp, "purchase_price", f)
    qte = numerique(erp, "stock_quantity", f)

    signaler(f, "price manquant", erp[prix.isna()], ["product_id", "price"])
    signaler(f, "price négatif ou nul", erp[prix <= 0], ["product_id", "price"])
    signaler(f, "purchase_price manquant", erp[achat.isna()],
             ["product_id", "purchase_price"])
    signaler(f, "purchase_price négatif ou nul", erp[achat <= 0],
             ["product_id", "purchase_price"])
    signaler(f, "Prix de vente inférieur au prix d'achat (marge négative)",
             erp[prix < achat], ["product_id", "price", "purchase_price"])

    signaler(f, "stock_quantity négatif", erp[qte < 0],
             ["product_id", "stock_quantity", "stock_status"])
    signaler(f, "stock_quantity non entier", erp[qte.notna() & (qte % 1 != 0)],
             ["product_id", "stock_quantity"])

    statut = colonne(erp, "stock_status").fillna("").astype(str).str.strip().str.lower()
    print("\nRépartition de stock_status :")
    print(statut.replace("", "<vide>").value_counts().to_string())
    signaler(f, "stock_status manquant", erp[statut == ""],
             ["product_id", "stock_quantity", "stock_status"])
    signaler(f, f"stock_status hors des valeurs {sorted(STATUTS_STOCK)}",
             erp[(statut != "") & ~statut.isin(STATUTS_STOCK)],
             ["product_id", "stock_status"])
    signaler(f, "Stock positif mais statut 'outofstock'",
             erp[(qte > 0) & (statut == "outofstock")],
             ["product_id", "stock_quantity", "stock_status"])
    signaler(f, "Stock nul ou négatif mais statut 'instock'",
             erp[(qte <= 0) & (statut == "instock")],
             ["product_id", "stock_quantity", "stock_status"])

    signaler(f, "price atypique (méthode IQR, à vérifier)",
             erp[atypiques(prix)].sort_values("price", ascending=False),
             ["product_id", "price", "purchase_price"], gravite="avertissement")
    signaler(f, "stock_quantity atypique (méthode IQR, à vérifier)",
             erp[atypiques(qte)].sort_values("stock_quantity", ascending=False),
             ["product_id", "stock_quantity"], gravite="avertissement")


# ---------------------------------------------------------------------------
# WEB
# ---------------------------------------------------------------------------
def controles_web(web):
    f = "web"
    titre("WEB — contrôles métier")
    web["cle"] = norm_cle(colonne(web, "sku"))
    sku = web["cle"]
    ptype = colonne(web, "post_type").fillna("<vide>").astype(str)
    apercu_cols = ["sku", "post_title", "post_type"]

    for c in ["post_type", "post_status", "product_type", "tax_status",
              "tax_class", "comment_status", "ping_status"]:
        if c in web.columns:
            print(f"\nRépartition de {c} :")
            print(web[c].fillna("<vide>").value_counts().to_string())

    signaler(f, "sku manquant", web[sku.isna()], apercu_cols + ["post_status"])

    doublon_meme_type = sku.notna() & pd.Series(
        list(zip(sku, ptype)), index=web.index).duplicated(keep=False)
    signaler(f, "sku en double pour un même post_type",
             web[doublon_meme_type].sort_values("cle"), apercu_cols)
    signaler(f, "sku présent sous plusieurs post_type (ex. product + attachment)",
             web[sku.notna() & sku.duplicated(keep=False) & ~doublon_meme_type]
             .sort_values("cle"), apercu_cols, gravite="avertissement")
    signaler(f, "sku non numérique (format différent des autres)",
             web[sku.notna() & ~sku.str.fullmatch(r"\d+", na=False)],
             apercu_cols, gravite="avertissement")

    for c in ["virtual", "downloadable"]:
        val = numerique(web, c, f)
        signaler(f, f"{c} différent de 0 ou 1",
                 web[val.notna() & ~val.isin([0, 1])], ["sku", c])

    nb_avis = numerique(web, "rating_count", f)
    note = numerique(web, "average_rating", f)
    ventes = numerique(web, "total_sales", f)
    nb_com = numerique(web, "comment_count", f)
    signaler(f, "rating_count négatif", web[nb_avis < 0], ["sku", "rating_count"])
    signaler(f, "average_rating hors de [0 ; 5]", web[(note < 0) | (note > 5)],
             ["sku", "average_rating"])
    signaler(f, "Note moyenne > 0 sans aucun avis",
             web[(note > 0) & (nb_avis == 0)], ["sku", "rating_count", "average_rating"])
    signaler(f, "total_sales négatif", web[ventes < 0], ["sku", "total_sales"])
    signaler(f, "comment_count négatif", web[nb_com < 0], ["sku", "comment_count"])

    dates = {}
    for c in ["post_date", "post_date_gmt", "post_modified", "post_modified_gmt"]:
        brut = colonne(web, c)
        dates[c] = pd.to_datetime(brut, errors="coerce")
        signaler(f, f"{c} : date illisible",
                 web[brut.notna() & dates[c].isna()], ["sku", c])
        signaler(f, f"{c} : date dans le futur",
                 web[dates[c] > pd.Timestamp.now()], ["sku", c],
                 gravite="avertissement")
    signaler(f, "post_modified antérieure à post_date",
             web[dates["post_modified"] < dates["post_date"]],
             ["sku", "post_date", "post_modified"])
    for local, gmt in [("post_date", "post_date_gmt"),
                       ("post_modified", "post_modified_gmt")]:
        signaler(f, f"Écart anormal entre {local} et {gmt} (> {ECART_GMT_MAX})",
                 web[(dates[local] - dates[gmt]).abs() > ECART_GMT_MAX],
                 ["sku", local, gmt], gravite="avertissement")

    produits = ptype == "product"
    titres = colonne(web, "post_title")
    signaler(f, "post_title manquant", web[titres.isna()], apercu_cols)
    nom_url = colonne(web, "post_name")
    signaler(f, "post_name (slug) en double parmi les produits",
             web[produits & nom_url.notna() & nom_url.duplicated(keep=False)]
             .sort_values("post_name"), ["sku", "post_name", "post_title"])
    guid = colonne(web, "guid")
    signaler(f, "guid en double", web[guid.notna() & guid.duplicated(keep=False)]
             .sort_values("guid"), ["sku", "guid", "post_type"])


# ---------------------------------------------------------------------------
# LIAISON + cohérence entre fichiers
# ---------------------------------------------------------------------------
def controles_liaison(liaison, erp, web):
    f = "liaison"
    titre("LIAISON et cohérence entre fichiers")
    lp = norm_cle(colonne(liaison, "product_id"))
    lw = norm_cle(colonne(liaison, "id_web"))
    cols = ["product_id", "id_web"]

    signaler(f, "product_id manquant", liaison[lp.isna()], cols)
    signaler(f, "product_id en double", liaison[lp.notna() & lp.duplicated(keep=False)]
             .sort_values("product_id"), cols)
    signaler(f, "id_web en double (un produit web relié à plusieurs product_id)",
             liaison[lw.notna() & lw.duplicated(keep=False)].sort_values("id_web"), cols)
    signaler(f, "id_web manquant (produit sans correspondance web)",
             liaison[lw.isna()], cols, gravite="info")

    ids_erp = set(erp["cle"].dropna())
    skus_web = set(web["cle"].dropna())
    signaler(f, "product_id absent de l'ERP",
             liaison[lp.notna() & ~lp.isin(ids_erp)], cols)
    signaler(f, "id_web absent du fichier web",
             liaison[lw.notna() & ~lw.isin(skus_web)], cols)
    signaler("erp", "product_id absent de la table de liaison",
             erp[erp["cle"].notna() & ~erp["cle"].isin(set(lp.dropna()))],
             ["product_id", "onsale_web"])
    signaler("web", "sku absent de la table de liaison",
             web[web["cle"].notna() & ~web["cle"].isin(set(lw.dropna()))],
             ["sku", "post_title", "post_type"])

    correspondance = (pd.DataFrame({"pid": lp, "web": lw})
                      .dropna(subset=["pid"]).drop_duplicates("pid")
                      .set_index("pid")["web"])
    a_un_id_web = erp["cle"].map(correspondance).notna()
    onsale = pd.to_numeric(colonne(erp, "onsale_web"), errors="coerce")
    signaler("erp", "En vente web (onsale_web = 1) mais sans id_web",
             erp[(onsale == 1) & ~a_un_id_web], ["product_id", "onsale_web"])
    signaler("erp", "Hors vente web (onsale_web = 0) mais avec un id_web",
             erp[(onsale == 0) & a_un_id_web], ["product_id", "onsale_web"],
             gravite="avertissement")


# ---------------------------------------------------------------------------
# Synthèse et export
# ---------------------------------------------------------------------------
def synthese():
    titre("SYNTHÈSE")
    if not PROBLEMES:
        print("Aucun problème détecté.")
        return
    ordre = {"erreur": 0, "avertissement": 1, "info": 2}
    resume = pd.DataFrame([{k: p[k] for k in ("fichier", "gravite", "controle", "nb")}
                           for p in PROBLEMES])
    resume["n°"] = range(1, len(resume) + 1)
    resume = resume.sort_values(["gravite", "fichier"],
                                key=lambda s: s.map(ordre) if s.name == "gravite" else s)
    print(resume[["n°", "fichier", "gravite", "controle", "nb"]].to_string(index=False))
    print("\nTotal :", resume["gravite"].value_counts().to_dict())

    try:
        with pd.ExcelWriter(EXPORT) as w:
            resume.to_excel(w, sheet_name="synthese", index=False)
            for i, p in enumerate(PROBLEMES, 1):
                detail = p["lignes"].drop(columns=[c for c in TEXTE_LIBRE | {"cle"}
                                                   if c in p["lignes"].columns])
                detail.to_excel(w, sheet_name=f"{i:02d}_{p['fichier']}"[:31], index=False)
        print(f"\nRapport détaillé exporté : {EXPORT.resolve()}")
    except Exception as e:  # export facultatif : la console reste la sortie principale
        print(f"\nExport Excel impossible ({e}) ; les résultats restent affichés ci-dessus.")


def main():
    pd.set_option("display.max_colwidth", 60)
    pd.set_option("display.width", 200)

    dfs = {}
    for nom, chemin in FICHIERS.items():
        try:
            dfs[nom] = charger(nom, chemin)
        except FileNotFoundError:
            print(f"Fichier introuvable : {chemin.resolve()}")
            return

    for nom, df in dfs.items():
        controles_generiques(nom, df)

    controles_erp(dfs["erp"])
    controles_web(dfs["web"])
    controles_liaison(dfs["liaison"], dfs["erp"], dfs["web"])
    synthese()


if __name__ == "__main__":
    main()
