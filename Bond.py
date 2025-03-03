import math

class Bond:
    def __init__(self, face_value, coupon_rate, ytm, maturity, frequency=1, compounding='Discrète'):
        self.face_value = face_value    # Valeur nominale (VN)
        self.coupon_rate = coupon_rate  # Taux de coupon
        self.ytm = ytm                  # Yield to Maturity (YTM)
        self.maturity = maturity        # Échéance
        self.frequency = frequency      # Fréquence
        self.compounding = compounding  # Composition

    def actualize(self, cash_flow, time):
        """Actualise un flux de trésorerie à un temps donné."""
        if self.compounding == "Continue":
            return cash_flow * math.exp(-self.ytm * time)  # Composition continue
        elif self.compounding == "Discrète":
            return cash_flow / ((1 + self.ytm / self.frequency) ** (self.frequency * time))  # Composition discrète
        else:
            raise ValueError(f"Méthode de composition '{self.compounding}' non supportée. Utiliser 'continuous' ou 'discrete'.")

    def price(self):
        """Calcule le prix de l'obligation en actualisant les flux de coupons et la valeur nominale."""
        price = 0
        for t in range(1, int(self.maturity * self.frequency + 1)):
            time = t / self.frequency  # Temps actualisé en année avant chaque versement de coupon
            price += self.actualize(self.coupon_rate * self.face_value / self.frequency, time)  # Coupons actualisés
        #price += self.actualize(self.face_value, self.maturity)  # Valeur nominale actualisée
        price += self.face_value / ((1 + self.ytm) ** (self.maturity))
        return price 

    def duration(self):
        """Calcule la duration de l'obligation."""
        bond_price = self.price()  # Prix total de l'obligation (dénominateur)
        num_dur = 0  # Numérateur
        for t in range(1, int(self.maturity * self.frequency + 1)):
            time = t / self.frequency  # Temps actualisé
            num_dur += time * self.actualize(self.coupon_rate * self.face_value / self.frequency, time)  
        #num_dur += self.maturity * self.actualize(self.face_value, self.maturity)  
        num_dur += self.maturity * self.face_value / ((1 + self.ytm) ** (self.maturity))
        return num_dur / bond_price  # Duration de Macaulay

    def modified_duration(self):
        """Calcule la duration modifiée de l'obligation."""
        macaulay_duration = self.duration()  # Duration de Macaulay
        return macaulay_duration / (1 + self.ytm / self.frequency)  # Ajustée pour les variations du taux d'intérêt

    def convexity(self):
        """Calcule la convexité de l'obligation."""
        bond_price = self.price()  # Prix de l'obligation
        num_convexity = 0  
        for t in range(1, int(self.maturity * self.frequency + 1)):
            time = t / self.frequency  
            num_convexity += (time ** 2) * self.actualize(self.coupon_rate * self.face_value / self.frequency, time)  
        #num_convexity += (self.maturity ** 2) * self.actualize(self.face_value, self.maturity)  
        num_convexity += (self.maturity ** 2) * self.face_value / ((1 + self.ytm) ** (self.maturity))
        return num_convexity / bond_price
