#!/usr/bin/env python3
"""
Gera proposta-ufg.docx a partir de proposta-ufg.tex.

A classe inf-ufg-modificado usa comandos custom (\\autor, \\capa, \\rosto, \\chapter)
que pandoc não conhece. Este script cria um wrapper LaTeX equivalente em
documentclass article com capa manual e roda pandoc para gerar o .docx.
"""
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "proposta-ufg.tex"
BUILD = HERE / "_docx_build.tex"
OUT = HERE / "proposta-ufg.docx"

CAPA_FOLHA_ROSTO = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[brazilian]{babel}
\usepackage{geometry}
\geometry{top=3cm, left=3cm, right=2cm, bottom=2cm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{float}
\usepackage{array}
\usepackage{longtable}
\usepackage{setspace}
\usepackage{hyperref}
\onehalfspacing

% Stub macro para figuras com fallback (mostra placeholder se imagem ausente)
\newcommand{\figcomfallback}[3]{%
    \IfFileExists{#1.pdf}{\includegraphics[width=#3]{#1}}{%
    \IfFileExists{#1.png}{\includegraphics[width=#3]{#1}}{%
    \fbox{\parbox{#3}{\centering\vspace{1.5cm}\textit{[Figura: #2]}\vspace{1.5cm}}}}}%
}

\begin{document}

% ============================== CAPA ==============================
\begin{titlepage}
\begin{center}
\large UNIVERSIDADE FEDERAL DE GOIÁS (UFG)\\[0.2cm]
\large INSTITUTO DE INFORMÁTICA (INF)\\[3cm]

\large ANTONIO J. F. DE ARRUDA\\
\large GIVANILDO DE SOUSA GRAMACHO\\
\large JUCELINO SANTOS SILVA\\
\large RONNY MARCELO ALIAGA MEDRANO\\
\large VANDERSON SOARES DARRIBA\\[3cm]

\Large\textbf{BiblioGen: Sistema de Gestão de Biblioteca com Assistente RAG e Recomendações}\\[1cm]

\vfill
\large GOIÂNIA\\
\large 2026
\end{center}
\end{titlepage}

% ============================== FOLHA DE ROSTO ==============================
\begin{titlepage}
\begin{center}
\large ANTONIO J. F. DE ARRUDA\\
\large GIVANILDO DE SOUSA GRAMACHO\\
\large JUCELINO SANTOS SILVA\\
\large RONNY MARCELO ALIAGA MEDRANO\\
\large VANDERSON SOARES DARRIBA\\[5cm]

\Large\textbf{BiblioGen: Sistema de Gest\~ao de Biblioteca com Assistente RAG e Recomenda\c{c}\~oes}\\[2cm]
\end{center}

\hfill\begin{minipage}{0.55\textwidth}
\small Monografia apresentada ao Programa de Pós--Graduação do Instituto de Informática da Universidade Federal de Goiás, como requisito parcial para obtenção do Certificado de Especialização em Pós-Graduação em Agentes Inteligentes (Turma 2).

\vspace{0.4cm}
\textbf{Área de concentração:} Inteligência Artificial

\vspace{0.4cm}
\textbf{Orientador:} Prof. Ronaldo M. da Costa
\end{minipage}

\vfill
\begin{center}
\large GOIÂNIA\\
\large 2026
\end{center}
\end{titlepage}

% ============================== SUM\'ARIO ==============================
\tableofcontents
\newpage

% ============================== CONTE\'UDO ==============================

"""

FOOT = "\n\\end{document}\n"


def extract_body(tex: str) -> str:
    """Extract content between '\\chapter{Equipe}' and '\\end{document}'."""
    start = tex.index(r"\chapter{Equipe}")
    end = tex.index(r"\end{document}")
    return tex[start:end]


def transform_body(body: str) -> str:
    """Adapt UFG-class commands so article class can render them."""
    # \chapter -> \section (top-level), \section -> \subsection, \subsection -> \subsubsection
    body = re.sub(r"\\subsection\{", r"\\subsubsection{", body)
    body = re.sub(r"\\section\{", r"\\subsection{", body)
    body = re.sub(r"\\chapter\{", r"\\section{", body)

    # Strip the \ifincluirstatus / \fi block (omit "Status da Implementação" from DOCX)
    body = re.sub(
        r"\\ifincluirstatus.*?\\fi\s*%[^\n]*\n",
        "\n",
        body,
        flags=re.DOTALL,
    )

    # Replace \figcomfallback{path}{description}{width} with a visible textual
    # placeholder that pandoc renders as a styled paragraph in the .docx.
    # Pandoc does not expand custom macros, so the placeholder is necessary
    # to make the figure slots obvious for the human reviewer.
    def repl_figcom(m: re.Match[str]) -> str:
        desc = m.group(2)
        return (
            r"\textbf{[Figura --- inserir aqui: " + desc + r"]}"
        )

    body = re.sub(
        r"\\figcomfallback\{([^}]+)\}\{([^}]+)\}\{[^}]+\}",
        repl_figcom,
        body,
    )
    return body


def main() -> None:
    src_text = SRC.read_text(encoding="utf-8")
    body = extract_body(src_text)
    body = transform_body(body)

    BUILD.write_text(CAPA_FOLHA_ROSTO + body + FOOT, encoding="utf-8")

    cmd = [
        "pandoc",
        str(BUILD),
        "-o",
        str(OUT),
        "--from=latex",
        "--to=docx",
        "--toc",
        "--number-sections",
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"OK: {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
