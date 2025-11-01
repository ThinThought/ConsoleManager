# GamesDB

Hey pues nada es una simplita herramienta para gestionar los jueguinos.

Tengo hechos unos cuantos scripts pero no me acuerdo muy bien de como se usaban.


## To Do's
- [ ] Scripts de comunicacion con GameBoy Advance via ssh
- [ ] Scripts de insertacion de juegos en la base de datos
  - input: se precisara que en gamesdb_localdata haya un directorio llamado games_to_include
    - cada subdirectorio de games_to_include sera un juego a insertar
    - cada subdirectorio debe contener:
      - la rom del juego en el formato adecuado -- La extension debe indicar el formato --> Necesitamos un diccionario de plataformas y extensiones
      - la caratula del juego en el formato que sea --> se exporta a .png
  - [ ] debe insertar el juego en la plataforma correspondiente. El nombre del juego viene del directorio padre.
  - [ ] debe insertar la caratula del juego, procesada para su correcta visualizacion en la GameBoy
  - [ ] debe insertar la rom del juego. Sin comprimir para mejorar la velocidad de carga.
- [ ] Reindexacion de juegos. Se ordenan alfabeticamente por plataforma. Se anade un indice numerico delante del nombre del juego. y de la caratula.