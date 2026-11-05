import requests
import yfinance as yf
from ta.volatility import AverageTrueRange
from ta.momentum import RSIIndicator
import pandas as pd

# Configuración de tu canal de ntfy.sh (¡Asegúrate de que coincida con el que elegiste en tu app de Android!)
NTFY_TOPIC = "mi_trading_bot_alerta_998822"

def enviar_alerta(titulo, mensaje, prioridad="default"):
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=mensaje.encode("utf-8"),
            headers={
                "Title": titulo.encode("utf-8"),
                "Priority": prioridad,
                "Tags": "chart_with_upwards_trend,warning"
            }
        )
    except Exception as e:
        print(f"Error al enviar notificación: {e}")

# Lista de activos a monitorear
activos = {
    "BTC": "BTC-USD",
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "NASDAQ": "^IXIC",
    "SP500": "^GSPC"
}

def analizar_mercados():
    print("Ejecutando escaneo de mercado...")
    for nombre, ticker in activos.items():
        try:
            # Descargar datos recientes
            df = yf.download(ticker, period="5d", interval="1h", progress=False)
            if df.empty:
                continue
            
            # Asegurar formato plano si yfinance devuelve multi-index
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            close = df['Close']
            
            # Indicadores técnicos rápidos
            rsi_indicator = RSIIndicator(close=close, window=14)
            rsi = rsi_indicator.rsi().iloc[-1]
            
            atr_indicator = AverageTrueRange(high=df['High'], low=df['Low'], close=close, window=14)
            atr = atr_indicator.average_true_range().iloc[-1]
            
            precio_actual = close.iloc[-1]
            cambio_porcentual = ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100

            print(f"[{nombre}] Precio: {precio_actual:.2f} | RSI: {rsi:.1f} | Cambio: {cambio_porcentual:.2f}%")

            # Reglas de Alerta Inteligente
            if rsi > 75:
                enviar_alerta(
                    f"⚠️ ALERTA RIESGO CAÍDA: {nombre}",
                    f"El activo {nombre} está en SOBRECOMPRA extrema (RSI: {rsi:.1f}). Precio actual: {precio_actual:.2f}. Vigilar rechazo bajista.",
                    prioridad="high"
                )
            elif rsi < 25:
                enviar_alerta(
                    f"🚀 POSIBLE OPORTUNIDAD COMPRA: {nombre}",
                    f"El activo {nombre} está en SOBREVENTA (RSI: {rsi:.1f}). Precio actual: {precio_actual:.2f}. Buscar patrones de giro alcista.",
                    prioridad="high"
                )
            
            if abs(cambio_porcentual) > 1.5:
                enviar_alerta(
                    f"⚡ MOVIMIENTO BRUSCO EN {nombre}",
                    f"Variación del {cambio_porcentual:.2f}% en la última hora. Precio: {precio_actual:.2f} ATR: {atr:.2f}",
                    prioridad="urgent"
                )

        except Exception as e:
            print(f"Error procesando {nombre}: {e}")

if __name__ == "__main__":
    # Ejecuta el análisis una sola vez y finaliza para integrarse con GitHub Actions
    analizar_mercados()
