TEMPLATE=r"""
%!TEX program = xelatex
%http://tex.stackexchange.com/questions/148843/how-to-write-over-a-table

\documentclass[UTF8, adobefonts, oneside, landscape]{ctexbook} \newcommand{\whzkjk}{\kaishu}
%\documentclass[oneside]{book} \input{setupfonts}

\usepackage{multicol}

\newcommand{\doctitle}{ {{ title }} }
\newcommand{\docdate}{ {{ date }} }
\newcommand{\docauthor}{Z.~Forest}
\newcommand{\dockeywords}{{ '{{中文}}' }}
\newcommand{\docsubject}{ {{ title }} }

{% raw %}
\usepackage{ifthen}
\usepackage{ifpdf}
\usepackage{ifxetex}
\usepackage{ifluatex}


\usepackage{amsfonts,amssymb}

\usepackage{color}
\usepackage[rgb]{xcolor}


\usepackage{tikz}
\usepackage{geometry}
%\geometry{margin = 2.1cm, papersize = {16cm, 13cm}}
\geometry{top=2cm, bottom=2cm, left=2cm, right=2cm,}
\linespread{0.833333}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhead[L]{\doctitle}
\fancyhead[C]{\docdate}
% \fancyfoot[R]{\thepage}

\makeatletter
\ExplSyntaxOn
\box_new:N \l_@@_grid_box % l means local
\coffin_new:N \l_@@_grid_coffin
\coffin_new:N \l_@@_charater_coffin
\int_const:Nn \c_@@_test_char { "4E00 }
\cs_new_protected_nopar:Npn \@@_update_grid_box:
  {
    \hbox_set:Nn \l_@@_grid_box
      { \XeTeXuseglyphmetrics = \c_zero \c_@@_test_char }
    \use:x
      {
        \@@_update_grid_box:nnn
          { \dim_use:N \box_wd:N \l_@@_grid_box } % width
          { \dim_use:N \box_ht:N \l_@@_grid_box } % height
          { \dim_use:N \box_dp:N \l_@@_grid_box } % depth
      }
    \coffin_attach:NnnNnnnn
      \l_@@_charater_coffin { hc } { vc }
      \l_@@_grid_coffin     { hc } { vc }
      { \c_zero_dim } { \c_zero_dim }
    \hbox_set:Nn \l_@@_grid_box
      {
        \coffin_typeset:Nnnnn \l_@@_charater_coffin
          { H } { l } { \c_zero_dim } { \c_zero_dim }
      }
    \box_set_wd:Nn \l_@@_grid_box { \c_zero_dim }
    \box_set_ht:Nn \l_@@_grid_box { \c_zero_dim }
    \box_set_dp:Nn \l_@@_grid_box { \c_zero_dim }
  }
\cs_new_protected_nopar:Npn \@@_update_grid_box:nnn #1#2#3
  {
    \hbox_set:Nn \l_@@_grid_box { }
    \box_set_wd:Nn \l_@@_grid_box {#1}
    \box_set_ht:Nn \l_@@_grid_box {#2}
    \box_set_dp:Nn \l_@@_grid_box {#3}
    \hcoffin_set:Nn \l_@@_charater_coffin { \box_use:N \l_@@_grid_box }
    \@@_draw_grid:nn {#1} { (#2) + (#3) }
  }
\cs_new_protected_nopar:Npn \@@_draw_grid:nn #1#2
  {
    \use:x
      {
        \@@_draw_grid_tian:nnnn { \dim_eval:n {#1} } { \dim_eval:n {#2} }
          { \dim_eval:n { (#1) / 2 } } { \dim_eval:n { (#2) / 2 } }
      }
  }
\cs_new_protected_nopar:Npn \@@_draw_grid:nnnn #1#2#3#4
  {
    \hcoffin_set:Nn \l_@@_grid_coffin
      {
        \begin{tikzpicture}
          \draw[help~lines, red] (0,#4) -- (#1,#4) (#3,0) -- (#3,#2);
          \draw[help~lines, red, dashed] (0,0) -- (#1,#2) (0,#2) -- (#1,0);
          \draw[help~lines, red, thick] (0,0) rectangle (#1,#2);
        \end{tikzpicture}
      }
  }
\cs_new_protected_nopar:Npn \@@_draw_grid_tian:nnnn #1#2#3#4
  {
    \hcoffin_set:Nn \l_@@_grid_coffin
      {
        \begin{tikzpicture}
          \draw[help~lines, red, dashed] (0,#4) -- (#1,#4) (#3,0) -- (#3,#2);
          \draw[help~lines, red, thick] (0,0) rectangle (#1,#2);
        \end{tikzpicture}
      }
  }
\cs_new_protected_nopar:Npn \@@_draw_grid:nnnnnn #1#2#3#4#5#6
  {
    \hcoffin_set:Nn \l_@@_grid_coffin
      {
        \begin{tikzpicture}
          \draw[help~lines, red, dashed] (0,#4) -- (#1,#4) (#3,0) -- (#3,#2) (0,#6) -- (#1,#6) (#5,0) -- (#5,#2);
          \draw[help~lines, red, thick] (0,0) rectangle (#1,#2);
        \end{tikzpicture}
      }
  }
\cs_new_protected_nopar:Npn \@@_grid_CJKsymbol:n
  { \box_use:N \l_@@_grid_box \@@_grid_CJKsymbol:n }
\cs_new_protected_nopar:Npn \@@_grid_CJKpunctsymbol:n
  { \box_use:N \l_@@_grid_box \@@_grid_CJKpunctsymbol:n }
\keys_define:nn { @@ }
  {
    format .tl_set:N  = \l_@@_formal_tl ,
    format .initial:n = { \normalfont }
  }
\cs_new_protected:Npn \@@_active_grid:n #1
  {
    \xeCJKsetup{PunctStyle=plain,CJKglue=\allowbreak,AllowBreakBetweenPuncts}
    \keys_set:nn { @@ } {#1}
    \tl_use:N \l_@@_formal_tl
    \@@_update_grid_box:
    \xeCJK_swap_cs:NN \CJKsymbol \@@_grid_CJKsymbol:n
    \xeCJK_swap_cs:NN \CJKpunctsymbol \@@_grid_CJKpunctsymbol:n
    \xeCJK_add_to_shipout:n
      {
        \xeCJK_swap_cs:NN \CJKsymbol \@@_grid_CJKsymbol:n
        \xeCJK_swap_cs:NN \CJKpunctsymbol \@@_grid_CJKpunctsymbol:n
      }
  }
\NewDocumentCommand \CJKgrid { +O { } +m }
  { \group_begin: \@@_active_grid:n {#1} #2 \relax \group_end: }
\NewDocumentEnvironment { CJKGrid } { +O { } }
  { \@@_active_grid:n {#1} } { \par }
\ExplSyntaxOff

%\newcommand\milinetwo[3]{\CJKgrid{\kaishu #1\color{gray!20} #1\color{white} #1 #2\color{gray!20} #1\color{white} #2 #2 #2 #3 #3 #3 #3 } \newline }
\newcommand\miline[1]{\CJKgrid{\kaishu #1\color{gray!20}\whzkjk #1\color{gray!20}\kaishu #1\color{white} #1 #1\whzkjk} }
\newcommand\mispace[1]{\CJKgrid{\color{white}\kaishu #1\color{white}\whzkjk #1\color{white}\kaishu #1\color{white} #1 #1\whzkjk} }


\ifxetex % xelatex
\else
    %The cmap package is intended to make the PDF files generated by pdflatex "searchable and copyable" in acrobat reader and other compliant PDF viewers.
    \usepackage{cmap}%
\fi
% ============================================
% Check for PDFLaTeX/LaTeX
% ============================================
\newcommand{\outengine}{xetex}
\newif\ifpdf
\ifx\pdfoutput\undefined
  \pdffalse % we are not running PDFLaTeX
  \ifxetex
    \renewcommand{\outengine}{xetex}
  \else
    \renewcommand{\outengine}{dvipdfmx}
  \fi
\else
  \pdfoutput=1 % we are running PDFLaTeX
  \pdftrue
  \usepackage{thumbpdf}
  \renewcommand{\outengine}{pdftex}
  \pdfcompresslevel=9
\fi
\usepackage[\outengine,
    bookmarksnumbered, %dvipdfmx
    %% unicode, %% 不能有unicode选项，否则bookmark会是乱码
    colorlinks=true,
    citecolor=red,
    urlcolor=blue,        % \href{...}{...} external (URL)
    filecolor=red,      % \href{...} local file
    linkcolor=black, % \ref{...} and \pageref{...}
    breaklinks,
    pdftitle={\doctitle},
    pdfauthor={\docauthor},
    pdfsubject={\docsubject},
    pdfkeywords={\dockeywords},
    pdfproducer={Latex with hyperref},
    pdfcreator={pdflatex},
    %%pdfadjustspacing=1,
    pdfborder=1,
    pdfpagemode=UseNone,
    pagebackref,
    bookmarksopen=true]{hyperref}

% --------------------------------------------
% Load graphicx package with pdf if needed 
% --------------------------------------------
\ifxetex    % xelatex
    \usepackage{graphicx}
\else
    \ifpdf
        \usepackage[pdftex]{graphicx}
        \pdfcompresslevel=9
    \else
        \usepackage{graphicx} % \usepackage[dvipdfm]{graphicx}
    \fi
\fi

{% endraw %}


\title{\doctitle}

\begin{document}
\setlength{\parindent}{0pt}
\zihao{0}
\begin{multicols}{3}
{% for word in words -%}
{% if word == " " %}{{ '\mispace{无}' }}{% else %}{{ '\miline{' + word + '}' }}{% endif %}
{% endfor -%}
\end{multicols}
\end{document}
"""

from jinja2 import Template

template = Template(TEMPLATE)
words='食 无 名 加 共,，'
words = words.replace(' ', '') + "    "
words = "".join([' ' if ord(x)<128 else x for x in words])
while len(words) % 36 != 0:
    words = words + " "
print(template.render(title='中文', date='2019-09-29', words=words))