# GamesDB

<p align="center">
  <img src="logo.png" alt="GamesDB logo" width="180">
</p>

Kit de utilidades para gestionar el árbol de juegos de la RG34XX (u otras consolas retro) desde Python. Expone herramientas para indexar rutas, generar datasets CSV y mantener respaldos incrementales de la tarjeta SD.

## Instalación con uv

La forma recomendada de gestionar dependencias es con [uv](https://docs.astral.sh/uv/):

```bash
# Instalar la última versión publicada
uv pip install .
```

Si estás trabajando desde el repositorio clonado, prepara el entorno reproducible con:

```bash
uv sync
```

Luego podrás ejecutar cualquier comando directo con `uv run`, por ejemplo `uv run gamesdb get-games`.

## Configuración

Edita `gamesdb/data/config/config.yaml` antes de ejecutar cualquier script:

- `server`: IP, usuario y puerto usados por las pruebas de conectividad y los scripts de conexión.
- `paths.target_dir`: raíz donde viven tus ROMs y carátulas (se usa para indexado y datasets).
- `paths.output_dir`: carpeta local para artefactos (e.g. `paths.txt`).
- `paths.sdcard_backup_dir`: carpeta donde se almacenan los snapshots diarios (`YYYY-MM-DD`) generados por `backup_ops`.

Asegúrate de tener montada la SD en `/mnt/sdcard` y contar con `rsync` y `sshpass` instalados.

## CLI oficial

Desde la versión actual se expone un `console_script` llamado `gamesdb` que agrupa los mismos flujos operativos. Si estás dentro del repo, invócalo con `uv run` para reutilizar el entorno sincronizado:

```bash
# Prueba de conectividad con el dispositivo
uv run gamesdb ping --count 2

# Generar/actualizar respaldo local de la SD
uv run gamesdb backup-sd

# Regenerar índices y datasets
uv run gamesdb paths
uv run gamesdb datasets

# Reindexar juegos (incluye reinserción automática desde games_to_include)
uv run gamesdb get-games

# Insertar juegos pendientes de games_to_include en el backup
uv run gamesdb push

# Restaurar el snapshot más reciente al dispositivo remoto
uv run gamesdb restore latest
```

Internamente el comando `get-games`:

- Normaliza los nombres de las carpetas como `NNN_Titulo`.
- Copia ROMs y carátulas desde el backup (`paths.roms_dir`) y genera miniaturas 256x160.
- Detecta carpetas creadas a mano en `games_to_include`, reinserta su contenido en la plataforma correcta (usando `emu_extensions.yaml`) y borra la carpeta original tras reindexar.

El comando `push` se apoya en `emu_extensions.yaml` para sugerir la plataforma según la extensión del ROM. Si hay ambigüedades, mostrará un listado y solicitará tu elección antes de copiar la ROM y su carátula al respaldo (`paths.roms_dir`) y limpiar la carpeta de staging. A continuación ejecuta `uv run gamesdb get-games` para regenerar el índice numerado y sincronizar las miniaturas.

## Desarrollo y pruebas

Instala las dependencias opcionales y ejecuta la suite integrada:

```bash
uv sync
uv run pytest gamesdb_tests
```

Los tests generan directorios locales según la configuración y verifican la conectividad con el servidor definido en el YAML (incluye ping de salud).

## Notas operativas

- Ejecuta `gamesdb/shellscripts/connect_to_rg34xx_sp.sh` para iniciar una sesión SSH usando las credenciales cargadas en el paquete.
- Los snapshots se sincronizan con `--delete`, así que el histórico reside únicamente en los subdirectorios fechados del backup. Mantén los que quieras conservar y elimina manualmente los que ya no necesites.
