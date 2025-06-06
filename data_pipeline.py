# data_pipeline.py
import numpy as np
import pandas as pd
import xarray as xr
import os

# --- ÉTAPE 1: DÉFINIR NOTRE ZONE D'ÉTUDE (GRILLE FIXE) ---
print("1. Création de la grille d'analyse pour le Golfe de Gascogne...")
# Coordonnées du Golfe
LAT_MIN, LAT_MAX = 43.5, 47.5
LON_MIN, LON_MAX = -5.0, -1.5
# Résolution de notre grille (un point tous les 0.1 degrés)
RESOLUTION = 0.1

# Créer les vecteurs de latitude et longitude
lats_grid = np.arange(LAT_MIN, LAT_MAX, RESOLUTION)
lons_grid = np.arange(LON_MIN, LON_MAX, RESOLUTION)

# Créer la grille de points
lon_mesh, lat_mesh = np.meshgrid(lons_grid, lats_grid)
grid_df = pd.DataFrame({
    'latitude': lat_mesh.ravel(),
    'longitude': lon_mesh.ravel()
})
print(f"-> Grille créée avec {len(grid_df)} points.")


# --- ÉTAPE 2: SIMULATION DU TÉLÉCHARGEMENT & LECTURE DES DONNÉES ---
# Dans une vraie app, ici on téléchargerait les fichiers depuis Copernicus/Météo-France
print("\n2. Traitement des données sources (simulation)...")

# Pour cet exemple, nous créons un FAUX fichier NetCDF de température
# pour pouvoir tester le reste du code sans se connecter aux APIs.
def create_fake_netcdf_data():
    if os.path.exists('fake_temperature_data.nc'):
        return
    print("-> Création d'un fichier de données de température de test (fake_temperature_data.nc)...")
    lats_source = np.arange(43, 48, 0.05)
    lons_source = np.arange(-6, 0, 0.05)
    temps = 15 + 5 * np.random.rand(len(lats_source), len(lons_source))
    ds = xr.Dataset(
        {"sst": (("lat", "lon"), temps)},
        coords={"lat": lats_source, "lon": lons_source},
    )
    ds.to_netcdf("fake_temperature_data.nc")
create_fake_netcdf_data()


# --- ÉTAPE 3: TRAITEMENT ET PROJECTION SUR NOTRE GRILLE ---
print("\n3. Projection des données sur notre grille...")

# Lire notre faux fichier de données
source_data = xr.open_dataset("fake_temperature_data.nc")

# Pour chaque point de NOTRE grille, on va chercher la valeur la plus proche
# dans le fichier de données source. C'est le "ré-échantillonnage".
temperatures = source_data['sst'].sel(
    lat=xr.DataArray(grid_df['latitude'], dims="points"),
    lon=xr.DataArray(grid_df['longitude'], dims="points"),
    method='nearest'
).values - 273.15 # On suppose Kelvin -> Celsius

# Ajouter les données à notre DataFrame
grid_df['temp_surface_c'] = temperatures

# Ici, on ferait la même chose pour les autres variables (chlorophylle, vent...)
# Pour l'instant, on les simule pour avoir un fichier complet.
grid_df['chlorophylle_mg_m3'] = np.random.uniform(0.1, 1.5, len(grid_df))
grid_df['vent_noeuds'] = np.random.randint(5, 25, len(grid_df))

print("-> Données de température projetées.")
print("-> Données de chlorophylle et de vent simulées.")


# --- ÉTAPE 4: SAUVEGARDER LE RÉSULTAT DU JOUR ---
output_path = "data/daily_data.csv"
grid_df.to_csv(output_path, index=False, float_format='%.2f')
print(f"\n4. ✅ Pipeline terminé ! Les données du jour ont été sauvegardées dans '{output_path}'.")
print("\nAperçu des données prêtes à l'emploi :")
print(grid_df.head())