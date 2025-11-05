# Console Manager
<div align="center">
  <img src="logo4.png" alt="GamesDB" width="300" />
</div>
Utilidades en Python para mantener bibliotecas de ROMs: inserta juegos, normaliza carátulas en miniaturas 256×160 y genera datasets a partir de respaldos de la RG34XX (u otras consolas retro).

## Instalación rápida

```bash
uv pip install .
```

`uv` instala dependencias bloqueadas y permite ejecutar cualquier comando con `uv run`.

## Configura primero

Actualiza `gamesdb/data/config/config.yaml` con tus rutas reales:

- Las rutas locales apuntan por defecto a `~/gamesdb_localdata/...`. GamesDB expande `~` y convierte cualquier ruta relativa en una dentro de tu `$HOME`, creando los directorios al cargar la configuración.
- Ajusta `paths.roms_dir`, `paths.games_to_include_dir`, `paths.sdcard_backup_dir`, `paths.artifacts_dir` y `paths.target_dir` si usas otra ubicación.
- Completa las credenciales del dispositivo en `server`.

> Tip: puedes editar valores desde la CLI con `uv run gamesdb config set paths.target_dir "~/otro/directorio"`. El comando valida la clave, guarda el YAML y recarga la configuración en caliente.

Asegúrate de tener montada la SD (ej. `/mnt/sdcard`) y contar con `rsync` y `sshpass`.

## CLI principal

El script `gamesdb` reúne los flujos diarios:


- `uv run gamesdb ping --count 2`: prueba conectividad antes de copiar datos.
- `uv run gamesdb push`: procesa staging (`games_to_include`) y genera miniaturas.
- `uv run gamesdb get-games`: renumera carpetas y replica ROMs/portadas al `target_dir`.
- `uv run gamesdb paths` y `uv run gamesdb datasets`: refrescan artefactos de navegación.
- `uv run gamesdb backup-sd` / `uv run gamesdb restore <snapshot>`: gestionan snapshots incrementales.

## Desarrollo y pruebas

```bash
uv run pytest gamesdb_tests/tests.py -v
```

Los tests crean directorios temporales y dependen de la configuración cargada en `config.yaml`.

### Qué valida cada test

- `test_generate_paths`: `get_paths` escribe `paths.txt` en el directorio de artefactos (`OUTPUT_DIR`/`paths.artifacts_dir`).
- `test_set_config_value_updates_custom_file`: `set_config_value` actualiza un YAML arbitrario y reporta los cambios.
- `test_resolve_config_path_prefers_env_override`: `resolve_config_path` prioriza `GAMESDB_CONFIG_PATH`.
- `test_export_datasets`: `export_dataset` produce CSV por cada subdirectorio válido de `TARGET_DIR`.
- `test_server_ping`: comprueba conectividad ICMP con la consola configurada.
- `test_thumbnailer_parser_handles_paths`: el parser CLI entrega `Path` para `thumbnailer`.
- `test_get_games_reindexes_rom_and_png`: `get_games` renumera, copia assets y genera miniaturas mientras limpia residuos.
- `test_push_games_inserts_staged_title`: `push_games` mueve nuevos juegos, asigna índice y elimina staging obsoleto.
- `test_push_games_updates_cover_only`: `push_games` reemplaza solo carátulas existentes manteniendo el ROM.
- `test_push_games_overwrites_numbered_rom`: `push_games` sobrescribe un ROM numerado y regenera la miniatura.
- `test_push_games_removes_previous_slug_entries`: `push_games` reindexa un slug, elimina versiones antiguas y recompone la portada.

## Atajos útiles

- `gamesdb/shellscripts/connect_to_rg34xx_sp.sh`: abre SSH con la configuración cargada.
- `uv run python -m gamesdb.thumbnailer portada.png destino.png`: genera miniaturas manualmente.
- Mantén snapshots en `paths.sdcard_backup_dir`; cada ejecución de `backup-sd` aplica `rsync --delete`, así que conserva los subdirectorios fechados que quieras preservar.
