import math
from scipy.stats import norm
from Greeks_parameters import Underlying, TimeToMaturity, FreeRate

class Call:
    def __init__(self, S, K, T, r, sigma, transaction_price=None):
        """Constructeur principal avec des valeurs brutes"""
        self.S = S                                  # Prix de l'actif sous-jacent (Spot)
        self.K = K                                  # Prix d'exercice (Strike)
        self.T = T                                  # Temps jusqu'à expiration
        self.r = r                                  # Taux d'intérêt sans risque
        self.sigma = sigma                          # Volatilité
        self.price = None                           # Initialisé à None
        self.transaction_price = transaction_price  # Initialisé à None ou à un prix donné
        self.pnl = None                             # P&L initialisé à None

        self.compute_price()  # Calcul du prix de l'option au moment de l'initialisation

    @classmethod
    def from_instances(cls, underlying, strike, time_to_maturity, free_rate, transaction_price=None):
        """Deuxième constructeur utilisant des instances d'autres classes"""
        return cls(
            S=underlying.spot_price,
            K=strike,
            T=time_to_maturity.value,
            r=free_rate.value,
            sigma=underlying.implied_vol,
            transaction_price=transaction_price
        )

    def compute_price(self):
        """Calcul du prix de l'option Call selon le modèle de Black-Scholes"""
        d1 = (math.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        d2 = d1 - self.sigma * math.sqrt(self.T)
        self.price = self.S * norm.cdf(d1) - self.K * math.exp(-self.r * self.T) * norm.cdf(d2)

    def update_pnl(self, pos="Call"):
        """Met à jour le P&L en fonction du prix actuel de l'option et de la position"""
        if self.transaction_price is not None and self.price is not None:
            if pos == "Long":
                self.pnl = self.price - self.transaction_price  # Position Long
            elif pos == "Short":
                self.pnl = self.transaction_price - self.price  # Position Short
        else:
            self.pnl = None

    def update_option(self, underlying, strike, time_to_maturity, free_rate, purchase_price=None):
        """Met à jour les attributs de l'option en fonction des instances fournies"""
        self.S = underlying.spot_price
        self.K = strike
        self.T = time_to_maturity.value
        self.r = free_rate.value
        self.sigma = underlying.implied_vol
        self.purchase_price = purchase_price  
        
        self.compute_price()
        self.update_pnl()

    def payoff_long(self, S_T):
        return max(S_T - self.K, 0)
    def payoff_short(self, S_T):
        return -max(S_T - self.K, 0)

    def delta(self, pos="Long"):
        d1 = (math.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        if pos == "Long":
            return norm.cdf(d1)
        elif pos == "Short":
            return -norm.cdf(d1)
    def gamma(self, pos="Long"):
        d1 = (math.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        return norm.pdf(d1) / (self.S * self.sigma * math.sqrt(self.T))
    def vega(self, pos="Long"):
        d1 = (math.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        vega_val = self.S * norm.pdf(d1) * math.sqrt(self.T)
        if pos == "Long":
            return vega_val
        elif pos == "Short":
            return -vega_val
    def theta(self, pos="Long"):
        d1 = (math.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        d2 = d1 - self.sigma * math.sqrt(self.T)
        theta_val = (-self.S * norm.pdf(d1) * self.sigma) / (2 * math.sqrt(self.T)) - self.r * self.K * math.exp(-self.r * self.T) * norm.cdf(d2)
        if pos == "Long":
            return theta_val
        elif pos == "Short":
            return -theta_val
    def rho(self, pos="Long"):
        d1 = (math.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        d2 = d1 - self.sigma * math.sqrt(self.T)
        rho_val = self.K * self.T * math.exp(-self.r * self.T) * norm.cdf(d2)
        if pos == "Long":
            return rho_val
        elif pos == "Short":
            return -rho_val

class Put:
    def __init__(self, S, K, T, r, sigma):
        self.S = S          # Prix de l'actif sous-jacent
        self.K = K          # Prix d'exercice
        self.T = T          # Temps jusqu'à expiration
        self.r = r          # Taux d'intérêt sans risque
        self.sigma = sigma  # Volatilité

    def price(self):
        """Calcul du prix de l'option Put selon le modèle de Black-Scholes"""
        d1 = (math.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        d2 = d1 - self.sigma * math.sqrt(self.T)
        put_price = self.K * math.exp(-self.r * self.T) * norm.cdf(-d2) - self.S * norm.cdf(-d1)
        return put_price

    def payoff_long(self, S_T):
        return max(self.K - S_T, 0)
    def payoff_short(self, S_T):
        return -max(self.K - S_T, 0)

    def delta(self):
        d1 = (math.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        return norm.cdf(d1) - 1
    def gamma(self):
        d1 = (math.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        return norm.pdf(d1) / (self.S * self.sigma * math.sqrt(self.T))
    def vega(self):
        d1 = (math.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        return self.S * math.sqrt(self.T) * norm.pdf(d1)
    def theta(self):
        d1 = (math.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        d2 = d1 - self.sigma * math.sqrt(self.T)
        theta_put = (-self.S * norm.pdf(d1) * self.sigma / (2 * math.sqrt(self.T)) 
                     - self.r * self.K * math.exp(-self.r * self.T) * norm.cdf(-d2))
        return theta_put
    def rho(self):
        d2 = (math.log(self.S / self.K) + (self.r - 0.5 * self.sigma ** 2) * self.T) / (self.sigma * math.sqrt(self.T))
        return -self.K * self.T * math.exp(-self.r * self.T) * norm.cdf(-d2)

class Straddle:
    def __init__(self, S, K, T, r, sigma):
        """Call + Put avec les mêmes paramètres"""
        self.call = Call(S, K, T, r, sigma)  # Crée une option Call
        self.put = Put(S, K, T, r, sigma)   # Crée une option Put

    def price(self):
        return self.call.price + self.put.price()

    def payoff_long(self, S_T):
        return self.call.payoff_long(S_T) + self.put.payoff_long(S_T)
    def payoff_short(self, S_T):
        return self.call.payoff_short(S_T) + self.put.payoff_short(S_T)

    def delta(self):
        return self.call.delta() + self.put.delta()
    def gamma(self):
        return self.call.gamma() + self.put.gamma()
    def vega(self):
        return self.call.vega() + self.put.vega()
    def theta(self):
        return self.call.theta() + self.put.theta()
    def rho(self):
        return self.call.rho() + self.put.rho()

class Strangle:
    def __init__(self, S, K_call, K_put, T, r, sigma):
        """Call + Put avec les mêmes paramètres sauf K"""
        self.call = Call(S, K_call, T, r, sigma)  # Crée une option Call avec un prix d'exercice différent
        self.put = Put(S, K_put, T, r, sigma)    # Crée une option Put avec un prix d'exercice différent

    def price(self):
        return self.call.price + self.put.price()

    def payoff_long(self, S_T):
        return self.call.payoff_long(S_T) + self.put.payoff_long(S_T)
    def payoff_short(self, S_T):
        return self.call.payoff_short(S_T) + self.put.payoff_short(S_T)

    def delta(self):
        return self.call.delta() + self.put.delta()
    def gamma(self):
        return self.call.gamma() + self.put.gamma()
    def vega(self):
        return self.call.vega() + self.put.vega()
    def theta(self):
        return self.call.theta() + self.put.theta()
    def rho(self):
        return self.call.rho() + self.put.rho()

class CallSpread:
    def __init__(self, S, K_long, K_short, T, r, sigma):
        """Call - Call (Acheter un call avec un strike inférieure et vendre un call avec un strike supérieur)"""
        self.call_long = Call(S, K_long, T, r, sigma)   # Crée une option Call (long)
        self.call_short = Call(S, K_short, T, r, sigma)  # Crée une option Call (short)

    def price(self):
        """Prix du Short Call Spread"""
        return self.call_long.price - self.call_short.price

    def payoff_long(self, S_T):
        """Calcule le payoff du Call Spread pour la position Long"""
        return self.call_long.payoff_long(S_T) - self.call_short.payoff_long(S_T)
    def payoff_short(self, S_T):
        """Calcule le payoff du Call Spread pour la position Short"""
        return self.call_long.payoff_short(S_T) - self.call_short.payoff_short(S_T)

    def delta(self):
        return self.call_long.delta() - self.call_short.delta()
    def gamma(self):
        return self.call_long.gamma() - self.call_short.gamma()
    def vega(self):
        return self.call_long.vega() - self.call_short.vega()
    def theta(self):
        return self.call_long.theta() - self.call_short.theta()
    def rho(self):
        return self.call_long.rho() - self.call_short.rho()


