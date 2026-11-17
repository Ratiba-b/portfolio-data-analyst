# Bottleneck : contrôle qualité automatique généré par l'IA (amélioration du projet 6)

**Contenu**
- `notebook_bottleneck_ameliore.ipynb` : notebook exécuté ; l'étape 1.3 raconte la démarche : référence, 4 programmes écrits par l'IA, évaluation ligne par ligne, méthodes sans IA générative, choix et impact.
- `controle_qualite_retenu.py` : le contrôle retenu (essai A1), seul.
- `essais_ia/` : les 4 codes générés par l'IA, ses explications et les résultats de la comparaison.
- `documentation_demarche.pdf` : veille, cahier des charges, tests, traçabilité, limites.
- `erp.xlsx`, `web.xlsx`, `liaison.xlsx` : données du cas d'école (fictif).

**Exécuter**
1. `pip install -r requirements.txt`
2. Garder les 3 fichiers xlsx dans le même dossier que le notebook.
3. Dans Jupyter : Kernel, puis Restart and Run All.

**Hypothèses (à confirmer avec le métier)** : `total_sales` = ventes d'octobre ; `price` = prix TTC avec une TVA de 20 % ; pour les produits en double, les ventes de la fiche produit sont retenues plutôt que celles de la ligne image.
