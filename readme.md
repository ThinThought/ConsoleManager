# ThinThought Console Manager
<div align="center">
  <img src="logo4.png" alt="GamesDB" width="300" />
</div>

`thinthought-console-manager` es una herramienta para gestionar ROMs y portadas en consolas y servers basados en Linux. Facilita la transferencia, conexion, organización y generación de miniaturas para juegos retro.

El objetivo es obtener una herramienta sencilla y automatizable para mantener bibliotecas de videojuegos en consolas en 
en las que se pretende testear el software de HeWo.

## Requisites

- Python 3.13
- `uv` como gestor de paquetes

## Install 

```bash
uv pip install thinthought-console-manager
```

`uv` instala dependencias bloqueadas y permite ejecutar cualquier comando con `uv run`.


## CLI principal

### gamesdb
La CLI `gamesdb` ofrece comandos para gestionar la consola:

#### config set
Cambia la configuracion por defecto de config.yaml
```
uv run gamesdb config set <key> <value>
uv run gamesdb config set server.host localhost
```

#### ping
Checkea la conectividad con la consola en la red.
```
uv run gamesdb ping --count 2
```

#### connect
Abre una conexión SSH a la consola.
```
uv run gamesdb connect
```
#### get-games
Obtiene la lista de juegos en el ultimo backup de la consola, renumera y replica ROMs/portadas al `games_to_include`.
```
uv run gamesdb get-games
```
Esto crearia un directorio de staging con la siguiente estructura:
```
games_to_include/
├── xxx_game_title_1/
│   ├── xxx_game_title_1.rom
│   └── xxx_game_title_1.png
```
Cambie imagenes y nombres de juegos segun sus preferencias.

#### push
Procesa `games_to_include`, moviendo nuevos juegos a la consola y generando miniaturas.
```
uv run gamesdb push
```

#### paths
Obtiene los paths del target dir.
```
uv run gamesdb paths
```
#### datasets
Exporta datasets CSV de los juegos en el target dir.
```
uv run gamesdb datasets
```

#### backup-sd
Crea un snapshot incremental del sistema de archivos en tu tarjeta SD o restaura uno previo.
```
uv run gamesdb backup-sd
```
Creara un snapshot con el dia actual y `latest`. `latest` es el elegido para hacer procesamiento


#### backup-system
Realiza una copia de seguridad del sistema en la consola
```
uv run gamesdb backup-system
```

#### restore
restaura la tarjeta SD a un snapshot previo
```
uv run gamesdb restore <snapshot>
```


## Desarrollo y pruebas

```bash
uv run pip install -e .[dev]
```
