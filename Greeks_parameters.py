import yfinance as yf
import numpy as np
import datetime

class Underlying:
    def __init__(self, ticker):
        self.ticker = ticker
        self.spot_price = None      # Dernier prix de clôture
        self.data = None            # Stocke les données historiques du marché
        self.historical_vol = None  # Volatilité historique
        self.implied_vol = None     # Volatilité implicite

    def update_data(self):
            """Récupère les dernières données de marché de l'actif sous-jacent."""
            try:
                asset = yf.Ticker(self.ticker)
                hist = asset.history(period="5y")  # Récupère les données historiques sur 5 ans
                if hist.empty:
                    raise ValueError(f"Impossible de récupérer les données pour {self.ticker}")
                self.data = hist
                self.spot_price = hist["Close"].iloc[-1]  # Dernier prix de clôture
                self.compute_historical_vol()
                self.compute_implied_vol()
            except Exception as e:
                raise ValueError(f"Erreur lors de la récupération des données de marché pour {self.ticker}: {e}")

    def compute_historical_vol(self):
        """Calcule la volatilité historique en utilisant les rendements log."""
        if self.data is None or self.data.empty:
            raise ValueError("Les données de marché ne sont pas disponibles.")
        # Calcul des rendements log
        log_returns = np.log(self.data["Close"] / self.data["Close"].shift(1)).dropna()  # dropna pour supprimer les NaN
        # Calcul de l'écart type
        mean_return = sum(log_returns) / len(log_returns)
        std = sum((r - mean_return) ** 2 for r in log_returns) / (len(log_returns) - 1)
        self.historical_vol = np.sqrt(std) * np.sqrt(252)  # Volatilité annualisée (252 jours de bourse)

    def compute_implied_vol(self):
        """Calcule la volatilité implicite à partir des options du sous-jacent."""
        try:
            asset = yf.Ticker(self.ticker)
            options_data = asset.option_chain(asset.options[0])  # Utilise la première expiration disponible
            calls = options_data.calls
            puts = options_data.puts
            # Calculer la volatilité implicite en prenant une moyenne des volatilités implicites des options
            iv_calls = calls["impliedVolatility"].mean()
            iv_puts = puts["impliedVolatility"].mean()
            # On prend la moyenne des volatilités implicites des calls et puts
            self.implied_vol = (iv_calls + iv_puts) / 2
        except Exception as e:
            raise ValueError(f"Erreur lors de la récupération des données des options pour {self.ticker}: {e}")

class TimeToMaturity:
    def __init__(self, initial_value=None, maturity_date=None, method=1):
        self.method = method  # Méthode de calcul (par défaut: Actual/Actual)
        
        if initial_value is not None:
            self.initial_value = initial_value  # Temps à la création en années
            self.maturity_date = self.calculate_maturity_date_from_initial_value(initial_value)  # Calculer la date d'échéance à partir de la valeur
            self.value = initial_value  # Valeur actuelle du temps à l'expiration
        elif maturity_date is not None:
            self.maturity_date = maturity_date  # Date d'échéance fournie
            self.initial_value = self.calculate_initial_value_from_maturity_date(maturity_date)  # Calculer la valeur de TTM à partir de la date d'échéance
            self.value = self.initial_value
        else:
            raise ValueError("Il faut fournir soit une valeur de TimeToMaturity soit une date d'échéance.")

    def calculate_maturity_date_from_initial_value(self, initial_value):
        """Calcule la date d'échéance en fonction de la valeur de TimeToMaturity (en années)."""
        today = datetime.datetime.today()
        delta_days = int(initial_value * 365)  # Convertir la valeur en jours
        return today + datetime.timedelta(days=delta_days)

    def calculate_initial_value_from_maturity_date(self, maturity_date):
        """Calcule la valeur de TimeToMaturity en fonction de la date d'échéance."""
        today = datetime.datetime.today()
        days_left = (maturity_date - today).days
        if self.method == 0:  # US (Nasd) 30/360
            return days_left / 360
        elif self.method == 1:  # Actual/Actual
            return days_left / 365
        elif self.method == 2:  # Actual/360
            return days_left / 360
        elif self.method == 3:  # Actual/365
            return days_left / 365
        elif self.method == 4:  # European 30/360
            return days_left / 360
        else:
            raise ValueError(f"Conventions de calcul {self.method} non supportées")

    def update_time(self, method=None):
        """Met à jour le temps restant en fonction de la méthode de comptabilisation du temps."""
        if method is not None:
            self.method = method

        today = datetime.datetime.today()
        days_left = (self.maturity_date - today).days
        if self.method == 0:  # US (Nasd) 30/360
            self.value = days_left / 360
        elif self.method == 1:  # Actual/Actual
            self.value = days_left / 365
        elif self.method == 2:  # Actual/360
            self.value = days_left / 360
        elif self.method == 3:  # Actual/365
            self.value = days_left / 365
        elif self.method == 4:  # European 30/360
            self.value = days_left / 360
        else:
            raise ValueError(f"Conventions de calcul {self.method} non supportées")

class FreeRate:
    def __init__(self, value):
        self.value = value  # Taux d'intérêt sans risque

    def update_rate(self, ticker="^IRX"):
        """Met à jour le taux sans risque en récupérant les données de Yahoo Finance."""
        try:
            asset = yf.Ticker(ticker)
            hist = asset.history(period="1d")  # Récupère les données du dernier jour
            if hist.empty:
                raise ValueError("Impossible de récupérer les données pour le taux sans risque.")
            self.value = hist["Close"].iloc[-1] / 100  # Divisé par 100 pour convertir en décimal
        except Exception as e:
            raise ValueError(f"Erreur lors de la récupération du taux sans risque pour {ticker}: {e}")

