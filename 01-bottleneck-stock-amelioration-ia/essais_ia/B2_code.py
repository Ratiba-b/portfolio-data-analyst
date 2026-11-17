"""
Contrôle qualité des extractions mensuelles (ERP, site WooCommerce, table de liaison)
à lancer avant toute analyse de chiffre d'affaires, de stock ou de marge.

Usage :
    import pandas as pd
    from controle_qualite import controle_qualite

    erp = pd.read_excel("erp.xlsx")
    web = pd.read_excel("web.xlsx")
    liaison = pd.read_excel("liaison.xlsx")

    recap = controle_qualite(erp, web, liaison)
    recap, details = controle_qualite(erp, web, liaison, retourner_details=True)
    details["ERP - product_id en doublon"]   # lignes complètes en anomalie

Hypothèses (paramétrables ou signalées dans le récapitulatif) :
- taux_tva = 20 % (taux normal français sur les vins et spiritueux) : sert seulement
  à comparer prix de vente TTC et prix d'achat HT. À ajuster si une partie du
  catalogue relève d'un autre taux.
- Les lignes produit du site sont celles dont post_type vaut "product" ou
  "product_variation" (valeurs standard de WooCommerce) ; les autres
  (ex. "attachment" pour les images) sont comptées mais exclues des contrôles croisés.
- « ligne » = numéro de ligne dans le fichier Excel, si le DataFrame a été lu avec
  pd.read_excel sans filtrage ni réindexation (index 0 = ligne 2 sous l'en-tête).
"""

import pandas as pd

COLONNES_ATTENDUES = {
    "ERP": ["product_id", "onsale_web", "price", "stock_quantity", "stock_status", "purchase_price"],
    "WEB": ["sku", "total_sales", "post_title", "post_type", "post_status"],
    "LIAISON": ["id_web", "product_id"],
}
TYPES_PRODUIT_WOO = {"product", "product_variation"}
STATUTS_STOCK = {"instock", "outofstock"}
ORDRE_GRAVITE = {"bloquant": 0, "à vérifier": 1, "info": 2}


def _normaliser_cle(serie):
    """Met les identifiants au même format texte : Excel lit souvent 4954 en 4954.0,
    et un sku numérique d'un côté ne joindrait pas le même sku texte de l'autre."""
    def conv(v):
        if pd.isna(v):
            return pd.NA
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        s = str(v).strip()
        return s if s else pd.NA
    return serie.map(conv).astype("string")


def controle_qualite(erp, web, liaison, taux_tva=0.20, n_exemples=5, retourner_details=False):
    erp, web, liaison = erp.copy(), web.copy(), liaison.copy()
    resultats, details = [], {}

    def ajouter(nom, perimetre, gravite, anomalies, cle, explication):
        if len(anomalies):
            exemples = "; ".join(
                f"ligne {l} : {cle}={v}"
                for l, v in zip(anomalies["_ligne"].head(n_exemples),
                                anomalies[cle].astype("string").fillna("(vide)").head(n_exemples))
            )
        else:
            exemples = ""
        resultats.append({
            "controle": nom, "perimetre": perimetre, "gravite": gravite,
            "nb_lignes_anomalie": len(anomalies), "exemples": exemples,
            "explication": explication,
        })
        details[nom] = anomalies.drop(columns="_ligne", errors="ignore")

    def recap():
        df = pd.DataFrame(resultats)
        df["_o"] = df["gravite"].map(ORDRE_GRAVITE)
        df = df.sort_values(["_o", "nb_lignes_anomalie"], ascending=[True, False]).drop(columns="_o")
        df = df.reset_index(drop=True)
        return (df, details) if retourner_details else df

    # --- 0. Structure : sans les colonnes attendues, aucun autre contrôle n'est fiable
    manque = False
    for nom, df in (("ERP", erp), ("WEB", web), ("LIAISON", liaison)):
        absentes = [c for c in COLONNES_ATTENDUES[nom] if c not in df.columns]
        if absentes:
            manque = True
            resultats.append({
                "controle": f"{nom} - colonnes manquantes", "perimetre": nom, "gravite": "bloquant",
                "nb_lignes_anomalie": len(df), "exemples": ", ".join(absentes),
                "explication": "Une colonne absente ou renommée dans l'export rend les contrôles "
                               "et l'analyse impossibles ; arrêt avant les autres contrôles.",
            })
    if manque:
        return recap()

    for df in (erp, web, liaison):
        df["_ligne"] = df.index + 2

    erp["product_id"] = _normaliser_cle(erp["product_id"])
    liaison["product_id"] = _normaliser_cle(liaison["product_id"])
    liaison["id_web"] = _normaliser_cle(liaison["id_web"])
    web["sku"] = _normaliser_cle(web["sku"])

    price = pd.to_numeric(erp["price"], errors="coerce")
    achat = pd.to_numeric(erp["purchase_price"], errors="coerce")
    qte = pd.to_numeric(erp["stock_quantity"], errors="coerce")
    onsale = pd.to_numeric(erp["onsale_web"], errors="coerce")
    statut = erp["stock_status"].astype("string").str.strip().str.lower()

    # --- 1. ERP
    ajouter("ERP - product_id manquant", "ERP", "bloquant",
            erp[erp["product_id"].isna()], "product_id",
            "Un produit sans identifiant ne peut être relié ni aux ventes ni à la liaison.")
    ajouter("ERP - product_id en doublon", "ERP", "bloquant",
            erp[erp["product_id"].notna() & erp["product_id"].duplicated(keep=False)], "product_id",
            "Un identifiant présent deux fois double le stock et les ventes lors des jointures.")
    ajouter("ERP - onsale_web hors 0/1", "ERP", "bloquant",
            erp[~onsale.isin([0, 1])], "onsale_web",
            "Ce drapeau définit le périmètre « vendu en ligne » ; une autre valeur le rend ambigu.")
    ajouter("ERP - prix de vente manquant ou ≤ 0", "ERP", "bloquant",
            erp[price.isna() | (price <= 0)], "product_id",
            "Le prix de vente sert à calculer le CA ; une valeur absente, nulle ou non numérique le fausse.")
    ajouter("ERP - prix d'achat manquant ou ≤ 0", "ERP", "bloquant",
            erp[achat.isna() | (achat <= 0)], "product_id",
            "Sans prix d'achat valide, la marge du produit ne peut pas être calculée.")
    ajouter("ERP - prix de vente TTC < prix d'achat HT", "ERP", "à vérifier",
            erp[(price > 0) & (achat > 0) & (price < achat)], "product_id",
            "Le produit est vendu à perte même avant TVA : erreur de saisie probable ou déstockage à confirmer.")
    ht = price / (1 + taux_tva)
    ajouter(f"ERP - prix HT (TVA {taux_tva:.0%}) < prix d'achat HT", "ERP", "à vérifier",
            erp[(price >= achat) & (ht < achat) & (achat > 0)], "product_id",
            "Une fois la TVA retirée, la marge devient négative ; dépend du taux de TVA supposé.")
    ajouter("ERP - stock manquant, négatif ou non entier", "ERP", "bloquant",
            erp[qte.isna() | (qte < 0) | (qte % 1 != 0)], "product_id",
            "Une quantité de stock invalide fausse la valorisation du stock et les ruptures.")
    ajouter("ERP - stock_status hors instock/outofstock", "ERP", "bloquant",
            erp[~statut.isin(STATUTS_STOCK).fillna(False)], "stock_status",
            "Un statut inconnu empêche de classer le produit en stock ou en rupture.")
    ajouter("ERP - statut de stock incohérent avec la quantité", "ERP", "à vérifier",
            erp[((qte > 0) & (statut == "outofstock")) | ((qte <= 0) & (statut == "instock"))],
            "product_id",
            "Statut et quantité se contredisent : l'une des deux colonnes est fausse "
            "(ou le site autorise les précommandes, à confirmer).")
    p_ok = price[price > 0]
    if len(p_ok) >= 4:
        q1, q3 = p_ok.quantile([0.25, 0.75])
        borne_haute, borne_basse = q3 + 1.5 * (q3 - q1), q1 - 1.5 * (q3 - q1)
        ajouter("ERP - prix atypique (méthode IQR)", "ERP", "info",
                erp[(price > borne_haute) | ((price > 0) & (price < borne_basse))], "product_id",
                "Un prix très éloigné des autres peut être une erreur de saisie ou un produit premium "
                "réel ; il pèse fortement sur le CA et doit être vérifié à la main.")

    # --- 2. WEB
    est_produit = web["post_type"].astype("string").str.strip().isin(TYPES_PRODUIT_WOO).fillna(False)
    ajouter("WEB - lignes qui ne sont pas des produits", "WEB", "info",
            web[~est_produit], "post_type",
            "WooCommerce exporte aussi d'autres contenus (images…) ; ils sont exclus des contrôles "
            "croisés pour ne pas compter deux fois un produit.")
    wp = web[est_produit]
    ventes = pd.to_numeric(wp["total_sales"], errors="coerce")
    ajouter("WEB - lignes entièrement dupliquées", "WEB", "bloquant",
            web[web.drop(columns="_ligne").duplicated(keep=False)], "sku",
            "Une ligne exportée deux fois double les ventes du mois.")
    ajouter("WEB - sku manquant (lignes produit)", "WEB", "bloquant",
            wp[wp["sku"].isna()], "post_title",
            "Sans sku, les ventes du produit ne peuvent pas être rattachées à l'ERP.")
    ajouter("WEB - sku en doublon (lignes produit)", "WEB", "bloquant",
            wp[wp["sku"].notna() & wp["sku"].duplicated(keep=False)], "sku",
            "Deux lignes produit avec le même sku doublent les ventes à la jointure.")
    ajouter("WEB - total_sales manquant, négatif ou non entier", "WEB", "bloquant",
            wp[ventes.isna() | (ventes < 0) | (ventes % 1 != 0)], "sku",
            "Le volume vendu est la base du CA ; une valeur invalide le fausse.")
    ajouter("WEB - produit non publié", "WEB", "info",
            wp[wp["post_status"].astype("string").str.strip() != "publish"], "sku",
            "Un produit en brouillon ou privé n'est pas visible ; utile pour expliquer une absence de ventes.")

    # --- 3. LIAISON
    ajouter("LIAISON - product_id manquant", "LIAISON", "bloquant",
            liaison[liaison["product_id"].isna()], "id_web",
            "Une liaison sans identifiant ERP ne relie rien.")
    ajouter("LIAISON - id_web manquant", "LIAISON", "à vérifier",
            liaison[liaison["id_web"].isna()], "product_id",
            "Le produit ERP n'a pas de référence site : normal s'il n'est pas vendu en ligne, "
            "anomalie sinon (voir contrôle croisé).")
    ajouter("LIAISON - product_id en doublon", "LIAISON", "bloquant",
            liaison[liaison["product_id"].notna() & liaison["product_id"].duplicated(keep=False)],
            "product_id",
            "Un produit ERP relié à plusieurs sku duplique son stock et son prix d'achat à la jointure.")
    ajouter("LIAISON - id_web en doublon", "LIAISON", "bloquant",
            liaison[liaison["id_web"].notna() & liaison["id_web"].duplicated(keep=False)], "id_web",
            "Un sku relié à plusieurs produits ERP duplique ses ventes à la jointure.")

    # --- 4. Contrôles croisés
    ids_erp = set(erp["product_id"].dropna())
    skus_web = set(wp["sku"].dropna())
    liaison_ok = liaison[liaison["id_web"].notna() & liaison["product_id"].notna()]
    ids_lies = set(liaison_ok["product_id"])
    skus_lies = set(liaison_ok["id_web"])

    ajouter("CROISÉ - product_id de la liaison absent de l'ERP", "LIAISON → ERP", "bloquant",
            liaison[liaison["product_id"].notna() & ~liaison["product_id"].isin(ids_erp)],
            "product_id",
            "Les ventes de ces produits n'auront ni prix d'achat ni stock : marge incalculable.")
    ajouter("CROISÉ - id_web de la liaison absent du site", "LIAISON → WEB", "à vérifier",
            liaison[liaison["id_web"].notna() & ~liaison["id_web"].isin(skus_web)], "id_web",
            "Le sku attendu n'existe pas dans l'export : produit supprimé du site ou faute de frappe.")
    ajouter("CROISÉ - produit vendu en ligne (ERP) sans liaison", "ERP → LIAISON", "bloquant",
            erp[(onsale == 1) & ~erp["product_id"].isin(ids_lies)], "product_id",
            "Ses ventes web ne pourront pas lui être rattachées : CA et marge sous-estimés.")
    ajouter("CROISÉ - sku du site sans liaison", "WEB → LIAISON", "bloquant",
            wp[wp["sku"].notna() & ~wp["sku"].isin(skus_lies)], "sku",
            "Les ventes de ce produit disparaîtront de l'analyse après jointure.")

    jointure = (liaison_ok[["id_web", "product_id"]]
                .merge(wp[["sku", "total_sales"]], left_on="id_web", right_on="sku", how="inner")
                .merge(erp[["product_id", "_ligne"]].assign(onsale_web=onsale), on="product_id", how="inner"))
    jointure["total_sales"] = pd.to_numeric(jointure["total_sales"], errors="coerce")
    ajouter("CROISÉ - ventes web sur un produit marqué non vendu en ligne", "ERP ↔ WEB", "à vérifier",
            jointure[(jointure["onsale_web"] == 0) & (jointure["total_sales"] > 0)]
            .drop_duplicates(subset="_ligne"), "product_id",
            "onsale_web ou la liaison est faux ; selon le filtre utilisé, ces ventes seront exclues du CA.")

    return recap()


if __name__ == "__main__":
    pd.set_option("display.max_colwidth", 80)
    pd.set_option("display.width", 200)
    r = controle_qualite(pd.read_excel("erp.xlsx"), pd.read_excel("web.xlsx"), pd.read_excel("liaison.xlsx"))
    print(r.to_string())
    r.to_excel("controle_qualite_resultat.xlsx", index=False)
