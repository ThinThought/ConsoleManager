# GamesDB

Kit de utilidades para gestionar el árbol de juegos de la RG34XX (u otras consolas retro) desde Python. Expone herramientas para indexar rutas, generar datasets CSV y mantener respaldos incrementales de la tarjeta SD.

## Instalación

```bash
pip install gamesdb
```

Al instalar el paquete se resuelven automáticamente las rutas declaradas en `gamesdb/data/config/config.yaml`. Si trabajas localmente con el repo, también puedes hacer:

```bash
pip install -e .
```

## Configuración

Edita `gamesdb/data/config/config.yaml` antes de ejecutar cualquier script:

- `server`: IP, usuario y puerto usados por las pruebas de conectividad y los scripts de conexión.
- `paths.target_dir`: raíz donde viven tus ROMs y carátulas (se usa para indexado y datasets).
- `paths.output_dir`: carpeta local para artefactos (e.g. `paths.txt`).
- `paths.sdcard_backup_dir`: carpeta donde se almacenan los snapshots diarios (`YYYY-MM-DD`) generados por `backup_ops`.

Asegúrate de tener montada la SD en `/mnt/sdcard` y contar con `rsync` y `sshpass` instalados.

## Uso básico

El paquete está pensado para ser importado desde tus propios scripts:

```python
from gamesdb import TARGET_DIR, OUTPUT_DIR, DATASETS_DIR
from gamesdb.get_paths import get_paths
from gamesdb.tree_to_csv_datasets import export_dataset
from gamesdb.backup_ops import run_backup, restore_backup

# Generar listado de rutas
get_paths(TARGET_DIR, OUTPUT_DIR / "paths.txt")

# Exportar datasets CSV para cada subdirectorio
for subdir in TARGET_DIR.iterdir():
    if subdir.is_dir():
        export_dataset(DATASETS_DIR, subdir)

# Crear snapshot diario y restaurar uno existente
run_backup()
restore_backup("2024-11-01")
```

Cada helper respeta la configuración cargada en `gamesdb/data/config/config.yaml`, por lo que no necesitas pasar rutas manualmente.

## Uso CLI (opcional)

El repositorio incluye `main.py` para invocar los mismos flujos desde la terminal:

```bash
python main.py paths --output ./gamesdb_localdata/paths.txt
python main.py datasets
python main.py backup
python main.py restore 2024-11-01
python main.py ping --count 2
```

## Desarrollo y pruebas

Instala las dependencias opcionales y ejecuta la suite integrada:

```bash
pip install .[dev]
pytest gamesdb_tests
```

Los tests generan directorios locales según la configuración y verifican la conectividad con el servidor definido en el YAML (incluye ping de salud).

## Notas operativas

- Ejecuta `gamesdb/shellscripts/connect_to_rg34xx_sp.sh` para iniciar una sesión SSH usando las credenciales cargadas en el paquete.
- Los snapshots se sincronizan con `--delete`, así que el histórico reside únicamente en los subdirectorios fechados del backup. Mantén los que quieras conservar y elimina manualmente los que ya no necesites.
