"""
Contrôle qualité des extractions mensuelles (ERP, site web, table de liaison),
à lancer avant l'analyse du chiffre d'affaires, du stock et de la marge.

Usage :
    import pandas as pd
    from controle_qualite import controle_qualite

    erp = pd.read_excel("erp.xlsx")
    web = pd.read_excel("web.xlsx")
    liaison = pd.read_excel("liaison.xlsx")

    recap = controle_qualite(erp, web, liaison)
    # ou, pour récupérer toutes les lignes en anomalie :
    recap, details = controle_qualite(erp, web, liaison, retourner_details=True)
    details["ERP - product_id dupliqué"]   # DataFrame complet

Gravités :
    bloquant     -> fausse directement le CA, le stock ou la marge si on ne corrige pas
    à vérifier   -> peut être normal, mais demande une décision humaine
    information  -> à connaître (lignes à exclure, périmètre), pas une erreur en soi
"""

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Paramètres de structure
# --------------------------------------------------------------------------
COLONNES_ERP = ["product_id", "onsale_web", "price", "stock_quantity",
                "stock_status", "purchase_price"]
COLONNES_WEB = ["sku", "total_sales", "post_title", "product_type", "post_type",
                "virtual", "downloadable", "rating_count", "average_rating",
                "tax_status", "tax_class", "post_author", "post_date", "post_date_gmt",
                "post_content", "post_excerpt", "post_status", "comment_status",
                "ping_status", "post_password", "post_name", "post_modified",
                "post_modified_gmt", "post_content_filtered", "post_parent", "guid",
                "menu_order", "post_mime_type", "comment_count"]
# Colonnes web réellement utilisées par les contrôles (les autres sont seulement vérifiées)
COLONNES_WEB_UTILES = ["sku", "total_sales", "post_type", "post_status"]
COLONNES_LIAISON = ["id_web", "product_id"]
STATUTS_STOCK = {"instock", "outofstock"}


# --------------------------------------------------------------------------
# Outils internes
# --------------------------------------------------------------------------
def _cle(serie):
    """Normalise une clé de jointure : 15298.0 -> '15298', ' abc ' -> 'abc', vide -> NA.
    Nécessaire car Excel/pandas lit souvent un identifiant en float quand la colonne
    contient des vides, ce qui fait échouer les jointures sans erreur visible."""
    def f(v):
        if pd.isna(v):
            return pd.NA
        if isinstance(v, (float, np.floating)) and float(v).is_integer():
            v = int(v)
        v = str(v).strip()
        return v if v != "" else pd.NA
    return serie.map(f).astype("string")


def _num(serie):
    return pd.to_numeric(serie, errors="coerce")


def _a(df, colonnes):
    return all(c in df.columns for c in colonnes)


class _Journal:
    def __init__(self, n_exemples):
        self.lignes, self.details, self.n = [], {}, n_exemples

    def ajouter(self, controle, fichier, gravite, explication, anomalies, colonnes=None):
        if colonnes is not None:
            anomalies = anomalies[[c for c in colonnes if c in anomalies.columns]]
        ex = anomalies.head(self.n).reset_index()
        exemples = " | ".join(
            ", ".join(f"{k}={v}" for k, v in rec.items()) for rec in ex.to_dict("records")
        )
        self.lignes.append({"controle": controle, "fichier": fichier, "gravite": gravite,
                            "nb_anomalies": len(anomalies), "exemples": exemples,
                            "explication": explication})
        self.details[controle] = anomalies

    def non_execute(self, controle, fichier, explication, raison):
        self.lignes.append({"controle": controle, "fichier": fichier, "gravite": "non exécuté",
                            "nb_anomalies": np.nan, "exemples": f"Non exécuté : {raison}",
                            "explication": explication})


# --------------------------------------------------------------------------
# Fonction principale
# --------------------------------------------------------------------------
def controle_qualite(erp, web, liaison, taux_tva=None, post_types_produit=("product",),
                     n_exemples=5, iqr_k=1.5, retourner_details=False):
    """
    Paramètres
    ----------
    erp, web, liaison : DataFrames lus depuis les trois fichiers.
    taux_tva : float ou None. Si renseigné (ex. 0.20), ajoute un contrôle de marge HT
        négative. Laissé à None par défaut : le taux applicable n'est pas dans les données.
    post_types_produit : valeurs de post_type considérées comme des fiches produit.
        Dans WooCommerce, 'product' = fiche produit ; 'attachment' = média (image) ;
        'product_variation' = variante. Adapter si vous vendez des variantes.
    n_exemples : nombre d'exemples affichés par contrôle.
    iqr_k : sévérité du repérage des prix atypiques (1.5 = règle de Tukey classique).
    retourner_details : si True, renvoie aussi un dict {contrôle: DataFrame complet}.

    Les index affichés dans les exemples sont les index pandas : ligne Excel = index + 2
    si le fichier a une seule ligne d'en-tête et a été lu sans index_col.
    """
    j = _Journal(n_exemples)
    erp, web, liaison = erp.copy(), web.copy(), liaison.copy()

    # ======================================================================
    # 0. Structure
    # ======================================================================
    for nom, df, attendues, utiles in [
        ("erp", erp, COLONNES_ERP, COLONNES_ERP),
        ("web", web, COLONNES_WEB, COLONNES_WEB_UTILES),
        ("liaison", liaison, COLONNES_LIAISON, COLONNES_LIAISON),
    ]:
        manquantes = [c for c in attendues if c not in df.columns]
        bloquantes = [c for c in manquantes if c in utiles]
        j.ajouter(f"{nom.upper()} - colonnes manquantes", nom,
                  "bloquant" if bloquantes else "information",
                  "Vérifie que l'export a la structure attendue ; une colonne manquante "
                  "signale un changement d'export et désactive les contrôles qui en dépendent.",
                  pd.DataFrame({"colonne_manquante": manquantes,
                                "utilisee_par_les_controles": [c in utiles for c in manquantes]}))
        j.ajouter(f"{nom.upper()} - lignes entièrement vides", nom, "information",
                  "Repère les lignes sans aucune valeur, à retirer avant tout calcul "
                  "pour ne pas gonfler les comptages.",
                  df[df.isna().all(axis=1)])

    # ======================================================================
    # 1. ERP
    # ======================================================================
    if "product_id" in erp.columns:
        erp["_cle"] = _cle(erp["product_id"])
        j.ajouter("ERP - product_id manquant", "erp", "bloquant",
                  "Un produit sans identifiant ne peut être relié ni au site ni à ses ventes.",
                  erp[erp["_cle"].isna()], COLONNES_ERP)
        j.ajouter("ERP - product_id dupliqué", "erp", "bloquant",
                  "Un identifiant en double multiplie les ventes et le stock lors des jointures "
                  "et rend le prix ou le coût ambigu.",
                  erp[erp["_cle"].notna() & erp["_cle"].duplicated(keep=False)]
                  .sort_values("_cle"), COLONNES_ERP)

    for col in ["onsale_web", "price", "stock_quantity", "purchase_price"]:
        if col in erp.columns:
            brut = erp[col]
            j.ajouter(f"ERP - {col} non numérique", "erp", "bloquant",
                      f"Une valeur texte dans {col} (virgule décimale, symbole €, espace) "
                      "est perdue silencieusement dans les calculs.",
                      erp[brut.notna() & _num(brut).isna()], ["product_id", col])
            erp[f"_{col}"] = _num(brut)

    if "_price" in erp.columns:
        j.ajouter("ERP - prix de vente manquant ou ≤ 0", "erp", "bloquant",
                  "Sans prix de vente valide, le chiffre d'affaires du produit vaut zéro ou est faux.",
                  erp[erp["_price"].isna() | (erp["_price"] <= 0)], COLONNES_ERP)
        p = erp["_price"].dropna()
        p = p[p > 0]
        if len(p) >= 4:
            q1, q3 = p.quantile([0.25, 0.75])
            haut, bas = q3 + iqr_k * (q3 - q1), q1 - iqr_k * (q3 - q1)
            j.ajouter("ERP - prix de vente atypique", "erp", "à vérifier",
                      f"Prix hors de l'intervalle [{bas:.2f} ; {haut:.2f}] (méthode IQR) : peut être "
                      "une erreur de saisie ou un vrai produit haut de gamme, à confirmer car "
                      "ces lignes pèsent fortement sur le CA.",
                      erp[(erp["_price"] > haut) | (erp["_price"] < bas)], COLONNES_ERP)

    if "_purchase_price" in erp.columns:
        j.ajouter("ERP - prix d'achat manquant ou ≤ 0", "erp", "bloquant",
                  "Sans coût d'achat valide, la marge du produit ne peut pas être calculée.",
                  erp[erp["_purchase_price"].isna() | (erp["_purchase_price"] <= 0)], COLONNES_ERP)

    if _a(erp, ["_price", "_purchase_price"]):
        perte = erp["_price"] < erp["_purchase_price"]
        j.ajouter("ERP - prix TTC inférieur au prix d'achat HT", "erp", "bloquant",
                  "Un prix TTC sous le coût HT donne une marge négative quel que soit le taux "
                  "de TVA : erreur de saisie ou vente à perte à justifier.",
                  erp[perte], COLONNES_ERP)
        if taux_tva is not None:
            prix_ht = erp["_price"] / (1 + taux_tva)
            j.ajouter(f"ERP - marge HT négative (TVA supposée {taux_tva:.0%})", "erp", "à vérifier",
                      "Avec le taux de TVA fourni en paramètre, le prix HT est sous le coût d'achat "
                      "(hors cas déjà signalés au contrôle précédent) ; dépend de l'hypothèse de TVA.",
                      erp[(prix_ht < erp["_purchase_price"]) & ~perte], COLONNES_ERP)

    if "_stock_quantity" in erp.columns:
        q = erp["_stock_quantity"]
        j.ajouter("ERP - stock manquant, négatif ou non entier", "erp", "bloquant",
                  "Une quantité absente, négative ou décimale fausse la valorisation du stock.",
                  erp[q.isna() | (q < 0) | (q.notna() & (q % 1 != 0))], COLONNES_ERP)

    if "stock_status" in erp.columns:
        j.ajouter("ERP - stock_status hors valeurs attendues", "erp", "bloquant",
                  "Seuls 'instock' et 'outofstock' sont attendus ; une autre valeur (casse, espace, "
                  "vide) fait sortir le produit des filtres de disponibilité.",
                  erp[~erp["stock_status"].isin(STATUTS_STOCK)], COLONNES_ERP)
        if "_stock_quantity" in erp.columns:
            q, s = erp["_stock_quantity"], erp["stock_status"]
            j.ajouter("ERP - statut de stock incohérent avec la quantité", "erp", "à vérifier",
                      "'instock' avec 0 unité ou 'outofstock' avec des unités : l'une des deux "
                      "colonnes est fausse, et on ne sait pas laquelle croire pour l'analyse du stock.",
                      erp[((s == "instock") & (q <= 0)) | ((s == "outofstock") & (q > 0))],
                      COLONNES_ERP)

    if "_onsale_web" in erp.columns:
        j.ajouter("ERP - onsale_web différent de 0 ou 1", "erp", "bloquant",
                  "Ce drapeau définit le périmètre vendu en ligne ; toute autre valeur rend "
                  "le périmètre de l'analyse ambigu.",
                  erp[~erp["_onsale_web"].isin([0, 1])], COLONNES_ERP)

    # ======================================================================
    # 2. WEB
    # ======================================================================
    if "post_type" in web.columns:
        est_produit = web["post_type"].isin(post_types_produit)
        j.ajouter("WEB - lignes qui ne sont pas des fiches produit", "web", "information",
                  f"Lignes dont post_type n'est pas dans {list(post_types_produit)} (ex. images "
                  "'attachment') : à exclure, sinon chaque produit risque d'être compté deux fois.",
                  web[~est_produit & ~web.isna().all(axis=1)],
                  ["sku", "post_type", "post_title", "total_sales"])
        web_p = web[est_produit].copy()
    else:
        j.non_execute("WEB - lignes qui ne sont pas des fiches produit", "web",
                      "Sépare fiches produit et autres objets WordPress.", "colonne post_type absente")
        web_p = web.copy()

    if "sku" in web.columns:
        web["_cle"] = _cle(web["sku"])
        web_p["_cle"] = _cle(web_p["sku"])
        j.ajouter("WEB - sku manquant (fiches produit)", "web", "bloquant",
                  "Une fiche produit sans sku ne peut pas être reliée à l'ERP : ses ventes "
                  "sortent de l'analyse.",
                  web_p[web_p["_cle"].isna()], ["post_title", "post_type", "total_sales"])
        j.ajouter("WEB - sku dupliqué (fiches produit)", "web", "bloquant",
                  "Deux fiches produit avec le même sku doublent les ventes lors de la jointure.",
                  web_p[web_p["_cle"].notna() & web_p["_cle"].duplicated(keep=False)]
                  .sort_values("_cle"), ["sku", "post_title", "post_type", "total_sales"])
        brut = web["sku"].astype("string")
        j.ajouter("WEB - sku avec espaces parasites", "web", "information",
                  "Des espaces en début ou fin de clé empêchent la jointure ; la fonction les "
                  "neutralise pour ses contrôles, mais votre analyse doit faire de même.",
                  web[brut.notna() & (brut != brut.str.strip())], ["sku", "post_title"])

    if "total_sales" in web_p.columns:
        brut = web_p["total_sales"]
        ts = _num(brut)
        web_p["_ventes"] = ts
        j.ajouter("WEB - total_sales manquant, non numérique, négatif ou non entier", "web",
                  "bloquant",
                  "Les ventes sont des quantités entières positives ; toute autre valeur fausse "
                  "directement le chiffre d'affaires.",
                  web_p[ts.isna() | (ts < 0) | (ts.notna() & (ts % 1 != 0))],
                  ["sku", "post_title", "total_sales"])

    if "post_status" in web_p.columns:
        j.ajouter("WEB - fiches produit non publiées", "web", "information",
                  "Statut différent de 'publish' (brouillon, privé…) : produit invisible en ligne, "
                  "à inclure ou exclure explicitement selon le périmètre voulu.",
                  web_p[web_p["post_status"] != "publish"],
                  ["sku", "post_title", "post_status", "total_sales"])

    # ======================================================================
    # 3. LIAISON
    # ======================================================================
    for col in COLONNES_LIAISON:
        if col in liaison.columns:
            liaison[f"_{col}"] = _cle(liaison[col])
            j.ajouter(f"LIAISON - {col} manquant", "liaison",
                      "bloquant" if col == "product_id" else "à vérifier",
                      f"Une ligne sans {col} ne relie rien : si le produit est vendu en ligne, "
                      "ses ventes ou son coût ne seront pas rapprochés.",
                      liaison[liaison[f"_{col}"].isna()], COLONNES_LIAISON)
            j.ajouter(f"LIAISON - {col} dupliqué", "liaison", "bloquant",
                      "La liaison est supposée un-pour-un (hypothèse à confirmer) ; un doublon "
                      "duplique les lignes lors de la jointure et gonfle CA et stock.",
                      liaison[liaison[f"_{col}"].notna() & liaison[f"_{col}"].duplicated(keep=False)]
                      .sort_values(f"_{col}"), COLONNES_LIAISON)

    # ======================================================================
    # 4. CROISEMENTS
    # ======================================================================
    ok_erp = "_cle" in erp.columns
    ok_web = "_cle" in web_p.columns
    ok_lia = _a(liaison, ["_product_id", "_id_web"])

    if ok_erp and ok_lia:
        cles_erp = set(erp["_cle"].dropna())
        j.ajouter("CROISÉ - product_id de la liaison absent de l'ERP", "liaison→erp", "bloquant",
                  "Le produit vendu en ligne n'a ni prix ni coût ni stock dans l'ERP : sa marge "
                  "et son stock sont impossibles à calculer.",
                  liaison[liaison["_product_id"].notna() & ~liaison["_product_id"].isin(cles_erp)],
                  COLONNES_LIAISON)

        if "_onsale_web" in erp.columns:
            lies = set(liaison.loc[liaison["_id_web"].notna(), "_product_id"].dropna())
            j.ajouter("CROISÉ - produit ERP vendu en ligne sans lien web", "erp→liaison", "bloquant",
                      "onsale_web = 1 mais aucun id_web associé : les ventes de ce produit ne "
                      "pourront pas lui être rattachées.",
                      erp[(erp["_onsale_web"] == 1) & ~erp["_cle"].isin(lies)], COLONNES_ERP)

    if ok_web and ok_lia:
        cles_web = set(web_p["_cle"].dropna())
        cles_lia_web = set(liaison["_id_web"].dropna())
        j.ajouter("CROISÉ - id_web de la liaison absent de l'export web", "liaison→web",
                  "à vérifier",
                  "Le produit est lié mais introuvable parmi les fiches produit du site (supprimé, "
                  "renommé, ou classé dans un autre post_type) : ses ventes du mois seront à zéro.",
                  liaison[liaison["_id_web"].notna() & ~liaison["_id_web"].isin(cles_web)],
                  COLONNES_LIAISON)
        j.ajouter("CROISÉ - sku du site absent de la liaison", "web→liaison", "bloquant",
                  "Fiche produit du site sans correspondance ERP : ses ventes sont comptées dans "
                  "le CA mais sans coût ni stock, ou perdues à la jointure.",
                  web_p[web_p["_cle"].notna() & ~web_p["_cle"].isin(cles_lia_web)],
                  ["sku", "post_title", "total_sales"])

    if ok_erp and ok_web and ok_lia and "_ventes" in web_p.columns:
        # Liaison dédoublonnée pour éviter de compter deux fois (doublons déjà signalés)
        lien = (liaison.dropna(subset=["_id_web", "_product_id"])
                .drop_duplicates("_id_web")[["_id_web", "_product_id"]])
        ref = erp.drop_duplicates("_cle").set_index("_cle")
        vendus = web_p[web_p["_ventes"] > 0].merge(lien, left_on="_cle", right_on="_id_web")
        vendus = vendus[vendus["_product_id"].isin(ref.index)]
        for col in ["_price", "_purchase_price", "_onsale_web"]:
            if col in ref.columns:
                vendus[col] = vendus["_product_id"].map(ref[col])

        if "_price" in vendus.columns:
            j.ajouter("CROISÉ - produit vendu sans prix ERP valide", "web→erp", "bloquant",
                      "Le produit a des ventes ce mois-ci mais un prix manquant ou nul : "
                      "le CA calculé sera sous-estimé.",
                      vendus[vendus["_price"].isna() | (vendus["_price"] <= 0)],
                      ["sku", "_product_id", "post_title", "total_sales", "_price"])
        if "_onsale_web" in vendus.columns:
            j.ajouter("CROISÉ - produit vendu en ligne mais onsale_web ≠ 1", "web→erp",
                      "à vérifier",
                      "Des ventes web existent alors que l'ERP dit le produit non vendu en ligne : "
                      "le drapeau est faux ou le produit a été retiré en cours de mois.",
                      vendus[vendus["_onsale_web"] != 1],
                      ["sku", "_product_id", "post_title", "total_sales", "_onsale_web"])

    recap = pd.DataFrame(j.lignes)
    ordre = {"bloquant": 0, "à vérifier": 1, "information": 2, "non exécuté": 3}
    recap = (recap.assign(_o=recap["gravite"].map(ordre))
             .sort_values(["_o", "nb_anomalies"], ascending=[True, False])
             .drop(columns="_o").reset_index(drop=True))
    return (recap, j.details) if retourner_details else recap
