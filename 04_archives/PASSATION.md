# Passation technique du projet océanographique

## 1. État général

Ce dépôt contient un projet scientifique consacré à l'analyse de
quatre profils CTD autour de Banyuls, aux stations `nord`, `est`, `sud` et
`ouest`.

La remise au propre a rendu le cœur scientifique compréhensible, appelable sans
Django et protégé par des tests de non-régression simples. Les traitements
principaux, les figures statiques, les exports et l'interface Django ont été
exécutés avec succès dans l'environnement validé.

## 2. Repères dans le dépôt

```text
.
├── 3d_visualization/
│   ├── Data/                     # Entrées directement consommées
│   ├── Geoctd/                   # Configuration Django
│   ├── Ocean/
│   │   ├── Processing/           # Cœur scientifique
│   │   ├── Views/                # Adaptateurs et vues Django
│   │   └── templates/            # Pages interactives Plotly
│   └── manage.py
├── Ressources/
│   ├── CTD/                      # Données instrumentales et préparées
│   └── SOLA/                     # Extractions non utilisées
├── tests/                        # Tests de non-régression
└── README.md                     # Installation et utilisation
```

Le cœur scientifique se trouve dans
`3d_visualization/Ocean/Processing/` :

| Module | Responsabilité |
| --- | --- |
| `cnv.py` | lecture spécialisée des fichiers Sea-Bird `.cnv` |
| `coords.py` | conversion latitude/longitude vers un repère local métrique |
| `geo.py` | primitives du calcul géostrophique |
| `pipeline.py` | orchestration géostrophique indépendante de Django |
| `ekman.py` | calcul numérique d'Ekman indépendant de Django |
| `figures.py` | figures statiques Matplotlib |
| `shared.py` | adaptation du pipeline aux pages Django |

## 3. Données disponibles

### Données actives

Le pipeline actuel consomme exclusivement :

```text
3d_visualization/Data/Cnv/nord.cnv
3d_visualization/Data/Cnv/est.cnv
3d_visualization/Data/Cnv/sud.cnv
3d_visualization/Data/Cnv/ouest.cnv
3d_visualization/Data/Coords/stations_banyuls.csv
```

Les quatre CNV sont des profils préparés par bins de `1 dbar`. Le lecteur
utilise `prdM`, `density00`, `sal00` et `tv290C`.

### Données de traçabilité

- `Ressources/CTD/RAW_DATA/` conserve les mesures instrumentales, la
  configuration du capteur et des traitements intermédiaires
- `Ressources/CTD/SBE_DATA/` conserve une seconde copie des quatre CNV
  préparés
- `Ressources/CTD/position.txt` conserve les positions sources
- `Ressources/SOLA/` conserve deux extractions non utilisées par le
  pipeline actuel

## 4. Traitements disponibles

### Lecture CTD

`read_cnv_vars(path)` lit un fichier Sea-Bird `.cnv`, extrait les colonnes
reconnues, supprime les lignes incomplètes sélectionnées et retourne un
`pandas.DataFrame` ordonné de la surface vers le fond.

Entrée : chemin d'un fichier `.cnv` préparé compatible.

Sortie : colonnes `depth`, et selon leur présence `density`, `salinity` et
`temperature`.

### Coordonnées

`load_xy_from_csv(csv_path)` lit les stations, calcule leur barycentre puis
convertit latitude et longitude dans un repère local.

Entrée : CSV contenant `station`, `lat_deg` et `lon_deg`.

Sorties : dictionnaire `{station: (x, y)}` en mètres et métadonnées `lat0`,
`lon0`, `kx`, `ky`.

### Géostrophie

Le point d'entrée hors Django est
`run_geostrophic_pipeline(coordinates_path, cnv_paths, z_ref)`.

Le pipeline :

1. lit les quatre profils et les coordonnées
2. construit l'intersection exacte des profondeurs entières
3. ajuste un plan horizontal de densité aux quatre stations à chaque niveau
4. calcule les gradients de densité et le paramètre de Coriolis
5. intègre le vent thermique
6. impose une vitesse relative nulle au niveau disponible le plus proche de
   `z_ref`.

Le résultat contient notamment les profils, coordonnées, gradients, `rho0`,
`f`, `u`, `v`, la grille commune et la profondeur de référence retenue. Avec
les données actuelles et `z_ref = 50`, la grille commune va de `1` à `57 m`.

### Ekman

`compute_surface_ekman(...)` calcule un courant de surface à partir de la
vitesse et de la direction du vent, du coefficient de traînée, des densités,
de la viscosité turbulente et de la latitude.

Le résultat contient la tension de vent, le paramètre de Coriolis, la vitesse
de surface, le vecteur vent, le vecteur courant et les erreurs rencontrées.

Ce modèle simple produit uniquement un courant de surface avec une déviation
fixe de `45°` en hémisphère nord. Il n'utilise ni profil CTD ni observation de
vent.

### Figures

`Ocean.Processing.figures` retourne des objets Matplotlib pour :

- le plan des stations et leur barycentre
- les profils de densité, salinité ou température
- les profils de vitesse géostrophique
- l'hodographe des vecteurs géostrophiques

Ces fonctions sont appelables directement depuis Python. L'interface Django
fournit aussi des pages Plotly interactives et des exports PNG, SVG et PDF.

## 5. Validation et tests

L'environnement validé utilise Python `3.9.6`, Django `4.2.30`, NumPy `1.26.4`,
pandas `2.2.3` et Matplotlib `3.9.4`. Aucun manifeste de dépendances n'est
encore versionné.

La suite `tests/test_scientific_core.py` contient cinq tests couvrant :

- la lecture des quatre CNV actifs
- les coordonnées et le barycentre
- le pipeline géostrophique avec `z_ref = 50`
- le calcul d'Ekman avec les paramètres
- la création en mémoire des principales figures Matplotlib

Commande validée :

```bash
MPLCONFIGDIR=/tmp/matplotlib-ocean-project \
  .venv/bin/python -m unittest discover -s tests -v
```

Ces tests protègent les résultats actuels contre une modification involontaire.