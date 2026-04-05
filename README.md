
# HTML2MD

HTML2MD is a lightweight Python CLI tool that converts HTML files into clean, readable Markdown. It includes smart preprocessing features to remove noise such as SVG icons, UI elements, and navigation blocks, and can automatically extract the main content from complex pages. This makes it especially useful for content migration, documentation workflows, and preparing high-quality input for AI/RAG pipelines.

## Project Setup (in Linux)

Make the depencies available:

### Install pipx

```sh
sudo apt update
sudo apt install pipx
pipx ensurepath
source ~/.bashrc
pipx --version
```

Install the script

```sh
pipx install html2md
```

Add the TOML file, install the script

```sh
pipx install -e . --force
pipx runpip html2md check
pip freeze > requirements.txt
```

## Add a new dependency

```sh
pipx inject html2md beautifulsoup4
pipx runpip html2md list
# Better option is to add the dependency to the TOML file and reinstall.
pipx reinstall html2md
```
