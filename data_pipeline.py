# data_pipeline.py
import numpy as np
import pandas as pd
import xarray as xr
import os
from datetime import datetime, timedelta
import subprocess
import shutil
import requests # For Météo-France API (even if placeholder)

# CMEMS Configuration (placeholders & Specifics for SST)
CMEMS_USERNAME_PLACEHOLDER = "YOUR_CMEMS_USERNAME"  # Emphasize this is a placeholder
CMEMS_PASSWORD_PLACEHOLDER = "YOUR_CMEMS_PASSWORD"  # Emphasize this is a placeholder
# General CMEMS URL, can be overridden in functions if needed
CMEMS_BASE_MOTU_URL = "https://nrt.cmems-du.eu/motu-web/Motu" # Example NRT URL

# Specifics for SST product
CMEMS_SST_MOTU_SERVER_URL = CMEMS_BASE_MOTU_URL
CMEMS_SST_SERVICE_ID = "SST_EUR_PHY_L4_NRT_010_001-TDS" # Example for L4 European SST
CMEMS_SST_PRODUCT_ID = "cmems_obs-sst_eur_phy_nrt_010_001" # Example product ID for L4 European SST
CMEMS_SST_VARIABLE = "analysed_sst"

# Specifics for Chlorophyll product (example for European NRT L4)
CMEMS_CHL_MOTU_SERVER_URL = CMEMS_BASE_MOTU_URL # Often the same server for NRT products
CMEMS_CHL_SERVICE_ID = "OCEANCOLOUR_EUR_CHL_L4_NRT_009_036-TDS" # Example: European Ocean Colour L4 NRT
CMEMS_CHL_PRODUCT_ID = "cmems_obs-oc_eur_chl-l4-nrt_009_036"   # Example: Corresponding product ID
CMEMS_CHL_VARIABLE = "CHL" # Typical variable name for Chlorophyll-a in mg/m^3

# Specifics for Ocean Currents product (example for European NRT MultiOBS)
CMEMS_CUR_MOTU_SERVER_URL = CMEMS_BASE_MOTU_URL
CMEMS_CUR_SERVICE_ID = "MULTIOBS_EUR_PHY_NRT_015_003-TDS" # Example Service ID
CMEMS_CUR_PRODUCT_ID = "cmems_obs_mob_eur_phy-cur_nrt_015_003" # Example Product ID
CMEMS_CUR_VAR_U = "uo"  # Standard name for eastward sea water velocity
CMEMS_CUR_VAR_V = "vo"  # Standard name for northward sea water velocity

# Météo-France Wind Configuration (Placeholders)
# METEOFRANCE_API_KEY = os.getenv("METEOFRANCE_API_KEY_PAYSANS") # Example, use proper env var management
# METEOFRANCE_WIND_PRODUCT_ID = "AROME_0_01_HD_VENT_SURFACE" # Example, verify actual product ID for wind
# METEOFRANCE_WAVE_PRODUCT_ID = "MFWAM_EUR_0_25_HD_WAVES" # Example, verify actual product ID for waves (e.g., MFWAM model)
# METEOFRANCE_BASE_URL = "https://public-api.meteofrance.fr/public/arome/v1/models" # Example for AROME, wave model might be different

# EMODnet Bathymetry Configuration
# User needs to manually download this file and place it in the specified path.
EMODNET_BATHYMETRY_FILEPATH = "data/bathymetry/emodnet_bay_of_biscay.tif"
# import rioxarray # Would be needed for actual GeoTIFF processing

# Tide & Moon Phase Configuration / Libraries
# import some_tide_api_client # Placeholder for a specific tide API client library
# from astral import Observer # Example for moon/sun calculations, if needed locally
# from astral.sun import sun  # Example
TIDE_API_KEY_PLACEHOLDER = os.getenv("YOUR_TIDE_API_KEY") # Placeholder for API key
TIDE_REFERENCE_PORT_LAT = 43.48 # Example for Bayonne/Anglet (Grande Plage)
TIDE_REFERENCE_PORT_LON = -1.56 # Example for Bayonne/Anglet (Grande Plage)


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

# --- Function to add Bathymetry (called in ÉTAPE 1 or early ÉTAPE 3) ---
def add_bathymetry_to_grid(grid_df: pd.DataFrame, emodnet_filepath: str) -> pd.DataFrame:
    """
    Adds bathymetry data to the grid_df from a local EMODnet GeoTIFF file.
    Uses placeholder logic if file exists, otherwise NaNs.
    """
    print("\n-> Tentative de traitement des données de bathymétrie EMODnet...")
    if os.path.exists(emodnet_filepath):
        print(f"   Fichier bathymétrie EMODnet trouvé: {emodnet_filepath}.")
        print("   NOTE: La logique de traitement réelle pour EMODnet (GeoTIFF) avec rioxarray n'est pas implémentée.")

        # --- Pseudocode for actual rioxarray processing ---
        # try:
        #     # Open the GeoTIFF file
        #     rds = rioxarray.open_rasterio(emodnet_filepath)
        #     # Optional: Clip to a slightly larger area than grid_df for efficiency if the GeoTIFF is global/large
        #     # min_lon, max_lon = grid_df['longitude'].min(), grid_df['longitude'].max()
        #     # min_lat, max_lat = grid_df['latitude'].min(), grid_df['latitude'].max()
        #     # rds_clipped = rds.rio.clip_box(minx=min_lon-0.1, miny=min_lat-0.1, maxx=max_lon+0.1, maxy=max_lat+0.1, crs="EPSG:4326")

        #     # Ensure it's in WGS84 (EPSG:4326) if not already (grid_df lats/lons are assumed WGS84)
        #     if rds.rio.crs and rds.rio.crs.to_string() != "EPSG:4326":
        #          rds_wgs84 = rds.rio.reproject("EPSG:4326")
        #     else:
        #          rds_wgs84 = rds # Already in WGS84 or no CRS info (assume WGS84)

        #     # Create DataArrays for latitude and longitude from grid_df for selection
        #     lats_da = xr.DataArray(grid_df['latitude'], dims="points")
        #     lons_da = xr.DataArray(grid_df['longitude'], dims="points")

        #     # Select bathymetry data at grid points. '.interp()' might be better than '.sel()' for continuous data.
        #     # Ensure the coordinates in the GeoTIFF are named 'x' and 'y' if using .sel or .interp directly.
        #     # Bathymetry values from EMODnet are typically negative (depths below sea level).
        #     # The .rio.reproject might change coord names, check rds_wgs84.coords
        #     # bathy_values_raw = rds_wgs84.sel(x=lons_da, y=lats_da, method="nearest").values.squeeze()
        #     # or using interp:
        #     # bathy_values_raw = rds_wgs84.interp(x=lons_da, y=lats_da, method="linear").values.squeeze()

        #     # grid_df['bathymetry_m'] = bathy_values_raw
        #     # print(f"-> Bathymétrie EMODnet réelle traitée et ajoutée. Vérifier les signes (normalement négatifs).")

        # except ImportError:
        #     print("   ⚠️ rioxarray non installé. Impossible de traiter le fichier GeoTIFF.")
        #     print("      Installation: pip install rioxarray")
        #     grid_df['bathymetry_m'] = np.random.uniform(-2000, -10, len(grid_df)) # Fallback to simulation
        #     print("   Utilisation de données de bathymétrie SIMULÉES car rioxarray est manquant.")
        # except Exception as e:
        #     print(f"   ❌ Erreur lors du traitement du fichier bathymétrique EMODnet: {e}")
        #     grid_df['bathymetry_m'] = np.random.uniform(-2000, -10, len(grid_df)) # Fallback to simulation
        #     print("   Utilisation de données de bathymétrie SIMULÉES suite à une erreur.")
        # --- End of Pseudocode ---

        # Functional placeholder for this subtask:
        grid_df['bathymetry_m'] = np.random.uniform(-2000, -10, len(grid_df)) # Simulated depths
        print("-> Bathymétrie SIMULÉE ajoutée (le fichier EMODnet a été trouvé, mais le traitement réel est un placeholder).")
    else:
        print(f"   Fichier bathymétrie EMODnet NON trouvé à: {emodnet_filepath}.")
        print("   La bathymétrie sera remplie avec NaN.")
        print("   NOTE: Téléchargez le fichier GeoTIFF depuis EMODnet et placez-le au chemin spécifié pour un traitement réel.")
        grid_df['bathymetry_m'] = np.nan
    return grid_df

# Appel de la fonction Bathymétrie après la création de la grille
grid_df = add_bathymetry_to_grid(grid_df, EMODNET_BATHYMETRY_FILEPATH)


# --- ÉTAPE 2: SIMULATION DU TÉLÉCHARGEMENT & LECTURE DES DONNÉES ---
# Dans une vraie app, ici on téléchargerait les fichiers depuis Copernicus/Météo-France
print("\n2. Traitement des données sources (simulation)...")

# Pour cet exemple, nous créons un FAUX fichier NetCDF de température
# pour pouvoir tester le reste du code sans se connecter aux APIs.
def create_fake_netcdf_data(file_path='fake_temperature_data.nc'):
    if os.path.exists(file_path):
        return
    print(f"-> Création d'un fichier de données de température de test ({file_path})...")
    lats_source = np.arange(43, 48, 0.05)
    lons_source = np.arange(-6, 0, 0.05)
    temps = 15 + 5 * np.random.rand(len(lats_source), len(lons_source)) # Températures en Celsius pour la simulation
    ds = xr.Dataset(
        {"sst": (("lat", "lon"), temps)}, # Nom de variable 'sst' comme dans les vrais fichiers
        coords={"lat": lats_source, "lon": lons_source},
    )
    ds.attrs['Conventions'] = 'CF-1.6'
    ds.attrs['title'] = 'Fake SST Data'
    ds.attrs['summary'] = 'Simulated sea surface temperature data for testing purposes.'
    ds.attrs['date_created'] = datetime.utcnow().isoformat()
    ds['lat'].attrs['units'] = 'degrees_north'
    ds['lat'].attrs['long_name'] = 'Latitude'
    ds['lon'].attrs['units'] = 'degrees_east'
    ds['lon'].attrs['long_name'] = 'Longitude'
    ds['sst'].attrs['units'] = 'degree_Celsius' # Unités Celsius directement
    ds['sst'].attrs['long_name'] = 'Sea Surface Temperature'
    ds['sst'].attrs['standard_name'] = 'sea_surface_temperature'
    ds.to_netcdf(file_path)

    # Add a time dimension to make it more similar to real CMEMS data
    # This is optional but can help avoid issues if later code expects a time dimension
    # For this specific task, keeping it simple without time dim for fake data.

# CMEMS Fetching Functions
def fetch_cmems_sst(date: datetime, lat_min: float, lat_max: float, lon_min: float, lon_max: float, output_dir="data/cmems") -> tuple[str | None, bool]:
    """
    Tente de télécharger les données SST de CMEMS pour une date et une zone données.
    En cas d'échec, copie les données de 'fake_temperature_data.nc' vers un fichier daté.
    Retourne un tuple: (chemin_du_fichier, is_real_data_flag)
    """
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"sst_{date.strftime('%Y%m%d')}.nc"
    output_path = os.path.join(output_dir, output_filename)
    is_real_data = False

    print(f"-> Tentative de téléchargement des données SST CMEMS pour {date.strftime('%Y-%m-%d')}...")

    # Formulate motuclient command
    motu_command = [
        "python3", "-m", "motuclient", # Ensure python3 is used if motuclient is installed for it
        "-u", CMEMS_USERNAME_PLACEHOLDER,
        "-p", CMEMS_PASSWORD_PLACEHOLDER,
        "-m", CMEMS_SST_MOTU_SERVER_URL,
        "-s", CMEMS_SST_SERVICE_ID,
        "-d", CMEMS_SST_PRODUCT_ID,
        "-x", str(lon_min), "-X", str(lon_max),
        "-y", str(lat_min), "-Y", str(lat_max),
        "-t", date.strftime('%Y-%m-%d %H:%M:%S'),
        "-T", (date + timedelta(days=1) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'), # End of the day
        "-v", CMEMS_SST_VARIABLE,
        "-o", output_dir, # motuclient will use this directory
        "-f", output_filename
    ]

    try:
        print(f"   Exécution de motuclient: {' '.join(motu_command)}")
        # Hide username and password in printout for security if needed in real logs, for now it's fine.
        result = subprocess.run(motu_command, capture_output=True, text=True, check=False, timeout=300) # 5 min timeout

        if result.returncode == 0:
            print(f"   ✅ Téléchargement CMEMS SST réussi. Données sauvegardées dans {output_path}")
            is_real_data = True
            return output_path, is_real_data
        else:
            print(f"   ⚠️ Échec du téléchargement CMEMS SST (code: {result.returncode}). Erreur:")
            print(f"   Stderr: {result.stderr}")
            print(f"   Stdout: {result.stdout}")

    except FileNotFoundError:
        print("   ⚠️ Erreur: motuclient non trouvé. Vérifiez l'installation et le PATH.")
    except subprocess.TimeoutExpired:
        print("   ⚠️ Erreur: Le téléchargement CMEMS SST a expiré (timeout).")
    except Exception as e:
        print(f"   ⚠️ Erreur inattendue lors du téléchargement CMEMS SST: {e}")

    # Fallback to fake data
    print("-> Basculement vers les données SST factices.")
    os.makedirs(output_dir, exist_ok=True) # Ensure directory exists again just in case
    fake_data_source_path = 'fake_temperature_data.nc' # Default name for the template

    # Ensure the base fake data exists
    if not os.path.exists(fake_data_source_path):
        print(f"   Création du fichier source factice: {fake_data_source_path}")
        create_fake_netcdf_data(file_path=fake_data_source_path)

    if not os.path.exists(fake_data_source_path): # If still not exists after attempt
        print(f"   ❌ Échec critique: Impossible de créer ou de trouver {fake_data_source_path}.")
        return None, False

    try:
        shutil.copy(fake_data_source_path, output_path)
        print(f"   Données SST factices copiées dans {output_path}")
        return output_path, False # False because it's fake data
    except Exception as e:
        print(f"   ❌ Erreur lors de la copie des données SST factices: {e}")
        return None, False

def fetch_cmems_chlorophyll(date: datetime, lat_min: float, lat_max: float, lon_min: float, lon_max: float, output_dir="data/cmems") -> tuple[str | None, bool]:
    """
    Tente de télécharger les données de Chlorophylle-a de CMEMS.
    En cas d'échec, retourne (None, False).
    """
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"chl_{date.strftime('%Y%m%d')}.nc"
    output_path = os.path.join(output_dir, output_filename)
    is_real_data = False

    print(f"-> Tentative de téléchargement des données Chlorophylle CMEMS pour {date.strftime('%Y-%m-%d')}...")

    motu_command_chl = [
        "python3", "-m", "motuclient",
        "-u", CMEMS_USERNAME_PLACEHOLDER,
        "-p", CMEMS_PASSWORD_PLACEHOLDER,
        "-m", CMEMS_CHL_MOTU_SERVER_URL,
        "-s", CMEMS_CHL_SERVICE_ID,
        "-d", CMEMS_CHL_PRODUCT_ID,
        "-x", str(lon_min), "-X", str(lon_max),
        "-y", str(lat_min), "-Y", str(lat_max),
        "-t", date.strftime('%Y-%m-%d %H:%M:%S'),
        "-T", (date + timedelta(days=1) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),
        "-v", CMEMS_CHL_VARIABLE,
        "-o", output_dir,
        "-f", output_filename
    ]

    try:
        print(f"   Exécution de motuclient pour CHL: {' '.join(motu_command_chl)}")
        result = subprocess.run(motu_command_chl, capture_output=True, text=True, check=False, timeout=300)

        if result.returncode == 0:
            print(f"   ✅ Téléchargement CMEMS CHL réussi. Données sauvegardées dans {output_path}")
            is_real_data = True
            return output_path, is_real_data
        else:
            print(f"   ⚠️ Échec du téléchargement CMEMS CHL (code: {result.returncode}). Erreur:")
            print(f"   Stderr: {result.stderr}")
            print(f"   Stdout: {result.stdout}")

    except FileNotFoundError:
        print("   ⚠️ Erreur: motuclient non trouvé pour CHL. Vérifiez l'installation et le PATH.")
    except subprocess.TimeoutExpired:
        print("   ⚠️ Erreur: Le téléchargement CMEMS CHL a expiré (timeout).")
    except Exception as e:
        print(f"   ⚠️ Erreur inattendue lors du téléchargement CMEMS CHL: {e}")

    # Fallback if download fails
    print(f"-> Échec du téléchargement des données Chlorophylle CMEMS. Aucune donnée CHL disponible pour {date.strftime('%Y-%m-%d')}.")
    return None, False


def fetch_cmems_currents(date: datetime, lat_min: float, lat_max: float, lon_min: float, lon_max: float, output_dir="data/cmems") -> tuple[str | None, bool]:
    """
    Tente de télécharger les données de courants océaniques (U et V) de CMEMS.
    En cas d'échec, retourne (None, False).
    """
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"cur_{date.strftime('%Y%m%d')}.nc"
    output_path = os.path.join(output_dir, output_filename)
    is_real_data = False

    print(f"-> Tentative de téléchargement des données Courants CMEMS pour {date.strftime('%Y-%m-%d')}...")

    # Note: motuclient usually requires variables to be specified one by one with multiple -v flags
    # However, some API versions or client interpretations might handle comma-separated.
    # For robustness, one could make two calls, or ensure the specific service supports multi-var requests this way.
    # Here, we'll try with multiple -v flags in the command list if that's standard for motuclient.py
    # Let's assume the client takes multiple --variable options.
    # The variable list for the command:
    variables_to_download = [
        "--variable", CMEMS_CUR_VAR_U,
        "--variable", CMEMS_CUR_VAR_V
    ]
    # Some products might have slightly different lat/lon names, e.g. 'latitude'/'longitude'
    # This example assumes 'lat'/'lon' are standard for the product. Adjust if needed.

    motu_command_cur = [
        "python3", "-m", "motuclient",
        "-u", CMEMS_USERNAME_PLACEHOLDER,
        "-p", CMEMS_PASSWORD_PLACEHOLDER,
        "-m", CMEMS_CUR_MOTU_SERVER_URL,
        "-s", CMEMS_CUR_SERVICE_ID,
        "-d", CMEMS_CUR_PRODUCT_ID,
        "-x", str(lon_min), "-X", str(lon_max),
        "-y", str(lat_min), "-Y", str(lat_max),
        "-t", date.strftime('%Y-%m-%d %H:%M:%S'),
        "-T", (date + timedelta(days=1) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),
        # Variables are added below
        "-o", output_dir,
        "-f", output_filename
    ]
    # Add variables to the command. The subprocess module expects all arguments as strings.
    for var_opt in variables_to_download:
        motu_command_cur.append(var_opt)

    try:
        print(f"   Exécution de motuclient pour Courants: {' '.join(motu_command_cur)}")
        result = subprocess.run(motu_command_cur, capture_output=True, text=True, check=False, timeout=300)

        if result.returncode == 0:
            print(f"   ✅ Téléchargement CMEMS Courants réussi. Données sauvegardées dans {output_path}")
            is_real_data = True
            return output_path, is_real_data
        else:
            print(f"   ⚠️ Échec du téléchargement CMEMS Courants (code: {result.returncode}). Erreur:")
            print(f"   Stderr: {result.stderr}")
            print(f"   Stdout: {result.stdout}")

    except FileNotFoundError:
        print("   ⚠️ Erreur: motuclient non trouvé pour Courants. Vérifiez l'installation et le PATH.")
    except subprocess.TimeoutExpired:
        print("   ⚠️ Erreur: Le téléchargement CMEMS Courants a expiré (timeout).")
    except Exception as e:
        print(f"   ⚠️ Erreur inattendue lors du téléchargement CMEMS Courants: {e}")

    print(f"-> Échec du téléchargement des données Courants CMEMS. Aucune donnée Courants disponible pour {date.strftime('%Y-%m-%d')}.")
    return None, False

# Météo-France Fetching Function (Placeholder)
def fetch_meteofrance_wind(date: datetime, lat_min: float, lat_max: float, lon_min: float, lon_max: float, output_dir="data/meteofrance") -> tuple[str | None, bool]:
    """
    Placeholder pour le téléchargement des données de vent de Météo-France.
    Simule toujours un échec pour l'instant.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"wind_mf_{date.strftime('%Y%m%d')}.grib2" # Example filename
    output_path = os.path.join(output_dir, output_filename)

    print(f"-> Tentative de téléchargement des données Vent Météo-France pour {date.strftime('%Y-%m-%d')} (Placeholder)...")

    # --- Début de la section de pseudocode pour le téléchargement réel ---
    # print("   NOTE: La logique de téléchargement réelle pour Météo-France n'est pas implémentée.")
    # if METEOFRANCE_API_KEY:
    #     headers = {"apikey": METEOFRANCE_API_KEY}
    #     # Example: Construct URL based on actual API specs for AROME model data
    #     # This would need specific product IDs, geographical selection mode (e.g., bbox), etc.
    #     # target_url = (
    #     #     f"{METEOFRANCE_BASE_URL}/{METEOFRANCE_WIND_PRODUCT_ID}/france?"
    #     #     f"date={date.strftime('%Y-%m-%dT%H:%M:%SZ')}&" # Example date format, API specific
    #     #     f"BBOX={lon_min},{lat_min},{lon_max},{lat_max}" # Example BBOX format
    #     # )
    #     # print(f"   Placeholder: Requête GET vers {target_url} avec headers.")
    #     # try:
    #     #     response = requests.get(target_url, headers=headers, timeout=60) # Example request
    #     #     response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)
    #     #     with open(output_path, 'wb') as f:
    #     #         f.write(response.content)
    #     #     print(f"   ✅ Téléchargement Météo-France Vent réussi (simulation). Données sauvegardées dans {output_path}")
    #     #     return output_path, True # Return True if successful
    #     # except requests.exceptions.RequestException as e:
    #     #     print(f"   ⚠️ Échec du téléchargement Météo-France Vent: {e}")
    #     # except Exception as e:
    #     #     print(f"   ⚠️ Erreur inattendue Météo-France Vent: {e}")
    # else:
    #     print("   Skipping Météo-France download: METEOFRANCE_API_KEY not set.")
    # --- Fin de la section de pseudocode ---

    print(f"-> Échec simulé du téléchargement des données Vent Météo-France pour {date.strftime('%Y-%m-%d')}.")
    return None, False

def fetch_meteofrance_waves(date: datetime, lat_min: float, lat_max: float, lon_min: float, lon_max: float, output_dir="data/meteofrance") -> tuple[str | None, bool]:
    """
    Placeholder pour le téléchargement des données de vagues de Météo-France.
    Simule toujours un échec pour l'instant.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"waves_mf_{date.strftime('%Y%m%d')}.grib2" # Example filename
    output_path = os.path.join(output_dir, output_filename)

    print(f"-> Tentative de téléchargement des données Vagues Météo-France pour {date.strftime('%Y-%m-%d')} (Placeholder)...")

    # --- Début de la section de pseudocode pour le téléchargement réel ---
    # print("   NOTE: La logique de téléchargement réelle pour Météo-France (Vagues) n'est pas implémentée.")
    # if METEOFRANCE_API_KEY:
    #     # Similar structure to wind download, but using METEOFRANCE_WAVE_PRODUCT_ID
    #     # target_url = f"{METEOFRANCE_BASE_URL_WAVES_API_OR_FTP_ENDPOINT}/{METEOFRANCE_WAVE_PRODUCT_ID}/..."
    #     # print(f"   Placeholder: Requête vers {target_url} pour les vagues.")
    #     # try:
    #     #     ... (logic similar to wind download) ...
    #     #     print(f"   ✅ Téléchargement Météo-France Vagues réussi (simulation). Données sauvegardées dans {output_path}")
    #     #     return output_path, True
    #     # except Exception as e:
    #     #     print(f"   ⚠️ Échec du téléchargement Météo-France Vagues: {e}")
    # else:
    #     print("   Skipping Météo-France wave download: METEOFRANCE_API_KEY not set.")
    # --- Fin de la section de pseudocode ---

    print(f"-> Échec simulé du téléchargement des données Vagues Météo-France pour {date.strftime('%Y-%m-%d')}.")
    return None, False

# --- Contextual Data Fetching Functions (Tides, Moon Phase) ---
def fetch_tide_data(date: datetime, ref_lat: float, ref_lon: float) -> dict | None:
    """
    Placeholder pour récupérer les données de marée pour un port de référence.
    Retourne un dictionnaire simulé d'événements de marée.
    """
    print(f"\n-> Tentative de récupération des données de marée pour {date.strftime('%Y-%m-%d')} à ({ref_lat}, {ref_lon}) (Placeholder)...")

    # --- Pseudocode for actual Tide API call ---
    # if TIDE_API_KEY_PLACEHOLDER:
    #     # client = some_tide_api_client.Client(api_key=TIDE_API_KEY_PLACEHOLDER)
    #     # try:
    #     #     tide_events = client.get_tides(latitude=ref_lat, longitude=ref_lon, start_date=date, end_date=date + timedelta(days=1))
    #     #     # Process tide_events into the desired dictionary format
    #     #     processed_tides = {
    #     #         "port_name": f"Lat:{ref_lat},Lon:{ref_lon} (API)",
    #     #         "date": date.strftime('%Y-%m-%d'),
    #     #         "tides": [{"type": e.type, "time": e.time.strftime('%H:%M'), "height_m": e.height} for e in tide_events],
    #     #         "source": "API Data"
    #     #     }
    #     #     print("   ✅ Données de marée récupérées depuis l'API (simulation).")
    #     #     return processed_tides
    #     # except Exception as e:
    #     #     print(f"   ⚠️ Échec de la récupération des données de marée depuis l'API: {e}")
    # else:
    #     print("   Skipping Tide API call: TIDE_API_KEY_PLACEHOLDER not set.")
    # --- End of Pseudocode ---

    # Fallback to hardcoded simulated data
    print("   Utilisation de données de marée simulées.")
    return {
        "port_name": f"Port ({ref_lat},{ref_lon}) (Simulated)",
        "date": date.strftime('%Y-%m-%d'),
        "tides": [
            {"type": "Low", "time": "06:30", "height_m": 0.8},
            {"type": "High", "time": "12:45", "height_m": 3.2},
            {"type": "Low", "time": "18:50", "height_m": 0.9},
            # Example of a tide that might be early next day but relevant to this day's cycle
            {"type": "High", "time": (date + timedelta(hours=24, minutes=55)).strftime('%Y-%m-%d %H:%M'), "height_m": 3.1}
        ],
        "source": "Simulated Data"
    }

def get_moon_phase(date: datetime) -> str:
    """
    Placeholder pour calculer la phase de la lune.
    Retourne une chaîne de caractères simulée.
    Libraries like astral or ephem could be used here.
    """
    print(f"\n-> Calcul de la phase de la lune pour {date.strftime('%Y-%m-%d')} (Placeholder)...")
    # --- Pseudocode for actual moon phase calculation ---
    # try:
    #     # Using astral library example:
    #     # city_info = astral.CityInfo("Biarritz", "France", "Europe/Paris", TIDE_REFERENCE_PORT_LAT, TIDE_REFERENCE_PORT_LON)
    #     # s = sun(city_info.observer, date=date) # Astral's sun calculation often needed for full astral setup
    #     # phase_deg = astral.moon.phase(date) # Returns 0-28
    #     # Basic mapping to phase name (astral doesn't give names directly)
    #     if 0 <= phase_deg < 1: phase_name = "New Moon"
    #     elif phase_deg < 6.5: phase_name = "Waxing Crescent"
    #     elif phase_deg < 7.5: phase_name = "First Quarter"
    #     elif phase_deg < 13.5: phase_name = "Waxing Gibbous"
    #     elif phase_deg < 14.5: phase_name = "Full Moon"
    #     elif phase_deg < 20.5: phase_name = "Waning Gibbous"
    #     elif phase_deg < 21.5: phase_name = "Last Quarter"
    #     else: phase_name = "Waning Crescent"
    #     print(f"   Phase de la lune calculée (simulation): {phase_name}")
    #     return f"{phase_name} (Calculated)"
    # except Exception as e:
    #     print(f"   ⚠️ Erreur lors du calcul de la phase de la lune: {e}")
    # --- End of Pseudocode ---

    print("   Utilisation d'une phase de lune simulée.")
    # Simple simulation based on day of month for variety in testing
    day_of_month = date.day
    if day_of_month < 4: return "New Moon (Simulated)"
    if day_of_month < 11: return "Crescent (Simulated)"
    if day_of_month < 18: return "Quarter/Gibbous (Simulated)"
    if day_of_month < 25: return "Full Moon (Simulated)"
    return "Waning Gibbous (Simulated)"


# --- ÉTAPE 2: TÉLÉCHARGEMENT & LECTURE DES DONNÉES --- (Modifié)
print("\n2. Téléchargement et lecture des données sources et contextuelles...")
current_date = datetime.now() # Use current date, or specific date for reproducibility
# current_date = datetime(2024, 1, 15) # Example for a specific date

# Télécharger/simuler les données CMEMS
sst_file_path, is_real_sst_data = fetch_cmems_sst(current_date, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX)
chl_file_path, is_real_chl_data = fetch_cmems_chlorophyll(current_date, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX)
cur_file_path, is_real_cur_data = fetch_cmems_currents(current_date, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX)

# Télécharger/simuler les données Météo-France
mf_wind_filepath, is_real_mf_wind_data = fetch_meteofrance_wind(current_date, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX)
mf_wave_filepath, is_real_mf_wave_data = fetch_meteofrance_waves(current_date, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX)

# Récupérer les données contextuelles (Marées, Phase de la Lune)
tide_data_today = fetch_tide_data(current_date, TIDE_REFERENCE_PORT_LAT, TIDE_REFERENCE_PORT_LON)
moon_phase_today = get_moon_phase(current_date)

print("\n--- Données Contextuelles du Jour ---")
if tide_data_today:
    print(f"Marées ({tide_data_today.get('port_name', 'N/A')}):")
    for tide_event in tide_data_today.get('tides', []):
        print(f"  - {tide_event['type']} à {tide_event['time']}, Hauteur: {tide_event['height_m']}m")
else:
    print("Aucune donnée de marée disponible.")
print(f"Phase de la Lune: {moon_phase_today}")
print("------------------------------------")


# La création de fake_temperature_data.nc est maintenant gérée dans fetch_cmems_sst si besoin.
# create_fake_netcdf_data() # Appel direct supprimé


# --- ÉTAPE 3: TRAITEMENT ET PROJECTION SUR NOTRE GRILLE ---
print("\n3. Projection des données sur notre grille...")

# Traitement SST
if sst_file_path and os.path.exists(sst_file_path):
    print(f"-> Chargement des données SST depuis {sst_file_path} (Réel: {is_real_sst_data})")
    try:
        source_sst_data = xr.open_dataset(sst_file_path)

        # Sélectionner la variable SST. Le nom peut varier.
        # Pour l'instant, on essaie 'analysed_sst' (CMEMS) puis 'sst' (fake data).
        # Une approche plus robuste serait de vérifier source_sst_data.data_vars
        sst_variable_name_in_file = CMEMS_SST_VARIABLE if CMEMS_SST_VARIABLE in source_sst_data.data_vars else 'sst'
        if sst_variable_name_in_file not in source_sst_data.data_vars:
            raise ValueError(f"Variable SST ('{CMEMS_SST_VARIABLE}' ou 'sst') non trouvée dans {sst_file_path}")

        print(f"   Utilisation de la variable: {sst_variable_name_in_file}")
        temperatures_raw = source_sst_data[sst_variable_name_in_file].sel(
            lat=xr.DataArray(grid_df['latitude'], dims="points"),
            lon=xr.DataArray(grid_df['longitude'], dims="points"),
            method='nearest'
        ).values

        # Conversion d'unités: CMEMS SST est souvent en Kelvin. Notre simulation est en Celsius.
        # Idéalement, vérifier les attributs 'units' du NetCDF.
        sst_units = source_sst_data[sst_variable_name_in_file].attrs.get('units', '').lower()

        if is_real_sst_data: # Assume real data might be Kelvin
            if 'kelvin' in sst_units or sst_units == 'k': # Basic check
                print(f"   Conversion de Kelvin ({sst_units}) vers Celsius.")
                temperatures_celsius = temperatures_raw - 273.15
            elif 'celsius' in sst_units or sst_units == 'c' or sst_units == 'degree_celsius': # More robust check for Celsius
                 print(f"   Les données SST sont déjà en Celsius ({sst_units}).")
                 temperatures_celsius = temperatures_raw
            else: # Unknown units, assume Kelvin as per typical CMEMS, but warn
                print(f"   Unités SST '{sst_units}' non reconnues ou absentes pour les données réelles. Tentative de conversion Kelvin -> Celsius.")
                print("   NOTE: Vérifier les unités réelles des données CMEMS SST et ajuster si nécessaire.")
                temperatures_celsius = temperatures_raw - 273.15
        else: # Fake data is already Celsius (or should be)
            if 'celsius' in sst_units or sst_units == 'degree_celsius':
                print(f"   Données SST factices en Celsius ({sst_units}). Aucune conversion.")
                temperatures_celsius = temperatures_raw
            else: # If fake data units are missing or not Celsius, still don't convert, but log it.
                print(f"   Données SST factices avec unités '{sst_units}'. Attendu 'degree_Celsius'. Aucune conversion appliquée.")
                temperatures_celsius = temperatures_raw

        grid_df['temp_surface_c'] = temperatures_celsius
        print("-> Données de température projetées.")

    except Exception as e:
        print(f"   ❌ Erreur lors du traitement du fichier SST {sst_file_path}: {e}")
        print("   Simulation des températures suite à l'erreur de traitement.")
        grid_df['temp_surface_c'] = np.random.uniform(10, 20, len(grid_df))

else:
    print("-> Aucune donnée SST (réelle ou factice) disponible. Simulation des températures.")
    grid_df['temp_surface_c'] = np.random.uniform(10, 20, len(grid_df)) # Valeur par défaut si échec


# Traitement Chlorophylle
if chl_file_path and is_real_chl_data and os.path.exists(chl_file_path):
    print(f"-> Chargement des données Chlorophylle réelles depuis {chl_file_path}")
    try:
        source_chl_data = xr.open_dataset(chl_file_path)

        chl_variable_name_in_file = CMEMS_CHL_VARIABLE if CMEMS_CHL_VARIABLE in source_chl_data.data_vars else 'chl'
        if chl_variable_name_in_file not in source_chl_data.data_vars:
            # Try another common one if the first fails, e.g. CHL1_N (for some products)
            chl_variable_name_in_file = 'CHL1_N' if 'CHL1_N' in source_chl_data.data_vars else chl_variable_name_in_file

        if chl_variable_name_in_file not in source_chl_data.data_vars:
             raise ValueError(f"Variable Chlorophylle ('{CMEMS_CHL_VARIABLE}', 'chl', or 'CHL1_N') non trouvée dans {chl_file_path}")

        print(f"   Utilisation de la variable Chlorophylle: {chl_variable_name_in_file}")

        # Projection sur la grille (similaire à SST)
        # Note: Assurez-vous que les noms de dimension (lat, lon) sont les mêmes dans le fichier CHL.
        # Si ce n'est pas le cas, il faudra les renommer ou adapter la sélection.
        # e.g., source_chl_data = source_chl_data.rename({'latitude': 'lat', 'longitude': 'lon'})

        chl_values = source_chl_data[chl_variable_name_in_file].sel(
            lat=xr.DataArray(grid_df['latitude'], dims="points"),
            lon=xr.DataArray(grid_df['longitude'], dims="points"),
            method='nearest'
        ).values

        grid_df['chlorophylle_mg_m3'] = chl_values
        # TODO: Vérifier les unités de CHL et convertir si nécessaire.
        # Les produits L4 NRT sont typiquement en mg/m^3.
        print(f"-> Données de Chlorophylle réelles projetées. Unités supposées mg/m^3.")

    except Exception as e:
        print(f"   ❌ Erreur lors du traitement du fichier Chlorophylle {chl_file_path}: {e}")
        print("   Simulation des données de Chlorophylle suite à l'erreur de traitement.")
        grid_df['chlorophylle_mg_m3'] = np.random.uniform(0.1, 1.5, len(grid_df))
else:
    if is_real_chl_data and not (chl_file_path and os.path.exists(chl_file_path)):
        print("-> Fichier de données Chlorophylle réel non trouvé après téléchargement supposé réussi. Simulation.")
    elif not is_real_chl_data and chl_file_path: # Should not happen with current logic
        print("-> Incohérence: Chemin de fichier CHL présent mais marqué comme non réel. Simulation.")
    # Default case: No real data attempted or download failed
    print("-> Aucune donnée de Chlorophylle réelle disponible, simulation des valeurs.")
    grid_df['chlorophylle_mg_m3'] = np.random.uniform(0.1, 1.5, len(grid_df))

# Traitement Courants
grid_df['eastward_current_m_s'] = np.nan # Initialize columns
grid_df['northward_current_m_s'] = np.nan

if cur_file_path and is_real_cur_data and os.path.exists(cur_file_path):
    print(f"-> Chargement des données Courants réelles depuis {cur_file_path}")
    try:
        source_cur_data = xr.open_dataset(cur_file_path)

        u_var_name = CMEMS_CUR_VAR_U if CMEMS_CUR_VAR_U in source_cur_data.data_vars else 'uo'
        v_var_name = CMEMS_CUR_VAR_V if CMEMS_CUR_VAR_V in source_cur_data.data_vars else 'vo'

        found_u = u_var_name in source_cur_data.data_vars
        found_v = v_var_name in source_cur_data.data_vars

        if found_u and found_v:
            print(f"   Utilisation des variables courants: U='{u_var_name}', V='{v_var_name}'")

            # Ensure lat/lon coordinate names match if they differ in currents product
            # Example: source_cur_data = source_cur_data.rename({'latitude': 'lat', 'longitude': 'lon'})

            u_values = source_cur_data[u_var_name].sel(
                lat=xr.DataArray(grid_df['latitude'], dims="points"),
                lon=xr.DataArray(grid_df['longitude'], dims="points"),
                method='nearest'
            ).values

            v_values = source_cur_data[v_var_name].sel(
                lat=xr.DataArray(grid_df['latitude'], dims="points"),
                lon=xr.DataArray(grid_df['longitude'], dims="points"),
                method='nearest'
            ).values

            grid_df['eastward_current_m_s'] = u_values
            grid_df['northward_current_m_s'] = v_values
            # TODO: Unit conversion if necessary. Assume m/s for now.
            print(f"-> Données de Courants réelles projetées. Unités supposées m/s.")
        else:
            if not found_u:
                print(f"   ⚠️ Variable courant Est ('{CMEMS_CUR_VAR_U}' ou 'uo') non trouvée dans {cur_file_path}.")
            if not found_v:
                print(f"   ⚠️ Variable courant Nord ('{CMEMS_CUR_VAR_V}' ou 'vo') non trouvée dans {cur_file_path}.")
            print("   Simulation des données de courants (NaN) car variables manquantes.")
            # Columns already initialized to np.nan

    except Exception as e:
        print(f"   ❌ Erreur lors du traitement du fichier Courants {cur_file_path}: {e}")
        print("   Simulation des données de courants (NaN) suite à l'erreur de traitement.")
        # Columns already initialized to np.nan
else:
    if is_real_cur_data and not (cur_file_path and os.path.exists(cur_file_path)):
        print("-> Fichier de données courants réel non trouvé après téléchargement supposé réussi. Simulation (NaN).")
    # Default case: No real data attempted or download failed
    print("-> Aucune donnée de courants réelle disponible, valeurs mises à NaN.")
    # Columns already initialized to np.nan

# Traitement Vent Météo-France
# Default simulation, will be overwritten if real data is processed successfully
grid_df['vent_noeuds'] = np.random.randint(5, 25, len(grid_df))
print("-> Vent (vitesse en noeuds) simulé (par défaut).")

if mf_wind_filepath and is_real_mf_wind_data and os.path.exists(mf_wind_filepath):
    print(f"-> Tentative de traitement des données Vent Météo-France réelles depuis {mf_wind_filepath}...")
    try:
        # Example GRIB loading - requires cfgrib engine and correct GRIB keys
        # ds_wind = xr.open_dataset(
        #     mf_wind_filepath,
        #     engine="cfgrib",
        #     backend_kwargs={'filter_by_keys': {'typeOfLevel': 'heightAboveGround', 'level': 10, 'stepType': 'instant'}}
        #     # Adjust keys based on GRIB file content: e.g. typeOfLevel: 'surface' or 'heightAboveGround', level for 10m winds.
        # )
        print("   NOTE: La logique de traitement réelle pour les données Vent Météo-France (GRIB) n'est pas implémentée.")

        # Placeholder variable names for U and V components at 10m
        # wind_u_var_name = 'u10' # Or '10u', check GRIB shortName or paramId
        # wind_v_var_name = 'v10' # Or '10v'

        # if wind_u_var_name in ds_wind and wind_v_var_name in ds_wind:
        #     u10_wind = ds_wind[wind_u_var_name]
        #     v10_wind = ds_wind[wind_v_var_name]

        #     # Calculate wind speed from U and V components
        #     # Data is likely on its own grid, needs projection to our grid_df
        #     # This is a complex step involving reprojection if grids don't match.
        #     # For simplicity, let's assume for this placeholder that we can select nearest like others.
        #     # This would need lat/lon alignment similar to other xr.sel operations.

        #     # wind_speed_ms_raw = np.sqrt(u10_wind**2 + v10_wind**2)

        #     # # Example projection (assuming ds_wind has 'latitude' and 'longitude' coordinates aligned with our needs)
        #     # wind_speed_ms_points = wind_speed_ms_raw.sel(
        #     #     latitude=xr.DataArray(grid_df['latitude'], dims="points"),
        #     #     longitude=xr.DataArray(grid_df['longitude'], dims="points"),
        #     #     method='nearest'
        #     # ).values

        #     # wind_speed_knots = wind_speed_ms_points * 1.94384 # Convert m/s to knots
        #     # grid_df['vent_noeuds'] = wind_speed_knots
        #     # print(f"-> Données de Vent Météo-France réelles projetées en noeuds.")
        # else:
        #     print(f"   ⚠️ Variables Vent U/V non trouvées dans {mf_wind_filepath}. Utilisation des données simulées.")

        # Since actual processing is not implemented, we explicitly state it and keep simulated data.
        print("   Traitement réel des données Vent non effectué. Utilisation des données simulées.")

    except Exception as e:
        print(f"   ❌ Erreur lors du traitement du fichier Vent Météo-France {mf_wind_filepath}: {e}")
        print("   Utilisation des données de vent simulées suite à l'erreur de traitement.")
        # Ensures vent_noeuds retains its simulated values if an error occurs here
else:
    if is_real_mf_wind_data and not (mf_wind_filepath and os.path.exists(mf_wind_filepath)):
        print("-> Fichier de données Vent Météo-France réel non trouvé après téléchargement supposé. Simulation.")
    # Default case: No real data attempted or download failed, message already printed by default simulation.

# Traitement Vagues Météo-France
grid_df['wave_height_m'] = np.nan
grid_df['wave_direction_deg'] = np.nan
grid_df['wave_period_s'] = np.nan
print("-> Données de vagues initialisées à NaN (placeholder).")

if mf_wave_filepath and is_real_mf_wave_data and os.path.exists(mf_wave_filepath):
    print(f"-> Tentative de traitement des données Vagues Météo-France réelles depuis {mf_wave_filepath}...")
    try:
        # Example GRIB loading for waves
        # ds_wave = xr.open_dataset(
        #     mf_wave_filepath,
        #     engine="cfgrib",
        #     backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}} # Or other relevant keys for wave products
        # )
        print("   NOTE: La logique de traitement réelle pour les données Vagues Météo-France (GRIB) n'est pas implémentée.")

        # Placeholder variable names for wave parameters
        # wave_height_var = 'VHM0'       # Significant wave height (e.g., from MFWAM)
        # wave_direction_var = 'VMDR_WW' # Mean wave direction from wind waves (e.g., from MFWAM)
        # wave_period_var = 'VTM02_WW'   # Mean period of wind waves (e.g., VTM02 in MFWAM) or primary/secondary period.
                                         # Could also be TMW, TP, etc. depending on product.

        # if wave_height_var in ds_wave and wave_direction_var in ds_wave and wave_period_var in ds_wave:
        #     swh_raw = ds_wave[wave_height_var]
        #     mwd_raw = ds_wave[wave_direction_var]
        #     mwp_raw = ds_wave[wave_period_var]

        #     # Project onto grid_df - similar complex step as wind if grids/coords don't match
        #     # grid_df['wave_height_m'] = swh_raw.sel(...).values
        #     # grid_df['wave_direction_deg'] = mwd_raw.sel(...).values
        #     # grid_df['wave_period_s'] = mwp_raw.sel(...).values
        #     print(f"-> Données de Vagues Météo-France réelles projetées.")
        #     # TODO: Ensure units are m, degrees, seconds. Add conversions if needed.
        # else:
        #     print(f"   ⚠️ Variables Vagues (hauteur, direction, période) non trouvées dans {mf_wave_filepath}. Valeurs restent NaN.")

        print("   Traitement réel des données Vagues non effectué. Valeurs restent NaN.")

    except Exception as e:
        print(f"   ❌ Erreur lors du traitement du fichier Vagues Météo-France {mf_wave_filepath}: {e}")
        print("   Valeurs des données de vagues restent NaN suite à l'erreur de traitement.")
else:
    if is_real_mf_wave_data and not (mf_wave_filepath and os.path.exists(mf_wave_filepath)):
        print("-> Fichier de données Vagues Météo-France réel non trouvé après téléchargement supposé. Valeurs restent NaN.")
    # Default case: No real data attempted or download failed, message already printed by initialization.


# --- ÉTAPE 4: SAUVEGARDER LE RÉSULTAT DU JOUR ---
output_dir_final = "data"
os.makedirs(output_dir_final, exist_ok=True) # S'assurer que le dossier de sortie final existe
output_path = os.path.join(output_dir_final, f"daily_data_{current_date.strftime('%Y%m%d')}.csv")
grid_df.to_csv(output_path, index=False, float_format='%.2f')
print(f"\n4. ✅ Pipeline terminé ! Les données du jour ont été sauvegardées dans '{output_path}'.")
print("\nAperçu des données prêtes à l'emploi :")
print(grid_df.head())