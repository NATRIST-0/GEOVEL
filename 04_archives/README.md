# Analyse océanographique de profils CTD autour de Banyuls

## Objectif scientifique

Ce dépôt contient un projet scientifique consacré à l'exploitation de
quatre profils CTD autour de Banyuls, aux stations `nord`, `est`, `sud` et
`ouest`.

Le traitement principal :

1. lit quatre fichiers Sea-Bird `.cnv` préparés à une résolution de 1 dbar
2. extrait la pression, la densité, la salinité et la température
3. assimile la pression en dbar à une profondeur en mètres
4. convertit les coordonnées géographiques des stations dans un repère local
5. ajuste un plan horizontal de densité à chaque profondeur commune
6. calcule des vitesses géostrophiques relatives par vent thermique
7. produit des figures de coordonnées, profils, vitesses et vecteurs.

Un second traitement, indépendant des profils CTD, calcule un courant d'Ekman
de surface à partir de paramètres de vent et de mélange vertical.

Le projet permet d'explorer et de visualiser ces traitements. Les résultats
actuels sont protégés par des tests de non-régression.

## Structure du dépôt

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

| Module | Rôle |
| --- | --- |
| `cnv.py` | lecture spécialisée des fichiers Sea-Bird `.cnv` |
| `coords.py` | conversion latitude/longitude vers un repère local métrique |
| `geo.py` | primitives du calcul géostrophique |
| `pipeline.py` | point d'entrée géostrophique indépendant de Django |
| `ekman.py` | calcul d'Ekman indépendant de Django |
| `figures.py` | figures statiques Matplotlib |
| `shared.py` | adaptation du pipeline pour les pages Django |

## Données

### Données utilisées par le pipeline

Le pipeline actif lit exclusivement :

```text
3d_visualization/Data/Cnv/nord.cnv
3d_visualization/Data/Cnv/est.cnv
3d_visualization/Data/Cnv/sud.cnv
3d_visualization/Data/Cnv/ouest.cnv
3d_visualization/Data/Coords/stations_banyuls.csv
```

Les quatre CNV contiennent des profils CTD Sea-Bird préparés et moyennés par
bins de 1 dbar. Le code utilise les variables `prdM`, `density00`, `sal00` et
`tv290C`, retournées comme profondeur, densité, salinité et température.

Les fichiers `3d_visualization/Data/Cnv/*.cnv` sont des copies identiques des
fichiers préparés présents dans `Ressources/CTD/SBE_DATA/`.

### Données conservées pour traçabilité

`Ressources/CTD/RAW_DATA/` contient les mesures instrumentales `.hex`, la
configuration du capteur, des exports texte et des CNV intermédiaires. Ces
fichiers ne sont pas lus par le pipeline actif et doivent être préservés.

`Ressources/CTD/position.txt` conserve les positions sources, reprises sous
forme structurée dans le CSV opérationnel.

`Ressources/SOLA/` contient deux extractions SOLA/SOMLIT. Aucun
module Python actuel ne les utilise elles sont conservées pour traçabilité et
pour de possibles analyses futures.

## Installation

L'environnement fonctionnel validé utilise Python 3.9.6 et les dépendances
suivantes :

| Dépendance | Version validée |
| --- | ---: |
| Django | 4.2.30 |
| NumPy | 1.26.4 |
| pandas | 2.2.3 |
| Matplotlib | 3.9.4 |

Depuis la racine du dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install Django==4.2.30 numpy==1.26.4 pandas==2.2.3 matplotlib==3.9.4
```

Le dépôt ne contient actuellement aucun manifeste de dépendances. Les versions
ci-dessus correspondent à l'environnement utilisé pour la validation
fonctionnelle, sans garantir qu'elles soient les seules versions compatibles.

### Exécuter les tests

```bash
MPLCONFIGDIR=/tmp/matplotlib-ocean-project \
  .venv/bin/python -m unittest discover -s tests -v
```

La suite contient cinq tests couvrant la lecture CNV, les coordonnées, le
pipeline géostrophique, le calcul d'Ekman et les principales figures
Matplotlib.

## Exécution des traitements scientifiques

Les commandes suivantes sont à lancer depuis la racine du dépôt.

### Pipeline géostrophique indépendant

```bash
PYTHONPATH=3d_visualization .venv/bin/python - <<'PY'
from pathlib import Path

from Ocean.Processing.pipeline import STATIONS, run_geostrophic_pipeline

data_dir = Path("3d_visualization/Data")
cnv_paths = {
    station: data_dir / "Cnv" / f"{station}.cnv"
    for station in STATIONS
}

result = run_geostrophic_pipeline(
    data_dir / "Coords" / "stations_banyuls.csv",
    cnv_paths,
    z_ref=50,
)

print("Grille commune :", result["z"][0], "à", result["z"][-1], "m")
print("Profondeur de référence :", result["z_ref"], "m")
print("Densité de référence :", result["rho0"], "kg/m³")
print("Paramètre de Coriolis :", result["f"], "s⁻¹")
print("u(1 m), v(1 m) :", result["u"][0], result["v"][0], "m/s")
PY
```

Le résultat contient notamment les profils chargés, les coordonnées locales,
la grille commune, les gradients horizontaux de densité et les composantes de
vitesse `u` et `v`.

### Calcul d'Ekman indépendant

```bash
PYTHONPATH=3d_visualization .venv/bin/python - <<'PY'
from Ocean.Processing.ekman import compute_surface_ekman

result = compute_surface_ekman(
    wind_speed=8.0,
    drag_coefficient=1.5e-3,
    air_density=1.3,
    water_density=1025.0,
    eddy_viscosity=0.01,
    wind_direction=0.0,
    latitude=42.483,
)

print("Vitesse de surface :", result["surface_speed"], "m/s")
print("Vecteur d'Ekman :", result["ekman_vector"])
print("Erreurs :", result["errors"])
PY
```

### Figures

Les fonctions de `Ocean.Processing.figures` produisent des objets Matplotlib
pour :

- le plan des stations et leur barycentre
- les profils de densité, salinité ou température
- les profils de vitesse géostrophique
- l'hodographe des vecteurs géostrophiques

Elles sont appelables directement depuis Python. L'interface Django permet
également d'exporter ces figures en PNG, SVG ou PDF.

## Interface Django

Django est une interface secondaire autour du cœur scientifique. Elle lit des
paramètres HTTP, appelle les traitements, affiche des figures interactives
Plotly et expose les exports statiques.

Pour la lancer localement :

```bash
cd 3d_visualization
../.venv/bin/python manage.py check
../.venv/bin/python manage.py runserver
```

Les pages principales sont alors disponibles sur :

```text
http://127.0.0.1:8000/coords/
http://127.0.0.1:8000/profiles/density/
http://127.0.0.1:8000/velocity/
http://127.0.0.1:8000/vectors/
http://127.0.0.1:8000/ekman/
```

Les graphiques interactifs chargent Plotly depuis un CDN externe et nécessitent
donc une connexion réseau.