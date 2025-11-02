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

1. **Probar conectividad (`ping`)**: ideal antes de cualquier operación para confirmar que la consola responde:
   ```bash
   uv run gamesdb ping --count 2
   ```
2. **Respaldar la SD (`backup-sd`)**: crea o actualiza el snapshot incremental en `paths.sdcard_backup_dir`.
   ```bash
   uv run gamesdb backup-sd
   ```
3. **Regenerar artefactos (`paths`, `datasets`)**: sincroniza `paths.txt` y los CSV para análisis o catálogos.
   ```bash
   uv run gamesdb paths
   uv run gamesdb datasets
   ```
4. **Reindexar juegos (`get-games`)**: numera carpetas, genera miniaturas y replica ROMs/caratulas al `target_dir`.
   ```bash
   uv run gamesdb get-games
   ```
5. **Insertar pendientes (`push`)**: toma ROMs y portadas desde `games_to_include`, las clasifica y las fusiona al respaldo.
   ```bash
   uv run gamesdb push
   ```
6. **Restaurar un snapshot (`restore`)**: copia al dispositivo una versión resguardada; usa `latest` o un nombre de snapshot específico.
   ```bash
   uv run gamesdb restore latest
   ```

### Flujo típico con la CLI

1. **Configurar rutas y credenciales**: actualiza `gamesdb/data/config/config.yaml` con tus rutas reales (`paths.target_dir`, `paths.output_dir`, `paths.games_to_include_dir`, `paths.sdcard_backup_dir`) y los datos de conexión; asegúrate de montar la SD en `/mnt/sdcard`.
2. **Preparar el entorno**: ejecuta `uv sync` y verifica que existan las carpetas locales usadas como staging y respaldo (`gamesdb_localdata/games_to_include`, `paths.sdcard_backup_dir`).
3. **Comprobar conectividad**: antes de copiar datos, lanza `uv run gamesdb ping --count 2` para confirmar que el dispositivo responde por SSH.
4. **Organizar inserciones nuevas**: coloca ROM + portada (o solo una portada para juegos ya indexados) en `games_to_include/<juego>/` y corre `uv run gamesdb push` para reclasificar, generar miniaturas y limpiar el staging.
5. **Reindexar la biblioteca**: después de cualquier cambio sobre los juegos, usa `uv run gamesdb get-games` para renumerar carpetas, copiar assets al `target_dir` y normalizar nombres.
6. **Mantener artefactos y respaldos**: regenera índices y datasets con `uv run gamesdb paths` y `uv run gamesdb datasets`; crea snapshots incrementales con `uv run gamesdb backup-sd` y restaura el más reciente cuando sea necesario con `uv run gamesdb restore latest`.

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

## Actualizar portadas

1. Verifica que `paths.roms_dir` y `paths.games_to_include_dir` apunten a rutas válidas en `gamesdb/data/config/config.yaml`. El paquete crea los directorios necesarios al importarse.
2. Si prefieres un ajuste manual directo, coloca la imagen nueva en `$(paths.roms_dir)/<Plataforma>/Imgs/` con el mismo nombre base que el ROM (por ejemplo `123_titulo.png`) y genera la miniatura con `uv run python -m gamesdb.thumbnailer portada_original.png $(paths.roms_dir)/<Plataforma>/Imgs/123_titulo.png`.
3. Como alternativa automatizada, crea dentro de `$(paths.games_to_include_dir)` una carpeta con el nombre del juego (acepta `NNN_Titulo` o el título sin prefijo), deja ahí el PNG actualizado y ejecuta `uv run gamesdb push`; el asistente generará la miniatura 256x160 y la renombrará según el juego ya indexado.
4. Ejecuta `uv run gamesdb get-games` para regenerar la carpeta destino (`paths.target_dir`) y propagar la carátula actualizada. Vuelve a correr `uv run gamesdb paths` o `uv run gamesdb datasets` si necesitas refrescar artefactos derivados.
5. Para preparar varias inserciones (ROM + portada) desde cero, crea una subcarpeta sin prefijo numérico dentro de `$(paths.games_to_include_dir)`, copia ahí el ROM y la imagen y lanza `uv run gamesdb push`. El asistente detecta la portada, genera la miniatura en la carpeta `Imgs` correspondiente y borra la carpeta de staging al finalizar.
