from io import BytesIO
from pathlib import Path
from html import escape

import qrcode
import streamlit as st


# =========================================================
# CONFIGURAÇÕES
# =========================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
PASTA_FOTOS = ROOT_DIR / "assets" / "time"

st.title("🏆 Conheça a equipe")
st.markdown(
    """
    Conheça as pessoas por trás do **HydroTwin**, um projeto que
    integra diferentes áreas do conhecimento para o monitoramento
    de sistemas hidropônicos.
    """
)

# =========================================================
# DADOS DOS DESENVOLVEDORES
# =========================================================

DESENVOLVEDORES = [
    {
        "nome": "Amanda Carolina Ambrizzi Ramin",
        "area": "Engenharia de Computação",
        "linkedin": "https://br.linkedin.com/in/amanda-ramin",
        "foto": "amanda.jpg",
    },
    {
        "nome": "Enzo Lipari Saisi",
        "area": "Engenharia de Controle e Automação",
        "linkedin": "https://br.linkedin.com/in/enzosaisi",
        "foto": "enzo.jpg",
    },
    {
        "nome": "Matheus Jorge Alves Lima",
        "area": "Engenharia de Controle e Automação",
        "linkedin": "https://br.linkedin.com/in/matheus-jorge-alves-lima",
        "foto": "matheus.jpg",
    },
    {
        "nome": "Murilo Invernort Nunes",
        "area": "Engenharia de Controle e Automação",
        "linkedin": "https://br.linkedin.com/in/murilo-invernort-41a1751b1",
        "foto": "murilo.jpg",
    },
]

# =========================================================
# DADOS DA ORIENTADORA
# =========================================================

ORIENTADORA = {
    "nome": "Andressa Corrente Martins",
    "area": "Orientação acadêmica",
    "linkedin": "https://www.linkedin.com/in/andressacorrentemartins/",
    "foto": "andressa.jpg",
}


# =========================================================
# GERAÇÃO DO QR CODE
# =========================================================

@st.cache_data(show_spinner=False)
def gerar_qrcode(url: str) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    imagem = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    arquivo = BytesIO()
    imagem.save(arquivo, format="PNG")

    return arquivo.getvalue()


# =========================================================
# COMPONENTES VISUAIS
# =========================================================

def renderizar_foto(nome_arquivo: str, tamanho: int = 120):
    caminho = PASTA_FOTOS / nome_arquivo

    if caminho.is_file():
        st.image(
            str(caminho),
            width=tamanho,
        )
    else:
        st.markdown(
            f"""
            <div style="
                width: {tamanho}px;
                height: {tamanho}px;
                margin: 0 auto;
                border-radius: 50%;
                background: rgba(128, 128, 128, 0.15);
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 48px;
            ">👤</div>
            """,
            unsafe_allow_html=True,
        )


def renderizar_pessoa(pessoa: dict, orientadora: bool = False):
    with st.container(border=True):
        # Foto centralizada
        _, coluna_foto, _ = st.columns([1, 2, 1])
        with coluna_foto:
            renderizar_foto(
                pessoa["foto"],
                tamanho=120 if orientadora else 100,
            )

        # Nome e área centralizados
        nome = escape(pessoa["nome"])
        area = escape(pessoa["area"])

        st.markdown(
            f"""
            <div style="
                text-align: center;
                min-height: 76px;
                padding-top: 12px;
                overflow-wrap: anywhere;
            ">
                <div style="
                    font-size: 16px;
                    font-weight: 650;
                    margin-bottom: 8px;
                ">{nome}</div>
                <div style="
                    font-size: 14px;
                    opacity: 0.75;
                ">{area}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # QR Code centralizado
        _, coluna_qr, _ = st.columns([1, 2, 1])
        with coluna_qr:
            st.image(
                gerar_qrcode(pessoa["linkedin"]),
                width=150,
            )

        # Botão centralizado
        _, coluna_botao, _ = st.columns([1, 3, 1])
        with coluna_botao:
            st.link_button(
                "Acessar LinkedIn",
                pessoa["linkedin"],
                use_container_width=True,
            )


st.divider()
st.subheader("Equipe do HydroTwin")

colunas = st.columns(
    [1, 1, 1, 1],
    gap="small",
)

# Quatro desenvolvedores
for indice, desenvolvedor in enumerate(DESENVOLVEDORES):
    with colunas[indice]:
        renderizar_pessoa(desenvolvedor)


st.divider()

st.subheader("Orientação acadêmica")

# Mantém o card da orientadora centralizado e mais estreito.
_, coluna_orientadora, _ = st.columns(
    [1, 1, 1],
    gap="medium",
)

with coluna_orientadora:
    renderizar_pessoa(ORIENTADORA, orientadora=True)