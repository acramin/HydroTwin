from __future__ import annotations

from typing import Any
import pandas as pd
import streamlit as st
import altair as alt

from hydrotwin import (
    get_raw_recent,
    get_sensor_proc_ultimo,
    get_limites_bancada,
    detectar_anomalias,
    analisar_tendencias,
    logger
)

# --- CONSTANTES ---
COLUNAS_PREVISAO = [
    "nome",
    "status",
    "score",
    "media_antiga",
    "media_recente",
    "variacao_percentual",
]

COLUNAS_ANOMALIA = [
    "nome",
    "status",
    "score",
    "valor_atual",
    "media_recente",
    "desvio_percentual",
    "mensagem",
]

VARIAVEIS_ZONA_FORTES = [
    ("ph", "pH", ""),
    ("ec", "EC", "mS/cm"),
    ("luminosidade", "Luminosidade", "lux")
]

COR_ZONA_SAUDAVEL = "#d1e7dd"
COR_ZONA_ATENCAO = "#fff3cd"
COR_ZONA_CRITICO = "#f8d7da"


# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=60)
def carregar_monitoramento_bancada(bancada_id: int | str, horas: int = 24) -> dict[str, Any]:
    """Carrega e processa os dados de monitoramento da bancada.
    
    Utiliza cache de 60 segundos para otimizar re-execuções no Streamlit.
    """
    logger.debug("carregar_monitoramento_bancada(bancada_id: int | str, horas: int = 24) -> dict[str, Any]")
    df = get_raw_recent(bancada_id=bancada_id, horas=horas)
    proc = get_sensor_proc_ultimo(bancada_id)

    if df is None:
        df = pd.DataFrame()

    if not df.empty:
        df = df.copy()
        df["dth_recebido"] = pd.to_datetime(df["dth_recebido"], errors="coerce")
        df = df.dropna(subset=["dth_recebido"]).sort_values("dth_recebido")

    limites = get_limites_bancada(bancada_id)
    #logger.debug(f"limites: {limites}")
    limites['luminosidade'] = limites.pop('lux')
    #logger.debug(f"limites atualizado: {limites}")
    resultado_tendencia = analisar_tendencias(df)
    
    # Tratamento defensivo no dicionário de tendências
    resultado_tendencia = {
        "status": resultado_tendencia.get("status", "Sem dados"),
        "score": resultado_tendencia.get("score", 0.0),
        "resumo": resultado_tendencia.get(
            "resumo",
            (resultado_tendencia.get("tendencias") or [{}])[0].get(
                "mensagem", "Sem dados suficientes para prever o comportamento."
            ),
        ),
        "total_previsoes": resultado_tendencia.get(
            "total_tendencias", len(resultado_tendencia.get("tendencias", []))
        ),
        "previsoes": resultado_tendencia.get("tendencias", []),
    }
    
    resultado_anomalias = detectar_anomalias(df) if not df.empty else None

    return {
        "df": df,
        "proc": proc,
        "limites": limites,
        "resultado_tendencia": resultado_tendencia,
        "resultado_anomalias": resultado_anomalias,
    }


# --- FUNÇÕES AUXILIARES DE DATAFRAME ---
def _montar_df_generico(dados_dict: dict | None, chave: str, colunas: list[str]) -> pd.DataFrame:
    """Função genérica auxiliar para evitar duplicação de lógica entre previsões e anomalias."""
    logger.debug("_montar_df_generico(dados_dict: dict | None, chave: str, colunas: list[str]) -> pd.DataFrame")
    itens = (dados_dict or {}).get(chave) or []
    if not itens:
        return pd.DataFrame(columns=colunas)

    return pd.DataFrame(itens).reindex(columns=colunas)


def montar_df_previsoes(resultado_previsao: dict | None) -> pd.DataFrame:
    logger.debug("montar_df_previsoes(resultado_previsao: dict | None) -> pd.DataFrame")
    return _montar_df_generico(resultado_previsao, "previsoes", COLUNAS_PREVISAO)


def montar_df_anomalias(resultado_anomalias: dict | None) -> pd.DataFrame:
    logger.debug("montar_df_anomalias(resultado_anomalias: dict | None) -> pd.DataFrame")
    return _montar_df_generico(resultado_anomalias, "anomalias", COLUNAS_ANOMALIA)


def _serie_temporal(df: pd.DataFrame, metrica: str) -> pd.DataFrame:
    logger.debug("_serie_temporal(df: pd.DataFrame, metrica: str) -> pd.DataFrame")
    if metrica not in df.columns:
        return pd.DataFrame(columns=["dth_recebido", "valor"])

    serie = df[["dth_recebido", metrica]].copy()
    serie["valor"] = pd.to_numeric(serie[metrica], errors="coerce")
    return serie[["dth_recebido", "valor"]].dropna().sort_values("dth_recebido")


def _bandas_zona(
    y_min_plot: float,
    y_max_plot: float,
    limite_min: float | None,
    limite_max: float | None
) -> list[dict[str, Any]]:
    logger.debug("_bandas_zona(y_min_plot: float, y_max_plot: float, limite_min: float | None, limite_max: float | None) -> list[dict[str, Any]]")
    bandas = []

    if limite_min is not None and limite_max is not None:
        # Garante ordenação lógica caso limites estejam invertidos na origem
        if limite_min > limite_max:
            limite_min, limite_max = limite_max, limite_min

        amplitude = max(limite_max - limite_min, 1e-6)
        faixa_atencao = amplitude * 0.15
        ideal_core_min = min(limite_max, limite_min + faixa_atencao)
        ideal_core_max = max(limite_min, limite_max - faixa_atencao)

        bandas.extend(
            [
                {"y0": y_min_plot, "y1": limite_min, "cor": COR_ZONA_CRITICO, "zona": "Crítico (abaixo do limite)"},
                {"y0": limite_min, "y1": ideal_core_min, "cor": COR_ZONA_ATENCAO, "zona": "Atenção (próximo ao limite)"},
                {"y0": ideal_core_min, "y1": ideal_core_max, "cor": COR_ZONA_SAUDAVEL, "zona": "Saudável (faixa ideal)"},
                {"y0": ideal_core_max, "y1": limite_max, "cor": COR_ZONA_ATENCAO, "zona": "Atenção (próximo ao limite)"},
                {"y0": limite_max, "y1": y_max_plot, "cor": COR_ZONA_CRITICO, "zona": "Crítico (acima do limite)"},
            ]
        )

    elif limite_min is not None:
        bandas.extend(
            [
                {"y0": y_min_plot, "y1": limite_min, "cor": COR_ZONA_CRITICO, "zona": "Crítico (abaixo do limite)"},
                {"y0": limite_min, "y1": y_max_plot, "cor": COR_ZONA_SAUDAVEL, "zona": "Saudável (acima do mínimo)"},
            ]
        )

    elif limite_max is not None:
        bandas.extend(
            [
                {"y0": y_min_plot, "y1": limite_max, "cor": COR_ZONA_SAUDAVEL, "zona": "Saudável (abaixo do máximo)"},
                {"y0": limite_max, "y1": y_max_plot, "cor": COR_ZONA_CRITICO, "zona": "Crítico (acima do limite)"},
            ]
        )

    return [b for b in bandas if b["y1"] > b["y0"]]


# --- COMPONENTES VISUAIS ---
def render_legenda_zonas() -> None:
    logger.debug("render_legenda_zonas() -> None:")
    st.markdown(
        """
        <div style="display:flex;gap:14px;flex-wrap:wrap;margin:4px 0 12px 0;">
            <span style="display:flex;align-items:center;gap:6px;">
                <span style="display:inline-block;width:12px;height:12px;background:#d1e7dd;border-radius:2px;border:1px solid #b8d7c6;"></span>
                Saudável
            </span>
            <span style="display:flex;align-items:center;gap:6px;">
                <span style="display:inline-block;width:12px;height:12px;background:#fff3cd;border-radius:2px;border:1px solid #e7d9a6;"></span>
                Atenção
            </span>
            <span style="display:flex;align-items:center;gap:6px;">
                <span style="display:inline-block;width:12px;height:12px;background:#f8d7da;border-radius:2px;border:1px solid #dfb6bb;"></span>
                Crítico
            </span>
            <span style="display:flex;align-items:center;gap:6px;">
                <span style="display:inline-block;width:14px;height:0;border-top:2px dashed #b02a37;"></span>
                Limites
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_grafico_linha(df: pd.DataFrame, metrica: str, titulo: str, unidade: str = "") -> None:
    logger.debug("render_grafico_linha(df: pd.DataFrame, metrica: str, titulo: str, unidade: str = "") -> None")
    serie = _serie_temporal(df, metrica)
    st.subheader(titulo)

    if serie.empty:
        st.info(f"{titulo}: sem leituras válidas para exibir.")
        return

    base = alt.Chart(serie).encode(
        x=alt.X("dth_recebido:T", title="Horário"),
        y=alt.Y("valor:Q", title=unidade or "valor"),
    )
    grafico = base.mark_line(color="#1f77b4", strokeWidth=2).encode(
        tooltip=[
            alt.Tooltip("dth_recebido:T", title="Horário"),
            alt.Tooltip("valor:Q", title=titulo, format=".3f"),
        ]
    ).interactive()

    st.altair_chart(grafico.properties(height=220), width='stretch')


def render_grafico_zona(
    df: pd.DataFrame,
    metrica: str,
    titulo: str,
    limites: dict | None,
    unidade: str = "",
    mostrar_limites: bool = False,
) -> None:
    logger.debug("render_grafico_zona(df: pd.DataFrame,metrica: str,titulo: str,limites: dict | None,unidade: str = '',mostrar_limites: bool = False,) -> None")
    serie = _serie_temporal(df, metrica)
    if serie.empty:
        st.info(f"{titulo}: sem leituras válidas para exibir.")
        return

    limite_min, limite_max = (limites or {}).get(metrica, (None, None))

    min_serie = float(serie["valor"].min())
    max_serie = float(serie["valor"].max())

    candidatos_min = [min_serie]
    candidatos_max = [max_serie]
    if limite_min is not None:
        candidatos_min.append(float(limite_min))
    if limite_max is not None:
        candidatos_max.append(float(limite_max))

    y_min = min(candidatos_min)
    y_max = max(candidatos_max)
    margem = max((y_max - y_min) * 0.12, 0.05)
    y_min_plot = y_min - margem
    y_max_plot = y_max + margem

    x_inicio = serie["dth_recebido"].min()
    x_fim = serie["dth_recebido"].max()

    bandas = _bandas_zona(y_min_plot, y_max_plot, limite_min, limite_max)
    bandas_df = pd.DataFrame(
        [
            {
                "x_inicio": x_inicio,
                "x_fim": x_fim,
                "y0": b["y0"],
                "y1": b["y1"],
                "cor": b["cor"],
                "zona": b["zona"],
            }
            for b in bandas
        ]
    )

    base = alt.Chart(serie).encode(
        x=alt.X("dth_recebido:T", title="Horário"),
        y=alt.Y("valor:Q", title=unidade or "valor", scale=alt.Scale(domain=[y_min_plot, y_max_plot])),
    )

    camadas = []

    if not bandas_df.empty:
        camadas.append(
            alt.Chart(bandas_df)
            .mark_rect(opacity=0.35)
            .encode(
                x="x_inicio:T",
                x2="x_fim:T",
                y="y0:Q",
                y2="y1:Q",
                color=alt.Color("cor:N", scale=None, legend=None),
                tooltip=["zona:N", alt.Tooltip("y0:Q", format=".2f"), alt.Tooltip("y1:Q", format=".2f")],
            )
        )

    camadas.append(
        base.mark_line(color="#1f77b4", strokeWidth=2).encode(
            tooltip=[
                alt.Tooltip("dth_recebido:T", title="Horário"),
                alt.Tooltip("valor:Q", title=titulo, format=".3f"),
            ]
        )
    )

    ultimo_ponto = serie.tail(1)
    camadas.append(alt.Chart(ultimo_ponto).mark_circle(size=80, color="#1f77b4"))

    if limite_min is not None:
        limite_min_df = pd.DataFrame([{"valor": float(limite_min)}])
        camadas.append(
            alt.Chart(limite_min_df).mark_rule(color="#b02a37", strokeDash=[6, 4]).encode(y="valor:Q")
        )

    if limite_max is not None:
        limite_max_df = pd.DataFrame([{"valor": float(limite_max)}])
        camadas.append(
            alt.Chart(limite_max_df).mark_rule(color="#b02a37", strokeDash=[6, 4]).encode(y="valor:Q")
        )

    st.subheader(titulo)
    st.altair_chart(alt.layer(*camadas).properties(height=220).interactive(), width='stretch')

    if mostrar_limites:
        if limite_min is None and limite_max is None:
            st.caption("Sem limites configurados para esta variável. Exibindo apenas série temporal.")
        elif limite_min is not None and limite_max is not None:
            st.caption(f"Faixa ideal: {limite_min:.2f} a {limite_max:.2f} {unidade}".strip())
        elif limite_min is not None:
            st.caption(f"Limite mínimo recomendado: {limite_min:.2f} {unidade}".strip())
        else:
            st.caption(f"Limite máximo recomendado: {limite_max:.2f} {unidade}".strip())