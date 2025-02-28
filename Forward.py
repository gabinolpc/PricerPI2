import math

class Forward:
    def __init__(self, spot, maturity, interest_rate, dividend=0):
        self.spot = spot                   # Prix au comptant de l'actif sous-jacent
        self.maturity = maturity           # Temps jusqu'à la maturité (en années)
        self.interest_rate = interest_rate # Taux d'intérêt annuel
        self.dividend = dividend           # Rendement du dividende (annuel)

    def price(self):
        """Calcule le prix du contrat forward."""
        forward_price = self.spot * math.exp((self.interest_rate - self.dividend) * self.maturity)
        return forward_price
    
    def payoff_long(self, underlying_price):
        """Calcule le payoff pour une position longue dans le forward."""
        return underlying_price - self.price() 

    def payoff_short(self, underlying_price):
        """Calcule le payoff pour une position courte dans le forward."""
        return self.price() - underlying_price 


