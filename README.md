# Portfolio data : Ratiba Benzerouali

Analyse de données (formation Business Intelligence Analyst, OpenClassrooms) et product management (alternance chez Komeet).

**Contact :** _à ajouter : e-mail et LinkedIn_

Ce dépôt réunit le code et les livrables de mes projets, classés par pertinence pour un poste d'analyste de données. Les scénarios (Bottleneck, Les Plus Beaux Logis de Paris, Primero Bank) sont des cas d'école fictifs. Les chiffres cités viennent des livrables de chaque dossier.

## Projets

| # | Projet | Outils | Dossier |
|---|--------|--------|---------|
| 1 | Bottleneck : contrôle qualité automatique écrit par l'IA (amélioration du projet 6) | Python, pandas, scikit-learn, assistant IA | [01-bottleneck-stock-amelioration-ia](01-bottleneck-stock-amelioration-ia) |
| 2 | Bottleneck : rapport d'analyse et tableau de bord Power BI | SQLite, Power Query, DAX, Power BI | [02-bottleneck-power-bi](02-bottleneck-power-bi) |
| 3 | Prix immobiliers à Paris : régression et KMeans | Python, scipy, scikit-learn | [03-paris-immobilier-python](03-paris-immobilier-python) |
| 4 | Primero Bank : analyse du churn | Excel (tableaux croisés dynamiques) | [04-primero-bank-excel](04-primero-bank-excel) |
| 5 | Base de données d'assurance et 12 requêtes | SQL, MySQL Workbench, dbdiagram | [05-sql-assurance](05-sql-assurance) |
| 7 | UOI Games : quel premier jeu triple A lancer ? | Python, scipy, Google Forms | [07-uoi-games-etude-de-marche](07-uoi-games-etude-de-marche) |
| 6 | Sanitoral : tableau de bord Power BI de suivi de projets | Power BI, DAX | [06-sanitoral-power-bi](06-sanitoral-power-bi) |
| 8 | BestMarket : satisfaction client et NPS | SQL | [08-bestmarket-sql](08-bestmarket-sql) |
| 9 | Dev'Immediat : anonymisation RGPD d'un CRM | Power Query, RGPD | [09-rgpd-dev-immediat](09-rgpd-dev-immediat) |

Mon travail chez Komeet (alerte de liste d'attente, analyses Metabase) n'est pas publié ici pour des raisons de confidentialité.

## 1. Bottleneck : contrôle qualité automatique écrit par l'IA (amélioration du projet 6)

- **Besoin :** dans le projet 6, les erreurs des fichiers ERP, web et liaison étaient cherchées à la main. Le contrôle les détecte automatiquement avant chaque analyse.
- **Démarche :** Claude a écrit 4 programmes (2 demandes, 2 essais chacune), vérifiés ligne par ligne face aux 8 types d'erreurs du projet 6, et comparés à Isolation Forest et à la méthode IQR.
- **Résultats :** un seul programme (A1) retrouve les 8 types ; le même prompt relancé en rate 2 ; Isolation Forest et IQR retrouvent 5 à 7 erreurs chiffrées sur 9. A1 est retenu et figé.
- **Impact :** des lignes image portent d'autres ventes que la fiche produit : CA d'octobre de 143 505,1 € au lieu de 153 573,1 €, écart à arbitrer avec le métier.
- **Voir :** [dossier du projet](01-bottleneck-stock-amelioration-ia), [essais IA](01-bottleneck-stock-amelioration-ia/essais_ia).

## 2. Bottleneck : rapport d'analyse et tableau de bord Power BI

- **Besoin :** choisir comment alimenter Power BI depuis une base SQLite, puis suivre prix d'achat, marges, marchés et promotions (octobre 2022 à septembre 2023).
- **Démarche :** comparaison de 3 solutions d'extraction (connexion directe, export CSV, ETL) ; choix de la connexion directe avec nettoyage dans Power Query ; tableau de bord de 7 pages et 16 mesures DAX.
- **Résultats :** CA hors promotion 2 237 005 € ; marge 1 052 773 € (47,06 %) ; 88 133 quantités vendues ; rotation des stocks 2,37.
- **Recommandations :** répercuter la hausse des prix d'achat (+7,0 % contre +3,6 % pour les prix de vente) ; développer le sans alcool avec les bons produits ; cibler les promotions (marge de 31,7 % contre 47,1 % hors promotion).
- **Voir :** [rapport](02-bottleneck-power-bi/rapport_analyse.docx), [tableau de bord en PDF](02-bottleneck-power-bi/tableau_de_bord.pdf), [présentation](02-bottleneck-power-bi/presentation_soutenance.pdf) et [modèle Power BI](02-bottleneck-power-bi/modele_tableau_de_bord.pbit).

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

## UOI Games : quel premier jeu triple A lancer ?

- **Besoin :** UOI Games (cas d'école) n'a jamais lancé de triple A ; quel premier jeu lancer pour maximiser ses chances de succès ?
- **Données :** 3 fichiers fournis (ventes 1980-2016, notes de 440 896 jeux, ventes de consoles), études publiées (Newzoo, SELL…), questionnaire Google Forms (43 réponses dont 40 joueurs).
- **Résultats :** l'Action fait environ 30 % des ventes 2010-2016 mais c'est le genre le plus encombré ; notes critiques et ventes évoluent ensemble (Spearman 0,35, p < 0,001) ; concept testé noté 3,7 sur 5.
- **Recommandation :** une nouvelle licence d'action-aventure narrative, sur PC, PS5 et Xbox Series, à 59,99 € ; de 2,7 à 8 millions de ventes la première année (jeux comparables).
- **Limites :** questionnaire non représentatif ; données fournies arrêtées en 2016-2020 ; prévision = ordre de grandeur.
- **Voir :** [présentation](07-uoi-games-etude-de-marche/presentation.pptx), [notebook](07-uoi-games-etude-de-marche/notebook.ipynb), [version HTML](07-uoi-games-etude-de-marche/notebook.html). Les deux gros fichiers fournis (.xlsb) ne sont pas publiés (taille).

## Sanitoral : tableau de bord Power BI de suivi de projets

- **Besoin :** suivre des projets menés dans plusieurs pays (coûts, délais, livrables).
- **Démarche :** 7 tables, 4 pages (carte, analyse des performances, Gantt), 8 mesures DAX, sécurité par rôles (directeur général, pays, régional).
- **Voir :** [modèle Power BI](06-sanitoral-power-bi/modele_tableau_de_bord.pbit) (sans les données).

## BestMarket : satisfaction client et NPS avec SQL

- **Besoin :** centraliser les retours clients multicanaux et suivre le NPS de façon fiable.
- **Résultats :** 70,5 % des clients recommandent l'enseigne ; 39 magasins sur 83 sous la moyenne ; Drive le moins bien noté (7,94 sur 10).
- **Limite :** le NPS par canal donne la même valeur pour les trois canaux.
- **Voir :** [expression des besoins](08-bestmarket-sql/expression_des_besoins.docx), [présentation](08-bestmarket-sql/presentation.pdf).

## Dev'Immediat : anonymisation RGPD d'un CRM

- **Besoin :** continuer l'analyse commerciale pendant une sanction de la CNIL, sans données personnelles.
- **Démarche :** suppression des données personnelles, sensibles et tarifaires dans Power Query, tranches d'âge et de revenus, 5 recommandations RGPD.
- **Limite :** les identifiants du fichier final sont encodés en base64, donc réversibles ; le fichier n'est pas publié.
- **Voir :** [rapport](09-rgpd-dev-immediat/rapport_traitement.pdf), [recommandations](09-rgpd-dev-immediat/recommandations_rgpd.pdf).

## Mon système de veille

Objectif : suivre les outils et méthodes d'analyse de données et d'IA, et décider de façon justifiée. Détails dans [veille](veille/README.md).
