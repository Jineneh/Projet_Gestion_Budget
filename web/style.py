"""Style de l'interface : palette rose et mauve, titres en serif, panneaux à bandeau."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Montserrat:wght@400;500;600&display=swap');
:root {
  --encre: #2A1F24; --creme: #FDF6F7; --rose-clair: #F5D2D8; --rose: #E39BB2;
  --mauve: #C9A3B8; --mauve-fonce: #8E6580; --trait: rgba(58,45,51,.35);
  --serif: 'Cormorant Garamond', Georgia, 'Times New Roman', serif;
}
.stApp { background: linear-gradient(180deg,#D9B0C3 0%,#F0C6D4 26%,#F8E7EA 60%,#FBF1F0 100%);
         font-family: 'Montserrat', 'Segoe UI', sans-serif; color: var(--encre); }
header[data-testid="stHeader"], footer, #MainMenu, [data-testid="stToolbar"],
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
.block-container { max-width: 1260px; padding-top: 1.4rem; padding-bottom: 3rem; }
h1, h2, h3, h4 { font-family: var(--serif); color: var(--encre); }

.titre-carte { background: rgba(253,246,247,.93); border: 1px solid var(--trait);
  border-radius: 18px; text-align: center; padding: 1.5rem 1rem 1.2rem; margin-bottom: 1rem; }
.titre-carte h1 { font-family: var(--serif); font-weight: 600; font-size: 3.1rem; margin: 0;
  line-height: 1.05; padding: 0; }
.titre-carte p { margin: .55rem 0 0; font-size: .74rem; letter-spacing: .2em; text-transform: uppercase; }

.panneau { background: var(--creme); border: 1px solid var(--trait); border-radius: 4px;
  overflow: hidden; margin-bottom: 1rem; }
.panneau-entete { padding: .55rem .8rem; text-align: center; font-size: .66rem; font-weight: 600;
  letter-spacing: .22em; text-transform: uppercase; background: var(--rose-clair); }
.teinte-mauve .panneau-entete { background: var(--mauve); }
.teinte-peche .panneau-entete { background: #F3D9CE; }
.panneau-corps { padding: .9rem 1rem 1rem; }
.centre { text-align: center; }

.mois-nom { font-family: var(--serif); font-size: 2rem; font-weight: 600; text-align: center; white-space: nowrap;
  line-height: 1.1; margin: .3rem 0 .2rem; }
.mois-periode { text-align: center; font-size: .78rem; opacity: .8; }
.mini-stats { display: flex; justify-content: space-around; margin-top: 1rem;
  border-top: 1px dotted var(--trait); padding-top: .8rem; text-align: center; }
.mini-stats b { display: block; font-family: var(--serif); font-size: 1.5rem; font-weight: 600; }
.mini-stats span { font-size: .62rem; letter-spacing: .14em; text-transform: uppercase; }

.legende { list-style: none; margin: .4rem 0 0; padding: 0; font-size: .76rem; }
.legende li { display: flex; align-items: center; justify-content: space-between;
  padding: .18rem 0; border-bottom: 1px dotted rgba(58,45,51,.2); }
.legende .pt { width: .6rem; height: .6rem; border-radius: 50%; display: inline-block; margin-right: .5rem; }

.barres { font-size: .76rem; }
.barres .ligne { margin-bottom: .75rem; }
.barres .nom { display: flex; justify-content: space-between; margin-bottom: .2rem; }
.barres .piste { height: .5rem; background: #F4E3E6; border-radius: 3px; margin-bottom: .18rem; position: relative; }
.barres .remplie { height: 100%; border-radius: 3px; }
.barres .cle { display: flex; gap: 1rem; font-size: .66rem; letter-spacing: .08em; margin-bottom: .6rem; }

table.suivi { width: 100%; table-layout: auto; border-collapse: collapse; font-size: .76rem; }
table.suivi th { font-size: .6rem; letter-spacing: .16em; text-transform: uppercase; font-weight: 600;
  text-align: left; padding: .45rem .4rem; border-bottom: 1px solid var(--trait); }
table.suivi td { padding: .45rem .4rem; border-bottom: 1px dotted rgba(58,45,51,.28); vertical-align: middle; }
table.suivi th, table.suivi td { border-left: none; border-right: none; }
table.suivi .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
table.suivi tr.total td { font-weight: 600; border-top: 1px solid var(--trait); border-bottom: none; }
.defile { max-height: 24rem; overflow-y: auto; }

.pastille { display: inline-block; padding: .12rem .7rem; border-radius: 999px; font-size: .68rem;
  font-weight: 600; letter-spacing: .04em; white-space: nowrap; }
.p-ok { background: #CFE7D8; color: #24593C; } .p-attention { background: #F8DDB4; color: #7A4A06; }
.p-depassement { background: #F4B9C0; color: #7C1D2B; } .p-aucune { background: #E6E0E3; color: #5B5257; }
.jauge { height: .4rem; background: #F1DEE2; border-radius: 3px; min-width: 3rem; }
.jauge div { height: 100%; border-radius: 3px; }

.bandeau { border: 1px solid var(--trait); border-radius: 4px; padding: .7rem 1rem; margin-bottom: 1rem;
  font-size: .82rem; background: #FBE9D3; }
.bandeau.rouge { background: #F8D2D6; }
.bandeau.vert { background: #DCEFE3; }
.bandeau b { font-weight: 600; }

.indicateur { text-align: center; padding: .4rem 0; }
.indicateur .valeur { font-family: var(--serif); font-size: 2rem; font-weight: 600; line-height: 1.1; }
.indicateur .libelle { font-size: .62rem; letter-spacing: .16em; text-transform: uppercase; }
.indicateur .note { font-size: .72rem; opacity: .75; }

.etape { display: flex; gap: 1rem; align-items: flex-start; }
.etape .numero { font-family: var(--serif); font-size: 2.6rem; line-height: 1; color: var(--mauve-fonce); min-width: 2rem; }
.etape h4 { margin: 0 0 .15rem !important; padding: 0 !important; font-size: 1.25rem; }
.etape p { margin: 0 !important; font-size: .82rem; }
pre.rapport { background: transparent; border: none; font-size: .82rem; line-height: 1.55; margin: 0;
  font-family: 'Courier New', monospace; white-space: pre-wrap; }

/* Navigation : boutons radio affichés comme des onglets */
[data-testid="stRadioGroup"] { gap: .3rem; flex-wrap: wrap; }
label[data-testid="stRadioOption"] { background: rgba(253,246,247,.8); border: 1px solid var(--trait);
  border-radius: 999px; padding: .3rem 1.05rem; margin: 0; cursor: pointer; }
label[data-testid="stRadioOption"] > div > div:first-child { display: none; }
label[data-testid="stRadioOption"] p { font-size: .76rem; font-weight: 500; letter-spacing: .06em; margin: 0; }
label[data-testid="stRadioOption"][data-selected="true"] { background: var(--mauve-fonce); border-color: var(--mauve-fonce); }
label[data-testid="stRadioOption"][data-selected="true"] p { color: white; }

/* Panneaux contenant des widgets */
[class*="st-key-panneau_"] { background: var(--creme); border: 1px solid var(--trait); border-radius: 4px;
  padding: 0 1rem 1rem; margin-bottom: 1rem; }
[class*="st-key-panneau_"] .panneau-entete { margin: 0 -1rem .5rem; }
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  border-radius: 999px; border: 1px solid var(--mauve-fonce); background: transparent; color: var(--encre);
  font-size: .78rem; letter-spacing: .05em; padding: .35rem 1.2rem; }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {
  background: var(--mauve-fonce); color: white; border-color: var(--mauve-fonce); }
div[data-baseweb="input"], div[data-baseweb="select"] > div { background: white; border-radius: 6px; }
label p { font-size: .72rem; letter-spacing: .08em; }
button[data-baseweb="tab"] p { font-size: .78rem; letter-spacing: .08em; }
</style>
"""
