# 📖 Guide Utilisateur — MECHA Predict

> **Destinataires** : Responsables maintenance, Responsables production, Chefs d'équipe  
> **Version** : 1.0  
> **Date** : 30/05/2026  
> **Classification** : Usage interne  
> **Compétence couverte** : **C7 — Documentation utilisateur**

---

## 🎯 À quoi sert MECHA Predict ?

MECHA Predict est **votre assistant de maintenance intelligent**. Il surveille en permanence l'état de vos machines et vous prévient **avant** qu'une panne ne se produise.

> 💡 **En résumé** : Au lieu d'attendre qu'une machine tombe en panne (maintenance curative), MECHA Predict anticipe les problèmes et vous recommande d'intervenir au bon moment (maintenance prédictive).

### Ce que fait la solution

| Fonction | Description |
|----------|-------------|
| 🔍 **Surveillance continue** | Les capteurs de vos machines (température, vibration, pression…) sont analysés en permanence |
| 🧠 **Prédiction de pannes** | L'intelligence artificielle détecte les signes avant-coureurs d'une défaillance |
| ⏱️ **Estimation de durée de vie** | La solution estime combien de temps une machine peut encore fonctionner normalement |
| 🚨 **Alertes automatiques** | Vous êtes prévenu dès qu'une intervention est recommandée |
| 📊 **Tableaux de bord** | Vous visualisez l'état de votre parc machines en un coup d'œil |

### Ce que la solution **ne fait pas**

- ❌ Elle ne remplace **pas** votre expertise de terrain
- ❌ Elle ne décide **pas** des interventions à votre place
- ❌ Elle ne contrôle **pas** les machines directement

---

## 🔐 Accéder à la solution

### Connexion

| Information | Détail |
|-------------|--------|
| **Adresse** | `https://mecha-predict.votre-entreprise.fr` |
| **Identifiant** | Votre identifiant habituel (même que le réseau d'entreprise) |
| **Mot de passe** | Votre mot de passe réseau |
| **Navigateurs compatibles** | Chrome (recommandé), Firefox, Edge |

> ⚠️ **Premier accès** : Contactez votre administrateur local pour activer votre compte. Un tutoriel de prise en main de 15 minutes est disponible directement sur la plateforme.

---

## 📊 Le tableau de bord principal

Lorsque vous vous connectez, vous arrivez sur le **tableau de bord principal** qui vous donne une vue d'ensemble de votre site.

### Les indicateurs clés

| Indicateur | Signification | Objectif |
|------------|---------------|----------|
| **Machines actives** | Nombre de machines en fonctionnement | Proche de 100% |
| **Alertes en cours** | Nombre d'alertes non traitées | Le plus bas possible |
| **Taux de disponibilité** | % du temps où les machines sont opérationnelles | > 95% |
| **Prochaine maintenance recommandée** | Machine prioritaire pour la prochaine intervention | Planifier dans les délais |

### Comprendre le code couleur

Le système utilise un code couleur simple pour vous indiquer l'état de chaque machine :

| Couleur | Signification | Action recommandée |
|---------|---------------|-------------------|
| 🟢 **Vert** | Machine en bon état, fonctionnement normal | Aucune action nécessaire |
| 🟡 **Orange** | Machine sous surveillance, signes de dégradation détectés | Planifier une vérification dans les prochains jours |
| 🔴 **Rouge** | Intervention urgente recommandée, risque de panne élevé | Planifier une intervention dès que possible |
| ⚪ **Gris** | Machine à l'arrêt ou données indisponibles | Vérifier l'état du capteur |

---

## 🧠 Comprendre les prédictions

### Le score de santé machine (0 à 100%)

Chaque machine dispose d'un **score de santé** mis à jour en continu :

| Plage | Interprétation |
|-------|----------------|
| **80 — 100%** | Excellent état, la machine fonctionne dans des conditions optimales |
| **60 — 79%** | État correct, quelques paramètres à surveiller |
| **40 — 59%** | Dégradation en cours, une maintenance préventive est recommandée |
| **20 — 39%** | État critique, intervention fortement recommandée |
| **0 — 19%** | Risque imminent de panne, arrêt de production possible |

### La durée de vie restante (RUL)

Le **RUL** (Remaining Useful Life, ou « durée de vie résiduelle ») est une estimation du temps restant avant qu'une panne ne se produise si aucune intervention n'est réalisée.

> 💡 **Exemple concret** : Si le RUL d'une machine affiche « 72 heures », cela signifie que selon les données des capteurs, la machine pourrait tomber en panne dans environ 3 jours. C'est le moment idéal pour planifier une intervention sans impacter la production.

| RUL affiché | Interprétation | Recommandation |
|-------------|----------------|----------------|
| **> 7 jours** | Pas d'urgence | Intégrer dans la planification standard |
| **3 à 7 jours** | Attention requise | Planifier une intervention cette semaine |
| **1 à 3 jours** | Urgence modérée | Intervention dans les 24-48h |
| **< 24 heures** | Urgence élevée | Intervention immédiate recommandée |

### Le niveau de confiance

Chaque prédiction est accompagnée d'un **niveau de confiance** (en %) qui indique la fiabilité de l'estimation :

- **> 85%** : Forte confiance — vous pouvez vous appuyer sur cette prédiction pour planifier
- **60 — 85%** : Confiance moyenne — à croiser avec votre expertise terrain
- **< 60%** : Confiance faible — la prédiction est indicative, une vérification manuelle est recommandée

> ⚠️ **Important** : Un niveau de confiance faible peut indiquer un comportement inhabituel de la machine que le système n'a pas encore appris. Signalez-le à l'équipe support.

---

## 🚨 Les alertes

### Types d'alertes

| Type | Icône | Signification | Délai d'action |
|------|-------|---------------|----------------|
| **Alerte préventive** | 🟡 | Une dégradation est détectée, une maintenance est recommandée | Sous 7 jours |
| **Alerte urgente** | 🔴 | Risque de panne imminent, intervention prioritaire | Sous 24-48h |
| **Information** | 🔵 | Événement notable (ex : remplacement de capteur effectué) | Prise de connaissance |

### Comment réagir à une alerte

**Étape 1** — Consultez le détail de l'alerte (cliquez sur la ligne dans le tableau des alertes)

**Étape 2** — Lisez la recommandation associée (type de vérification, composant concerné)

**Étape 3** — Planifiez l'intervention si nécessaire

**Étape 4** — Après l'intervention, marquez l'alerte comme « traitée » dans le système

### Workflow de validation d'une alerte

```
Alerte reçue → Consultation détail → Décision (intervenir / surveiller)
    → Si intervention : Créer ordre de maintenance → Réaliser → Clôturer
    → Si surveillance : Programmer une vérification → Réévaluer
```

---

## 🔧 Planifier une maintenance

Depuis le tableau de bord, vous pouvez créer un **ordre de maintenance** :

1. Cliquez sur la machine concernée
2. Sélectionnez **« Planifier maintenance »**
3. Renseignez :
   - Type d'intervention (préventive / corrective)
   - Date souhaitée
   - Description de l'intervention
   - Technicien assigné (si applicable)
4. Validez

L'ordre de maintenance apparaîtra dans le **calendrier de maintenance** de votre site.

### Priorisation des interventions

Lorsque plusieurs alertes sont actives, le système vous propose un **ordre de priorité** basé sur :
- Le niveau d'urgence (rouge avant orange)
- L'impact production (machines critiques en premier)
- La facilité d'intervention (regrouper les interventions proches)

---

## ⚠️ Limites et conditions d'usage

### Conditions de fiabilité des prédictions

Pour que les prédictions soient fiables, il est important que :

- ✅ Les capteurs fonctionnent correctement (pas de données manquantes)
- ✅ La machine a été surveillée pendant au moins **2 semaines** (phase d'apprentissage)
- ✅ Les conditions de fonctionnement sont dans la plage habituelle
- ✅ Les maintenances réalisées sont enregistrées dans le système

### Ce qui peut réduire la fiabilité

- ❌ Un capteur défaillant ou mal calibré
- ❌ Un changement soudain de production (nouveau matériau, vitesse inhabituelle)
- ❌ Une machine récemment installée (historique insuffisant)

### Que faire si les prédictions semblent incorrectes ?

1. **Vérifiez les capteurs** — Un capteur défaillant peut fausser les données
2. **Signalez-le** — Utilisez le bouton « Signaler un problème » sur la fiche machine
3. **Continuez votre routine** — Le système s'améliore avec le temps et vos retours
4. **Contactez le support** — L'équipe data ajustera le modèle si nécessaire

---

## ❓ Questions fréquentes (FAQ)

**Q : L'IA va-t-elle remplacer les techniciens de maintenance ?**  
> Non. L'IA est un **outil d'aide à la décision**. C'est toujours le responsable maintenance qui décide des interventions. L'IA vous donne de l'information en plus, elle ne remplace pas votre expertise.

**Q : Que se passe-t-il si je n'ai pas accès à Internet ?**  
> Les données des capteurs continuent d'être collectées localement. Dès que la connexion est rétablie, les données sont synchronisées et les prédictions mises à jour.

**Q : À quelle fréquence les prédictions sont-elles mises à jour ?**  
> Les prédictions sont recalculées **toutes les heures** à partir des dernières données capteurs.

**Q : Puis-je exporter les données pour mes rapports ?**  
> Oui. Un bouton d'export (CSV / PDF) est disponible sur chaque page du tableau de bord.

**Q : Comment signaler une fausse alerte ?**  
> Cliquez sur l'alerte concernée et sélectionnez « Fausse alerte ». Cette information est précieuse car elle permet d'améliorer le modèle de prédiction.

**Q : La solution fonctionne-t-elle pendant les arrêts de production ?**  
> Le système continue de surveiller les machines même à l'arrêt. Les prédictions seront ajustées lors de la reprise de production.

---

## 📞 Support et contacts

| Type de besoin | Contact | Délai de réponse |
|----------------|---------|-----------------|
| **Problème d'accès** | Administrateur local de votre site | Sous 4h |
| **Question sur une prédiction** | Équipe data MECHA Predict | Sous 24h |
| **Bug ou dysfonctionnement** | Support technique : `support@mecha-predict.fr` | Sous 8h |
| **Suggestion d'amélioration** | Via le bouton « Feedback » sur l'interface | Pris en compte mensuellement |

> 💡 **Astuce** : Le bouton **« Aide »** (icône ❓) disponible sur chaque page vous donne accès à des explications contextuelles et des tutoriels vidéo.

---

> **Document rédigé par** : Équipe projet MECHA  
> **Dernière mise à jour** : 30/05/2026  
> **Prochaine révision** : Après la phase pilote (retours utilisateurs Lyon)
