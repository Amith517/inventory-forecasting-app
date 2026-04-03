import pandas as pd
from pmdarima import auto_arima
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
from modules.preprocessing import get_daily_sales_series
from modules.database import get_connection

def generate_forecast_for_product(product_id, days=14):
    import pandas as pd
    from modules.preprocessing import get_daily_sales_series

    series = get_daily_sales_series(product_id)

    # ✅ FIX: not enough data → fallback
    if series is None or len(series) < 2:
        avg = series.mean() if len(series) > 0 else 0
        return pd.Series([avg] * days)

    try:
        from pmdarima import auto_arima
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        from prophet import Prophet

        model = auto_arima(series, seasonal=True, m=7, suppress_warnings=True)

        sarima = SARIMAX(series,
                         order=model.order,
                         seasonal_order=model.seasonal_order).fit(disp=False)

        sarima_fc = sarima.get_forecast(steps=days).predicted_mean

        df = series.reset_index()
        df.columns = ['ds', 'y']

        # ✅ Prophet needs at least 2 rows
        if len(df) < 2:
            return pd.Series([df["y"].mean()] * days)

        prophet = Prophet()
        prophet.fit(df)

        future = prophet.make_future_dataframe(periods=days)
        fc = prophet.predict(future)['yhat'][-days:]

        final = (sarima_fc.values + fc.values) / 2
        return pd.Series(final)

    except Exception as e:
        # ✅ fallback safe
        avg = series.mean()
        return pd.Series([avg] * days)