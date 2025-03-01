import yfinance as yf
import numpy as np
import datetime

class Underlying:
    def __init__(self, ticker):
        self.ticker = ticker
        self.name = None            # Nom de l'underlying
        self.spot_price = None      # Dernier prix de clôture
        self.data = None            # Stocke les données historiques du marché
        self.historical_vol = None  # Volatilité historique
        self.implied_vol = None     # Volatilité implicite

    def update_data(self, period="1y"):  # Période par défaut = 1 an
        """Récupère les dernières données de marché de l'actif sous-jacent en fonction de la période."""
        try:
            # Récupérer les données avec yfinance
            asset = yf.Ticker(self.ticker)
            hist = asset.history(period=period)  # Utiliser la période spécifiée
            asset_info = asset.info
            
            # Stocker les informations de l'actif
            self.name = asset_info.get("longName", self.ticker)  # Nom de l'underlying
            self.spot_price = hist["Close"].iloc[-1]  # Dernier prix de clôture
            self.data = hist
            self.compute_historical_vol()  # Calculer la volatilité historique
            self.compute_implied_vol()     # Calculer la volatilité implicite
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
    def __init__(self, maturity_date, method=1):
        self.method = method  # Méthode de calcul (par défaut: Actual/Actual)
        if maturity_date is not None:
            self.maturity_date = maturity_date  # Date d'échéance fournie
            self.value = self.calculate_initial_value_from_maturity_date(maturity_date)  # Calculer la valeur de TTM à partir de la date d'échéance
        else:
            raise ValueError("Il faut fournir une date d'échéance.")

    def calculate_initial_value_from_maturity_date(self, maturity_date):
        """Calcule la valeur de TimeToMaturity en fonction de la date d'échéance."""
        today = datetime.datetime.today().date()  # On prend uniquement la partie date
        days_left = (maturity_date - today).days
        if days_left < 0:
            raise ValueError("La date d'échéance ne peut pas être dans le passé.")
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
            raise ValueError(f"Convention de calcul {self.method} non supportée. Méthodes disponibles: 0, 1, 2, 3, 4.")

class FreeRate:
    def __init__(self, value=None):
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

