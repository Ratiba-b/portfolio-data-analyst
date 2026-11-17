"""
Contrôle qualité des fichiers erp.xlsx, web.xlsx et liaison.xlsx.

Usage :
    python controle_qualite.py              # fichiers dans le dossier courant
    python controle_qualite.py chemin/vers/dossier

Affiche les problèmes par fichier (avec des exemples de lignes), puis une
synthèse, enregistrée aussi dans rapport_qualite.xlsx.
Dépendances : pandas, openpyxl
"""
import sys
from pathlib import Path

import pandas as pd

DOSSIER = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
N_EXEMPLES = 5

COLONNES = {
    "erp.xlsx": ["product_id", "onsale_web", "price", "stock_quantity",
                 "stock_status", "purchase_price"],
    "web.xlsx": ["sku", "virtual", "downloadable", "rating_count", "average_rating",
                 "total_sales", "tax_status", "tax_class", "post_author", "post_date",
                 "post_date_gmt", "post_content", "product_type", "post_title",
                 "post_excerpt", "post_status", "comment_status", "ping_status",
                 "post_password", "post_name", "post_modified", "post_modified_gmt",
                 "post_content_filtered", "post_parent", "guid", "menu_order",
                 "post_type", "post_mime_type", "comment_count"],
    "liaison.xlsx": ["id_web", "product_id"],
}

problemes = []


# --------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------
def signaler(fichier, controle, lignes, colonnes=None, tout=False, unite="ligne(s)"):
    """Enregistre un problème s'il concerne au moins une ligne."""
    if len(lignes) == 0:
        return
    apercu = lignes[colonnes] if colonnes else lignes
    problemes.append({
        "fichier": fichier,
        "controle": controle,
        "nb": len(lignes),
        "unite": unite,
        "exemples": apercu if tout else apercu.head(N_EXEMPLES),
    })


def normaliser_cle(serie):
    """Clé en texte comparable : '123', 123 et 123.0 deviennent '123'."""
    s = serie.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    return s.replace({"": pd.NA, "nan": pd.NA})


def num(df, col):
    return pd.to_numeric(df[col], errors="coerce")


def texte(df, col):
    return df[col].fillna("").astype(str).str.strip().str.lower()


def non_numeriques(fichier, df, col, cle):
    masque = num(df, col).isna() & df[col].notna()
    signaler(fichier, f"{col} : valeurs non numériques", df[masque], [cle, col])


def valeurs_atypiques(fichier, df, col, cle):
    """Méthode IQR : à vérifier, pas forcément des erreurs."""
    s = num(df, col)
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    bas, haut = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    masque = (s < bas) | (s > haut)
    signaler(fichier,
             f"{col} : valeurs atypiques à vérifier (hors [{bas:.2f} ; {haut:.2f}], IQR)",
             df[masque].sort_values(col, ascending=False), [cle, col])


# --------------------------------------------------------------------------
# Chargement et contrôles génériques
# --------------------------------------------------------------------------
def charger(nom):
    df = pd.read_excel(DOSSIER / nom)
    df.columns = df.columns.astype(str).str.strip()
    attendues = COLONNES[nom]
    manquantes = [c for c in attendues if c not in df.columns]
    en_trop = [c for c in df.columns if c not in attendues]
    if en_trop:
        signaler(nom, "Colonnes inattendues", pd.DataFrame({"colonne": en_trop}),
                 tout=True, unite="colonne(s)")
    if manquantes:
        sys.exit(f"{nom} : colonnes manquantes {manquantes}, contrôles impossibles.")
    return df


def controles_generiques(nom, df):
    signaler(nom, "Lignes entièrement dupliquées", df[df.duplicated(keep=False)])

    manquants = df.isna().sum()
    manquants = manquants[manquants > 0]
    if not manquants.empty:
        tableau = pd.DataFrame({
            "colonne": manquants.index,
            "nb_manquants": manquants.values,
            "pct": (manquants.values / len(df) * 100).round(1),
        }).sort_values("nb_manquants", ascending=False)
        signaler(nom, "Valeurs manquantes", tableau, tout=True, unite="colonne(s)")

    vides = [c for c in df.columns if df[c].isna().all()]
    signaler(nom, "Colonnes entièrement vides", pd.DataFrame({"colonne": vides}),
             tout=True, unite="colonne(s)")

    constantes = [c for c in df.columns
                  if df[c].nunique(dropna=True) == 1 and df[c].notna().any()]
    signaler(nom, "Colonnes à valeur unique (constantes)",
             pd.DataFrame({"colonne": constantes,
                           "valeur": [df[c].dropna().iloc[0] for c in constantes]}),
             tout=True, unite="colonne(s)")

    # Espaces en début ou fin de texte (hors champs de contenu long)
    for col in df.columns:
        if col.startswith(("post_content", "post_excerpt")):
            continue
        s = df[col].dropna()
        s = s[s.map(lambda x: isinstance(x, str))].astype(str)
        if s.empty:
            continue
        masque = s != s.str.strip()
        signaler(nom, f"{col} : espaces en début ou fin de texte", df.loc[s[masque].index], [col])


# --------------------------------------------------------------------------
# Contrôles par fichier
# --------------------------------------------------------------------------
def controles_erp(erp):
    f = "erp.xlsx"
    erp = erp.copy()
    erp["product_id"] = normaliser_cle(erp["product_id"])

    signaler(f, "product_id manquant", erp[erp["product_id"].isna()])
    signaler(f, "product_id en double",
             erp[erp["product_id"].notna() & erp["product_id"].duplicated(keep=False)]
             .sort_values("product_id"))

    for col in ["onsale_web", "price", "stock_quantity", "purchase_price"]:
        non_numeriques(f, erp, col, "product_id")

    prix, achat, stock, en_ligne = (num(erp, c) for c in
                                    ["price", "purchase_price", "stock_quantity", "onsale_web"])

    signaler(f, "onsale_web différent de 0/1",
             erp[en_ligne.notna() & ~en_ligne.isin([0, 1])], ["product_id", "onsale_web"])
    signaler(f, "price <= 0", erp[prix <= 0], ["product_id", "price"])
    signaler(f, "purchase_price <= 0", erp[achat <= 0], ["product_id", "purchase_price"])
    signaler(f, "Prix de vente inférieur au prix d'achat", erp[prix < achat],
             ["product_id", "price", "purchase_price"])
    signaler(f, "stock_quantity négatif", erp[stock < 0], ["product_id", "stock_quantity"])
    signaler(f, "stock_quantity non entier", erp[stock.notna() & (stock % 1 != 0)],
             ["product_id", "stock_quantity"])

    statut = texte(erp, "stock_status")
    signaler(f, "stock_status hors {instock, outofstock}",
             erp[(statut != "") & ~statut.isin(["instock", "outofstock"])],
             ["product_id", "stock_status"])
    signaler(f, "Incohérence : instock avec une quantité <= 0",
             erp[(statut == "instock") & (stock <= 0)],
             ["product_id", "stock_quantity", "stock_status"])
    signaler(f, "Incohérence : outofstock avec une quantité > 0",
             erp[(statut == "outofstock") & (stock > 0)],
             ["product_id", "stock_quantity", "stock_status"])

    valeurs_atypiques(f, erp, "price", "product_id")
    valeurs_atypiques(f, erp, "purchase_price", "product_id")
    return erp


def controles_web(web):
    f = "web.xlsx"
    web = web.copy()
    web["sku"] = normaliser_cle(web["sku"])
    types = texte(web, "post_type")

    # Plusieurs post_type = un même produit peut apparaître plusieurs fois
    if types.nunique() > 1:
        repartition = types.value_counts().rename_axis("post_type").reset_index(name="nb")
        signaler(f, "post_type : plusieurs valeurs (lignes répétées par produit ?)",
                 repartition, tout=True, unite="valeur(s)")

    signaler(f, "sku manquant", web[web["sku"].isna()], ["post_type", "post_title"])
    signaler(f, "sku en double pour un même post_type",
             web[web["sku"].notna() & web.duplicated(["sku", "post_type"], keep=False)]
             .sort_values("sku"), ["sku", "post_type", "post_title"])

    for col in ["virtual", "downloadable"]:
        s = num(web, col)
        signaler(f, f"{col} différent de 0/1", web[web[col].notna() & ~s.isin([0, 1])],
                 ["sku", col])

    for col in ["rating_count", "average_rating", "total_sales", "comment_count"]:
        non_numeriques(f, web, col, "sku")
        signaler(f, f"{col} négatif", web[num(web, col) < 0], ["sku", col])

    note, nb_avis = num(web, "average_rating"), num(web, "rating_count")
    signaler(f, "average_rating hors [0 ; 5]", web[(note < 0) | (note > 5)],
             ["sku", "average_rating"])
    signaler(f, "Note moyenne > 0 sans aucun avis", web[(nb_avis == 0) & (note > 0)],
             ["sku", "rating_count", "average_rating"])

    dates = {}
    for col in ["post_date", "post_date_gmt", "post_modified", "post_modified_gmt"]:
        d = pd.to_datetime(web[col], errors="coerce")
        signaler(f, f"{col} : date invalide", web[d.isna() & web[col].notna()], ["sku", col])
        signaler(f, f"{col} : date dans le futur", web[d > pd.Timestamp.now()], ["sku", col])
        dates[col] = d
    signaler(f, "post_modified antérieur à post_date",
             web[dates["post_modified"] < dates["post_date"]],
             ["sku", "post_date", "post_modified"])

    taxe = texte(web, "tax_status")
    signaler(f, "tax_status hors {taxable, shipping, none}",
             web[(taxe != "") & ~taxe.isin(["taxable", "shipping", "none"])],
             ["sku", "tax_status"])
    signaler(f, "post_title vide", web[texte(web, "post_title") == ""], ["sku", "post_type"])
    signaler(f, "post_password renseigné", web[texte(web, "post_password") != ""],
             ["sku", "post_password"])
    signaler(f, "guid en double",
             web[web["guid"].notna() & web["guid"].duplicated(keep=False)].sort_values("guid"),
             ["sku", "post_type", "guid"])

    produits = web[types == "product"] if (types == "product").any() else web
    signaler(f, "Produits non publiés (post_status ≠ publish)",
             produits[texte(produits, "post_status") != "publish"],
             ["sku", "post_title", "post_status"])
    signaler(f, "post_name en double parmi les produits",
             produits[produits["post_name"].notna()
                      & produits["post_name"].duplicated(keep=False)].sort_values("post_name"),
             ["sku", "post_name"])
    return produits


def controles_liaison(liaison):
    f = "liaison.xlsx"
    liaison = liaison.copy()
    for col in ["id_web", "product_id"]:
        liaison[col] = normaliser_cle(liaison[col])
        signaler(f, f"{col} manquant", liaison[liaison[col].isna()])
        signaler(f, f"{col} en double",
                 liaison[liaison[col].notna() & liaison[col].duplicated(keep=False)]
                 .sort_values(col))
    return liaison


def controles_croises(erp, produits, liaison):
    f = "Contrôles croisés"
    ids_erp = set(erp["product_id"].dropna())
    skus = set(produits["sku"].dropna())
    lp, lw = liaison["product_id"], liaison["id_web"]

    signaler(f, "liaison.product_id absent de l'ERP", liaison[lp.notna() & ~lp.isin(ids_erp)])
    signaler(f, "Produits ERP absents de la liaison",
             erp[erp["product_id"].notna() & ~erp["product_id"].isin(set(lp.dropna()))],
             ["product_id", "onsale_web", "stock_status"])
    signaler(f, "liaison.id_web absent du site (web.sku)", liaison[lw.notna() & ~lw.isin(skus)])
    signaler(f, "Produits web absents de la liaison",
             produits[produits["sku"].notna() & ~produits["sku"].isin(set(lw.dropna()))],
             ["sku", "post_title"])

    rattaches = set(liaison.loc[lp.notna() & lw.isin(skus), "product_id"])
    en_ligne = num(erp, "onsale_web")
    signaler(f, "onsale_web = 1 mais aucun produit web rattaché",
             erp[(en_ligne == 1) & ~erp["product_id"].isin(rattaches)],
             ["product_id", "onsale_web", "price"])
    signaler(f, "onsale_web = 0 mais rattaché à un produit web",
             erp[(en_ligne == 0) & erp["product_id"].isin(rattaches)],
             ["product_id", "onsale_web", "price"])


# --------------------------------------------------------------------------
# Rapport
# --------------------------------------------------------------------------
def afficher_rapport():
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.max_colwidth", 50)

    if not problemes:
        print("Aucun problème détecté.")
        return

    courant = None
    for p in problemes:
        if p["fichier"] != courant:
            courant = p["fichier"]
            print(f"\n{'=' * 80}\n{courant}\n{'=' * 80}")
        print(f"\n▶ {p['controle']} : {p['nb']} {p['unite']}")
        print(p["exemples"].to_string())

    synthese = pd.DataFrame([{k: p[k] for k in ("fichier", "controle", "nb", "unite")}
                             for p in problemes])
    print(f"\n{'=' * 80}\nSYNTHÈSE : {len(problemes)} problème(s)\n{'=' * 80}")
    print(synthese.to_string(index=False))
    synthese.to_excel(DOSSIER / "rapport_qualite.xlsx", index=False)
    print(f"\nSynthèse enregistrée dans {DOSSIER / 'rapport_qualite.xlsx'}")


def main():
    erp, web, liaison = (charger(n) for n in ["erp.xlsx", "web.xlsx", "liaison.xlsx"])
    for nom, df in [("erp.xlsx", erp), ("web.xlsx", web), ("liaison.xlsx", liaison)]:
        controles_generiques(nom, df)
    erp = controles_erp(erp)
    produits = controles_web(web)
    liaison = controles_liaison(liaison)
    controles_croises(erp, produits, liaison)
    afficher_rapport()


if __name__ == "__main__":
    main()
