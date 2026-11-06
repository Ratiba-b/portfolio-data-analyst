# Bottleneck : nettoyage et analyse du stock (amélioré avec l'IA)

**Contenu**
- `notebook_bottleneck_ameliore.ipynb` : notebook exécuté, avec ses sorties.
- `documentation_demarche.pdf` : veille, cahier des charges, tests comparatifs, traçabilité des essais IA, limites.
- `erp.xlsx`, `web.xlsx`, `liaison.xlsx` : données du cas d'école (fictif).

**Exécuter**
1. Installer les bibliothèques : `pip install -r requirements.txt` (Pandera est facultatif).
2. Garder les 3 fichiers xlsx dans le même dossier que le notebook.
3. Dans Jupyter : Kernel, puis Restart and Run All. Le notebook s'arrête avec un message si un contrôle échoue.

**Hypothèses (à confirmer avec le métier)** : `total_sales` = ventes d'octobre ; `price` = prix TTC avec une TVA de 20 %.
