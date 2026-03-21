
# HTML2MD

Make the depencies available:

Install pipx

```sh
sudo apt update
sudo apt install pipx
pipx ensurepath
source ~/.bashrc
pipx --version
```

Is this installing the dependency globally?

```sh
pipx install html-to-markdown
```

Add the TOML file, install the script

```sh
pipx install .
pipx install -e .
```

## New dependency

```sh
pipx inject html2md beautifulsoup4
pipx runpip html2md list
# BEtter option is to add the dependency to the TOML file and reinstall.
pipx reinstall html2md
```
