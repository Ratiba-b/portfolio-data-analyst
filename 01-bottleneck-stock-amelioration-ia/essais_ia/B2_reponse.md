# Réponse de l'IA, prompt B, essai 2 (explications rendues avec le code)

La fonction renvoie une ligne par contrôle (nom, périmètre, gravité, nombre de lignes en anomalie, exemples, explication), les contrôles bloquants en premier. L'IA indique l'avoir testée sur des données fictives, pas sur les vrais fichiers.

Points d'incertitude signalés par l'IA :
- TVA à 20 % en paramètre (`taux_tva`) ; deux contrôles séparés : « TTC < achat » (perte certaine) et « HT < achat » (dépend du taux).
- Lignes dont post_type n'est ni `product` ni `product_variation` exclues des contrôles croisés (ex. images `attachment`).
- **total_sales** : l'IA affirme que dans WooCommerce standard c'est un cumul depuis la création du produit. Affirmation non confirmée par une source officielle : signalée comme limite dans la documentation.
- Identifiants ramenés au même format texte avant comparaison.
- Quantité 0 avec statut « instock » signalée « à vérifier » (précommandes possibles).
- Prix atypiques (IQR) en simple information.
