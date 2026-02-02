# Czcionki w Ubuntu i LaTeX

## Listowanie czcionek w Ubuntu

```bash
# Wszystkie czcionki
fc-list

# Tylko nazwy czcionek (bardziej czytelne)
fc-list : family

# Posortowane unikalne nazwy
fc-list : family | sort -u

# Wyszukaj konkretną czcionkę
fc-list | grep -i "nazwa"

# Policz wszystkie czcionki
fc-list : family | sort -u | wc -l

# Szukaj czcionek serif/sans
fc-list : family | grep -i sans
fc-list : family | grep -i serif

# Pokaż ścieżki do plików czcionek
fc-list : file family
```

## Instalacja dodatkowych czcionek

```bash
sudo apt install fonts-liberation fonts-roboto fonts-open-sans fonts-firacode
```

## Użycie czcionki systemowej w LaTeX

Aby użyć czcionki systemowej w LaTeX, należy użyć **XeLaTeX** lub **LuaLaTeX** z pakietem `fontspec`:

```latex
\documentclass{article}
\usepackage{fontspec}

% Ustaw jako główną czcionkę
\setmainfont{Noto Sans Devanagari}

% LUB zdefiniuj jako osobną czcionkę do użycia
\newfontfamily\devanagarifont{Noto Sans Devanagari}

\begin{document}

% Jeśli ustawiono jako główną - po prostu pisz
Tekst w Noto Sans Devanagari

% Jeśli zdefiniowano jako osobną
{\devanagarifont Tekst w tej czcionce}

\end{document}
```

## Kompilacja

```bash
xelatex dokument.tex
# lub
lualatex dokument.tex
```
