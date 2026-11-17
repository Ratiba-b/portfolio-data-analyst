# Réponse de l'IA, prompt B, essai 1 (explications rendues avec le code)

La fonction renvoie un tableau trié par gravité (bloquant, à vérifier, information). Pour chaque contrôle, il donne le nombre de lignes en anomalie, cinq exemples et une colonne `explication` qui dit en une phrase pourquoi le contrôle compte. L'IA indique avoir testé le fichier sur des données factices où elle avait glissé des anomalies volontaires.

Points d'incertitude signalés par l'IA :
- La relation un-pour-un dans la liaison est supposée, pas garantie.
- Seules les lignes post_type = « product » sont retenues comme fiches produit (convention WooCommerce) ; les variantes (« product_variation ») sont à ajouter si besoin.
- Le taux de TVA n'est pas dans les données : le contrôle de marge HT ne s'active que si `taux_tva` est passé.
- La normalisation des clés ne traite ni les zéros en tête ni la casse.
- Les prix atypiques sont repérés par l'IQR, pas par une règle métier.
- Ventes supérieures au stock non contrôlées : on ne sait pas si le stock est une photo de début ou de fin de mois.
- Ligne Excel = index pandas + 2.
