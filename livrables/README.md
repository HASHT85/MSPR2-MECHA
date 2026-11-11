# Dossier des Livrables Officiels — MSPR TPRE841 (MECHA Predict)

**Certification** : RNCP35584 (Niveau 7) — Bloc 4 : *Concevoir et développer des solutions applicatives métier et spécifiques* (C1 à C8)  
**Équipe projet** : Malek EL FAYEDH, Thibaut DOREAU, Vincent GONÇALVES, Pierre-Louis GUINEL  
**Dépôt GitHub public** : https://github.com/HASHT85/MSPR2-MECHA

Ce dossier regroupe l'ensemble des documents finaux prêts à être transmis au jury (par courriel ou dépôt Drive), structurés selon la **section IV — Les Livrables** du cahier des charges officiel :

---

## `01_Dossier_Global/`
- **`00_Compte_Rendu_Global_MSPR_TPRE841_MECHA.pdf`** *(17 pages)* : Dossier maître consolidé regroupant de manière dissociée et argumentée l'ensemble des livrables d'aide à la décision (collecte des besoins C1, architecture C2, modélisation IA & AMDEC C3, solution applicative C4, tests C5, CI/CD C6, documentation C7, conduite du changement C8, RGPD/EU AI Act et déploiement multi-sites).

## `02_Documentation_et_Validation/`
Les 11 dossiers thématiques individuels paginés en A4 :
1. **`01_Entretien_Client_Besoins_C1.pdf`** — Compte-rendu des échanges client, besoins métiers et BPMN `AS-IS` (C1).
2. **`02_Architecture_Applicative_C2.pdf`** — Schéma d'architecture, flux de données, modélisation PostgreSQL 15 et exposition des résultats (C2, C4).
3. **`03_Choix_Techniques_et_Modeles_C2_C3.pdf`** — Outils, langages, gestion Git, benchmark des 5 modèles ML, critères de sélection et limites (C2, C3).
4. **`04_Dictionnaire_Donnees_MECHA.pdf`** — Référentiel des 30 variables et hypothèses de simulation / fusion UCI AI4I 2020 (C3).
5. **`05_Fiches_Modeles_ML_Model_Cards_C3.pdf`** — Paramètres retenus, métriques obtenues et interprétation des 5 modèles ML (C3, C7).
6. **`06_Plan_Tests_Validation_et_Conformite_C5_C7.pdf`** — Démarche de validation globale (104 tests automatisés) et plan de correction (C5, C6, C7).
7. **`07_Guide_Utilisateur_Metier_2pages_C7.pdf`** — **Guide opérationnel métier en 2 pages** destiné aux responsables maintenance et production (C7).
8. **`08_Conduite_du_Changement_C8.pdf`** — Acteurs concernés, messages clés, BPMN `AS-IS`/`TO-BE`, formation et accompagnement terrain (C8).
9. **`09_Analyse_RGPD_et_EU_AI_Act.pdf`** — Enjeux RGPD (données réelles, anonymisation, DPO) et conformité EU AI Act Art. 13-14.
10. **`10_Plan_Deploiement_Multi_Sites.pdf`** — Projection industrielle dans les 5 usines France/Espagne, prérequis, impacts et points de vigilance.
11. **`11_Modelisation_Processus_BPMN_AS_IS_TO_BE_C1_C8.pdf`** — Modélisation normalisée OMG BPMN 2.0 des workflows de maintenance (`AS-IS` vs `TO-BE` *Human-in-the-Loop*, fichiers XML sources disponibles dans `docs/bpmn/`).

## `03_Support_Soutenance/`
- **`Support_Soutenance_MECHA_TPRE841.pptx`** — Support PowerPoint éditable (16 slides 16:9 calibrées pour 20 minutes à 4 intervenants, avec minutage en notes).
- **`Support_Soutenance_MECHA_TPRE841.pdf`** — Version PDF vectorielle identique du support de présentation.
