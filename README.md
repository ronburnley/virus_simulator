# Virus Simulator

This repo contains a simple Pygame-based virus simulator. To run locally, install the dependencies and execute `main.py`:

```bash
pip install -r requirements.txt
python main.py
```

## Building a Web Version

This project can also be compiled for the browser using [pygbag](https://github.com/pygame-web/pygbag). After installing the dependencies, run:

```bash
pygbag --build main.py
```

The command creates a `build/web` directory containing a standalone web version. Host the contents of that directory using any static file server (for example, `python -m http.server`). Open the generated `index.html` to run the simulator in a web browser.
