# Portfolio data : Ratiba Benzerouali

Analyse de données (formation Business Intelligence Analyst, OpenClassrooms) et product management (alternance chez Komeet).

**Contact :** _à ajouter : e-mail et LinkedIn_

Ce dépôt réunit le code et les livrables de mes projets, classés par pertinence pour un poste d'analyste de données. Les scénarios (Bottleneck, Les Plus Beaux Logis de Paris, Primero Bank) sont des cas d'école fictifs. Les chiffres cités viennent des livrables de chaque dossier.

## Projets

| # | Projet | Outils | Dossier |
|---|--------|--------|---------|
| 1 | Bottleneck : nettoyage et analyse du stock, notebook amélioré avec l'IA | Python, pandas, plotly, seaborn, Pandera | [01-bottleneck-stock-amelioration-ia](01-bottleneck-stock-amelioration-ia) |
| 2 | Bottleneck : rapport d'analyse et tableau de bord Power BI | SQLite, Power Query, DAX, Power BI | [02-bottleneck-power-bi](02-bottleneck-power-bi) |
| 3 | Prix immobiliers à Paris : régression et KMeans | Python, scipy, scikit-learn | [03-paris-immobilier-python](03-paris-immobilier-python) |
| 4 | Primero Bank : analyse du churn | Excel (tableaux croisés dynamiques) | [04-primero-bank-excel](04-primero-bank-excel) |
| 5 | Base de données d'assurance et 12 requêtes | SQL, MySQL Workbench, dbdiagram | [05-sql-assurance](05-sql-assurance) |
| 6 | Sanitoral : tableau de bord Power BI | Power BI, DAX | [06-sanitoral-power-bi](06-sanitoral-power-bi) _(à compléter)_ |

Mon travail chez Komeet (alerte de liste d'attente, analyses Metabase) n'est pas publié ici pour des raisons de confidentialité.

## 1. Bottleneck : nettoyage et analyse du stock (amélioré avec l'IA)

- **Besoin :** rapprocher 3 sources (ERP, web, liaison), corriger les erreurs, analyser ventes, stock et rentabilité d'octobre.
- **Démarche :** contrôles automatiques (règles pandas et Pandera comparées), jointures vérifiées, comparaisons IQR / Z-score, Pearson / Spearman, taux de marge moyen / marge en euros pondérée, revue du notebook par un assistant IA dont chaque affirmation est vérifiée par exécution.
- **Résultats :** CA d'octobre 153 573,1 € TTC ; stock de 17 822 bouteilles valorisé 298 627,66 € ; 68 produits en stock sans vente web (36 564,89 €), dont 65 non référencés sur le site ; le vin représente 85,0 % de la marge ; en Spearman, stock/ventes 0,76 et prix/ventes -0,69.
- **Limites :** un seul mois de ventes ; hypothèses (ventes d'octobre, prix TTC avec TVA 20 %) à confirmer avec le métier.
- **Voir :** [notebook](01-bottleneck-stock-amelioration-ia/notebook_bottleneck_ameliore.ipynb) et [documentation de la démarche](01-bottleneck-stock-amelioration-ia/documentation_demarche.pdf).

## 2. Bottleneck : rapport d'analyse et tableau de bord Power BI

- **Besoin :** choisir comment alimenter Power BI depuis une base SQLite, puis suivre prix d'achat, marges, marchés et promotions (octobre 2022 à septembre 2023).
- **Démarche :** comparaison de 3 solutions d'extraction (connexion directe, export CSV, ETL) ; choix de la connexion directe avec nettoyage dans Power Query ; tableau de bord de 7 pages et 16 mesures DAX.
- **Résultats :** CA hors promotion 2 237 005 € ; marge 1 052 773 € (47,06 %) ; 88 133 quantités vendues ; rotation des stocks 2,37.
- **Recommandations :** répercuter la hausse des prix d'achat (+7,0 % contre +3,6 % pour les prix de vente) ; développer le sans alcool avec les bons produits ; cibler les promotions (marge de 31,7 % contre 47,1 % hors promotion).
- **Voir :** [rapport](02-bottleneck-power-bi/rapport_analyse.docx) et [modèle du tableau de bord](02-bottleneck-power-bi/modele_tableau_de_bord.pbit).

## 3. Prix immobiliers à Paris

- **Besoin :** quel segment vendre en priorité, et reconnaître automatiquement le type d'un bien.
- **Données :** 26 196 ventes à Paris (2017 à 2021), 16 doublons exacts supprimés.
- **Résultats :** erreur moyenne de la régression de 9,05 % (objectif inférieur à 10 %) ; portefeuille valorisé 71,23 M€ (154 appartements) et 98,69 M€ (121 locaux commerciaux) ; KMeans à 79,87 % de précision sur les ventes 2021.
- **Limites :** les 40 biens du client sont tous classés « appartement », sans étiquette pour vérifier ; ils sont tous dans le 75019.
- **Voir :** [notebook](03-paris-immobilier-python/notebook.ipynb) et [présentation](03-paris-immobilier-python/presentation.pptx).

## 4. Primero Bank : analyse du churn

- **Besoin :** identifier le profil des clients qui quittent la banque et les clients actuels à risque.
- **Résultats :** taux de départ de 70 % pour la carte Platinum et de 22,9 % pour les revenus de 40 K€ à 80 K€ ; au-delà de 4 mois sans transaction, le taux dépasse 50 %.
- **Limites :** les raisons du départ sont des hypothèses déduites de corrélations.
- **Voir :** [rapport](04-primero-bank-excel/rapport_analyse.pdf) et [présentation](04-primero-bank-excel/presentation.pdf).

## 5. Base de données d'assurance avec SQL

- **Besoin :** construire une base relationnelle à partir de 2 fichiers CSV (38 916 et 30 335 lignes importées) et l'analyser.
- **Démarche :** exploration sous Excel, dictionnaire de données, schéma relationnel, import dans MySQL, 12 requêtes (jointures, COUNT, AVG, GROUP BY, HAVING).
- **Voir :** [document technique](05-sql-assurance/document_technique.pdf), [requêtes et résultats](05-sql-assurance/liste_requetes_resultats.pdf), [méthodologie](05-sql-assurance/methodologie.pdf).

## Mon système de veille

Objectif : suivre les outils et méthodes d'analyse de données et d'IA, et décider de façon justifiée. Détails dans [veille](veille/README.md).
