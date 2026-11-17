# Essais IA : génération du contrôle qualité

**Outil :** Claude (Anthropic). **Date :** 13/11/2026. Une conversation neuve par essai, sans mémoire des échanges. Aucun fichier de données transmis : seulement les noms et le sens des colonnes.

## Prompts
- **Prompt A (générique)** : voir l'annexe B de `../documentation_demarche.pdf`.
- **Prompt B (avec le contexte métier)** : voir l'annexe B de `../documentation_demarche.pdf`.

## Fichiers
| Fichier | Essai |
|---|---|
| `A1_code.py` | Prompt A, essai 1 |
| `A2_code.py` | Prompt A, essai 2 |
| `B1_code.py` | Prompt B, essai 1 |
| `B2_code.py` | Prompt B, essai 2 |
| `B1_reponse.md`, `B2_reponse.md` | Explications rendues par l'IA avec les codes du prompt B |

## Résultats (calculés dans le notebook, étape 1.3.3)
Une erreur connue est « retrouvée » si toutes ses lignes sont signalées par au moins un contrôle du programme.

| Erreur (lignes) | A1 | A2 | B1 | B2 |
|---|---|---|---|---|
| 1. Statut de stock incohérent (2) | oui | oui | oui | oui |
| 2. Prix de vente négatif (3) | oui | oui | oui | oui |
| 3. Stock négatif (2) | oui | oui | oui | oui |
| 4. Prix positif inférieur au prix d'achat (4) | oui | oui | oui | oui |
| 5. Ligne du site sans SKU (85) | oui | oui | oui | oui |
| 6. Bon cadeau (2) | oui | non | partiel (1/2) | partiel (1/2) |
| 7. Ligne image (714) | oui | non | oui | oui |
| 8. Produit sans correspondance (91) | oui | oui | oui | oui |
| Contrôles qui signalent au moins une ligne | 18 | 15 | 11 | 12 |

**Retenu :** A1, tel quel, figé dans `../controle_qualite_retenu.py`. Une première notation faite à l'œil avait retenu B2 ; la notation ligne par ligne l'a corrigée.
