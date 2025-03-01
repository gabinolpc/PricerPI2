import streamlit as st
import matplotlib.pyplot as plt
import yfinance as yf
import datetime
import plotly.graph_objects as go
#import math
#import time

from Bond import Bond
from Forward import Forward
from Option import Call, Put, Straddle, Strangle, CallSpread
from Greeks_parameters import Underlying, TimeToMaturity, FreeRate

# Titre de l'application
st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center; color: #2C3E50;'>PricerPI2</h1>", unsafe_allow_html=True)

# Menu avec sections déroulantes
section = st.sidebar.radio("📋 Menu", ["Accueil", "Bond", "Forward & Future", "Options", "Suivi de Position"])

# Réinitialiser les données de session lorsque la section change
if 'current_section' not in st.session_state:
    st.session_state['current_section'] = section  # Initialisation au premier démarrage
if st.session_state['current_section'] != section:
    st.session_state.clear()  # Clear toutes les données de session
    st.session_state['current_section'] = section  # Met à jour la section sélectionnée

# Section Accueil
if section == "Accueil":
    st.write("### Bienvenue sur PricerPI2 !")
    st.write("""**PricerPI2** vous permet d'explorer différents modèles de **pricing** pour des instruments financiers.
    Vous pouvez naviguer entre les sections pour découvrir les fonctionnalités disponibles.""")

# Section Bond
elif section == "Bond":

    # Créer une mise en page avec deux colonnes
    col1, col2 = st.columns(2)

    # Colonne 1 (Pricing à gauche)
    with col1:
        # Inputs
        st.write("### Bond")
        
        # Récupérer les valeurs actuelles des inputs
        current_face_value = st.number_input("Valeur nominale (VN) :", min_value=100.0, value=1000.0, step=100.0)
        current_coupon_rate = st.number_input("Taux de coupon (%) :", min_value=0.0, value=5.0, step=0.5) / 100  # Divisé par 100
        current_ytm = st.number_input("Yield to Maturity (YTM) (%) :", min_value=0.0, value=3.0, step=0.5) / 100  # Divisé par 100
        current_maturity = st.number_input("Maturité (en années) :", min_value=1.0, value=5.0)
        current_frequency = st.selectbox("Fréquence des paiements de coupons :", [1, 2, 4, 12], index=0)
        current_compounding = st.selectbox("Méthode de composition :", ["Continue", "Discrète"], index=1)

        # Si les inputs ont changé par rapport aux précédentes valeurs, réinitialiser l'état de la session
        if (getattr(st.session_state, 'previous_face_value', None) != current_face_value or
            getattr(st.session_state, 'previous_coupon_rate', None) != current_coupon_rate or
            getattr(st.session_state, 'previous_ytm', None) != current_ytm or
            getattr(st.session_state, 'previous_maturity', None) != current_maturity or
            getattr(st.session_state, 'previous_frequency', None) != current_frequency or
            getattr(st.session_state, 'previous_compounding', None) != current_compounding):
            
            # Effacer les valeurs stockées dans la session
            if 'bond_price' in st.session_state:
                del st.session_state.bond_price
            if 'previous_face_value' in st.session_state:
                del st.session_state.previous_face_value
            if 'previous_coupon_rate' in st.session_state:
                del st.session_state.previous_coupon_rate
            if 'previous_ytm' in st.session_state:
                del st.session_state.previous_ytm
            if 'previous_maturity' in st.session_state:
                del st.session_state.previous_maturity
            if 'previous_frequency' in st.session_state:
                del st.session_state.previous_frequency
            if 'previous_compounding' in st.session_state:
                del st.session_state.previous_compounding

        # Mise à jour des anciennes valeurs dans la session pour les comparer lors des futurs changements
        st.session_state.previous_face_value = current_face_value
        st.session_state.previous_coupon_rate = current_coupon_rate
        st.session_state.previous_ytm = current_ytm
        st.session_state.previous_maturity = current_maturity
        st.session_state.previous_frequency = current_frequency
        st.session_state.previous_compounding = current_compounding

        # Création de l'objet Bond avec les paramètres
        bond = Bond(current_face_value, current_coupon_rate, current_ytm, current_maturity, current_frequency, current_compounding)

        # Calcul des caractéristiques de l'obligation
        if st.button("Calculer les caractéristiques du bond"):
            price = bond.price()
            duration = bond.duration()
            modified_duration = bond.modified_duration()
            convexity = bond.convexity()

            # Affichage des résultats
            st.subheader("Caractéristiques")
            st.write(f"💶 **Prix de l'Obligation** : {price:.2f} €")
            st.write(f"📅 **Duration de Macaulay** : {duration:.2f} années")
            st.write(f"📅 **Duration Modifiée** : {modified_duration:.2f} années")
            st.write(f"📈 **Convexité** : {convexity:.2f}")

            # Stocker le prix de l'obligation pour l'affichage dans la colonne 2
            st.session_state.bond_price = price

        # Bouton de réinitialisation
        if st.button("Réinitialiser"):
            st.session_state.clear()  # Réinitialiser l'état de la session

    # Colonne 2 (Graphique à droite)
    with col2:
        # Espacement pour aligner le graphique avec "Valeur nominale"
        st.markdown("<br>" * 4, unsafe_allow_html=True)

        # Vérification que le prix de l'obligation est bien défini
        if 'bond_price' in st.session_state:
            bond_price = st.session_state.bond_price

            # Génération des flux de paiements
            cash_flows = []
            times = []

            for t in range(1, int(current_maturity * current_frequency) + 1):
                time = t / current_frequency  # Paiement exactement au bon moment
                coupon_payment = current_coupon_rate * current_face_value / current_frequency
                cash_flows.append(coupon_payment)
                times.append(time)

            # Dernier flux = Valeur nominale + dernier coupon
            cash_flows.append(current_face_value + current_coupon_rate * current_face_value / current_frequency)
            times.append(current_maturity)

            # Création du graphique
            fig, ax = plt.subplots(figsize=(8, 5))
            bars = ax.bar(times, cash_flows, width=0.05, align='center', color='green', label="Flux de paiements")

            # Ajout de la valeur seulement pour le premier et dernier flux
            ax.text(times[0], cash_flows[0] + 5, f"{cash_flows[0]:.2f}€", ha='center', fontsize=10)
            ax.text(times[-1], cash_flows[-1] + 5, f"{cash_flows[-1]:.2f}€", ha='center', fontsize=10)

            ax.set_title("Flux de paiements de l'obligation")
            ax.set_xlabel("Temps (années)")
            ax.set_ylabel("Montant des paiements (€)")
            ax.grid(True)
            ax.legend(loc="best")

            # Affichage du graphique
            st.pyplot(fig)

        else:
            # Centrer et positionner la phrase plus bas
            st.markdown("""
            <div style="display: flex; justify-content: center; align-items: flex-end; height: 225px;">
                <p style="text-align: center;">Cliquez sur 'Calculer les caractéristiques du bond' pour afficher le graphique.</p>
            </div>
            """, unsafe_allow_html=True)

# Section Contrats Forward & Futures
elif section == "Forward & Future":

    # Créer une mise en page avec deux colonnes
    col1, col2 = st.columns(2)

    # Colonne 1 (Inputs à gauche)
    with col1:
        # Inputs
        st.write("### Forward & Future")
        
        # Récupérer les valeurs actuelles des inputs
        current_spot_price = st.number_input("Prix au comptant (Spot) :", min_value=0.0, value=100.0, step=100.0)
        current_maturity = st.number_input("Maturité (en années) :", min_value=0.0, value=3.0)
        current_interest_rate = st.number_input("Taux d'intérêt annuel (%) :", min_value=0.0, value=5.0, step=0.5) / 100  # Divisé par 100
        current_dividend = st.number_input("Rendement du dividende (%) :", min_value=0.0, value=0.0, step=0.5) / 100  # Divisé par 100

        # Si les inputs ont changé par rapport aux précédentes valeurs, réinitialiser l'état de la session
        if (getattr(st.session_state, 'previous_spot_price', None) != current_spot_price or
            getattr(st.session_state, 'previous_maturity', None) != current_maturity or
            getattr(st.session_state, 'previous_interest_rate', None) != current_interest_rate or
            getattr(st.session_state, 'previous_dividend', None) != current_dividend):
            
            # Effacer les valeurs stockées dans la session
            if 'forward_price' in st.session_state:
                del st.session_state.forward_price
            if 'previous_spot_price' in st.session_state:
                del st.session_state.previous_spot_price
            if 'previous_maturity' in st.session_state:
                del st.session_state.previous_maturity
            if 'previous_interest_rate' in st.session_state:
                del st.session_state.previous_interest_rate
            if 'previous_dividend' in st.session_state:
                del st.session_state.previous_dividend

        # Mise à jour des anciennes valeurs dans la session pour les comparer lors des futurs changements
        st.session_state.previous_spot_price = current_spot_price
        st.session_state.previous_maturity = current_maturity
        st.session_state.previous_interest_rate = current_interest_rate
        st.session_state.previous_dividend = current_dividend

        # Création de l'objet Forward avec les paramètres
        forward_contract = Forward(current_spot_price, current_maturity, current_interest_rate, current_dividend)

        # Calcul du prix du contrat Forward
        if st.button("Calculer le prix du contrat Forward & Future"):
            forward_price = forward_contract.price()  # Calcul du prix Forward
            st.subheader("Caractéristiques")
            st.write(f"💶 **Prix du contrat Forward & Futures** : {forward_price:.2f} €")

            # Stocker la valeur du prix dans une variable de session pour l'utiliser dans la colonne 2
            st.session_state.forward_price = forward_price

        # Bouton de réinitialisation
        if st.button("Réinitialiser"):
            st.session_state.clear()  # Réinitialiser l'état de la session

    # Colonne 2 (Graphique à droite)
    with col2:
        # Espacement pour aligner le graphique
        st.markdown("<br>" * 2, unsafe_allow_html=True)

        # Vérification que le prix Forward est bien défini
        if 'forward_price' in st.session_state:
            forward_price = st.session_state.forward_price

            # Calcul dynamique de la plage de prix Spot en fonction de l'impact des dividendes, taux et maturité
            lower_bound = max(current_spot_price - (20 + 10 * current_maturity), 0)  # Plage minimum ajustée
            upper_bound = current_spot_price + (20 + 10 * current_maturity)  # Plage maximum ajustée

            # Ajouter une marge pour les taux d'intérêt et dividendes
            lower_bound -= (current_interest_rate * current_maturity * current_spot_price)  # Ajuster la plage inférieure
            upper_bound += (current_interest_rate * current_maturity * current_spot_price)  # Ajuster la plage supérieure
            lower_bound = max(0, lower_bound)  # Assurer que la plage ne devienne pas négative

            # Utilisation de int() pour garantir des entiers dans range
            spot_prices = [i for i in range(int(lower_bound), int(upper_bound) + 1)]  # Plage de prix Spot

            # Calcul des payoffs
            long_payoffs = [max(spot - forward_price, 0) for spot in spot_prices]  # Payoff Long
            short_payoffs = [max(forward_price - spot, 0) for spot in spot_prices]  # Payoff Short

            # Création du graphique
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(spot_prices, long_payoffs, label="Long", color='green', linewidth=2)
            ax.plot(spot_prices, short_payoffs, label="Short", color='red', linewidth=2)

            ax.set_title("Payoff du contrat Forward & Future")
            ax.set_xlabel("Prix Spot")
            ax.set_ylabel("Payoff (€)")
            ax.grid(True)
            ax.legend(loc="best")

            # Affichage du graphique
            st.pyplot(fig)
        else:
            # Centrer et positionner la phrase plus bas
            st.markdown("""
            <div style="display: flex; justify-content: center; align-items: flex-end; height: 200px;">
                <p style="text-align: center;">Cliquez sur 'Calculer le prix du contrat Forward & Future' pour afficher le graphique.</p>
            </div>
            """, unsafe_allow_html=True)

# Section Options
elif section == "Options":

    # Sous-sections dans le menu "Options"
    option_type = st.sidebar.radio("📝 Choisir le type d'option", ["Call", "Put", "Straddle", "Strangle", "Call Spread"])

    # Si la sous-section a changé, réinitialiser les données
    if 'current_option_section' not in st.session_state:
        st.session_state['current_option_section'] = option_type  # Initialisation de la sous-section au premier démarrage
    if st.session_state['current_option_section'] != option_type:
        st.session_state.clear()  # Clear toutes les données de session
        st.session_state['current_option_section'] = option_type  # Met à jour la sous-section sélectionnée

    if option_type == "Call":
        # Créer une mise en page avec deux colonnes
        col1, col2 = st.columns(2)

        # Colonne 1 (Inputs à gauche)
        with col1:
            # Inputs
            st.write("### Option Call")

            # Récupérer les valeurs actuelles des inputs
            current_spot_price = st.number_input("Prix de l'actif sous-jacent (Spot) :", min_value=0.0, value=100.0, step=5.0)
            strike_price = st.number_input("Prix d'exercice (Strike) :", min_value=0.0, value=100.0, step=5.0)
            maturity = st.number_input("Maturité (en années) :", min_value=0.0, value=1.0, step=1.0)
            interest_rate = st.number_input("Taux d'intérêt annuel (%) :", min_value=0.0, value=5.0, step=0.5) / 100  # Divisé par 100
            volatility = st.number_input("Volatilité (%) :", min_value=0.0, value=20.0, step=1.0) / 100  # Divisé par 100

            # Si les inputs ont changé par rapport aux précédentes valeurs, réinitialiser l'état de la session
            if (getattr(st.session_state, 'previous_spot_price', None) != current_spot_price or
                getattr(st.session_state, 'previous_strike_price', None) != strike_price or
                getattr(st.session_state, 'previous_maturity', None) != maturity or
                getattr(st.session_state, 'previous_interest_rate', None) != interest_rate or
                getattr(st.session_state, 'previous_volatility', None) != volatility):
                
                # Effacer les valeurs stockées dans la session
                if 'call_price' in st.session_state:
                    del st.session_state.call_price
                if 'previous_spot_price' in st.session_state:
                    del st.session_state.previous_spot_price
                if 'previous_strike_price' in st.session_state:
                    del st.session_state.previous_strike_price
                if 'previous_maturity' in st.session_state:
                    del st.session_state.previous_maturity
                if 'previous_interest_rate' in st.session_state:
                    del st.session_state.previous_interest_rate
                if 'previous_volatility' in st.session_state:
                    del st.session_state.previous_volatility

            # Mise à jour des anciennes valeurs dans la session pour les comparer lors des futurs changements
            st.session_state.previous_spot_price = current_spot_price
            st.session_state.previous_strike_price = strike_price
            st.session_state.previous_maturity = maturity
            st.session_state.previous_interest_rate = interest_rate
            st.session_state.previous_volatility = volatility

            # Création de l'objet Call avec les paramètres
            call_option = Call(current_spot_price, strike_price, maturity, interest_rate, volatility)

            # Calcul du prix de l'option Call
            if st.button("Calculer le prix du Call"):
                call_price = call_option.price  
                st.subheader("Caractéristiques (Long)")
                st.write(f"💶 **Prix du Call** : {call_price:.2f} €")

                # Afficher les valeurs des grecs
                st.write(f"**Δ** : {call_option.delta():.4f}")
                st.write(f"**Γ** : {call_option.gamma():.4f}")
                st.write(f"**ν** : {call_option.vega():.4f}")
                st.write(f"**θ** : {call_option.theta():.4f}")
                st.write(f"**ρ** : {call_option.rho():.4f}")

                # Stocker la valeur du prix dans une variable de session pour l'utiliser dans la colonne 2
                st.session_state.call_price = call_price

            # Bouton de réinitialisation
            if st.button("Réinitialiser"):
                st.session_state.clear()  # Réinitialiser l'état de la session

        # Colonne 2 (Graphiques à droite)
        with col2:
            # Espacement pour aligner le graphique
            st.markdown("<br>" * 2, unsafe_allow_html=True)

            # Vérification que le prix Call est bien défini
            if 'call_price' in st.session_state:
                call_price = st.session_state.call_price

                # Calcul des bornes
                lower_bound = max(current_spot_price - (volatility * current_spot_price * maturity) / 2, 0)  # Plage minimum ajustée
                upper_bound = current_spot_price + (volatility * current_spot_price * maturity) / 2  # Plage maximum ajustée

                # Utilisation de int() pour garantir des entiers dans range
                spot_prices = [i for i in range(int(lower_bound), int(upper_bound) + 1)]  # Plage de prix Spot

                # Calcul des payoffs
                long_payoffs = [call_option.payoff_long(spot) for spot in spot_prices]  
                short_payoffs = [call_option.payoff_short(spot) for spot in spot_prices]  

                # Création du graphique Long
                fig_long, ax_long = plt.subplots(figsize=(8, 5))
                ax_long.plot(spot_prices, long_payoffs, label="Long", color='green', linewidth=2)
                ax_long.set_title("Payoff Long Call")
                ax_long.set_xlabel("Prix Spot")
                ax_long.set_ylabel("Payoff (€)")
                ax_long.grid(True)
                ax_long.legend(loc="best")
                st.pyplot(fig_long)

                # Création du graphique Short
                fig_short, ax_short = plt.subplots(figsize=(8, 5))
                ax_short.plot(spot_prices, short_payoffs, label="Short", color='red', linewidth=2)
                ax_short.set_title("Payoff Short Call")
                ax_short.set_xlabel("Prix Spot")
                ax_short.set_ylabel("Payoff (€)")
                ax_short.grid(True)
                ax_short.legend(loc="best")
                st.pyplot(fig_short)
            else:
                # Centrer et positionner la phrase plus bas
                st.markdown(""" 
                <div style="display: flex; justify-content: center; align-items: center; height: 425px;">
                    <p style="text-align: center;">Cliquez sur 'Calculer le prix du Call' pour afficher les graphiques.</p>
                </div>
                """, unsafe_allow_html=True)
    elif option_type == "Put":
        # Créer une mise en page avec deux colonnes
        col1, col2 = st.columns(2)

        # Colonne 1 (Inputs à gauche)
        with col1:
            # Inputs
            st.write("### Option Put")

            # Récupérer les valeurs actuelles des inputs
            current_spot_price = st.number_input("Prix de l'actif sous-jacent (Spot) :", min_value=0.0, value=100.0, step=5.0)
            strike_price = st.number_input("Prix d'exercice (Strike) :", min_value=0.0, value=100.0, step=5.0)
            maturity = st.number_input("Maturité (en années) :", min_value=0.0, value=1.0, step=1.0)
            interest_rate = st.number_input("Taux d'intérêt annuel (%) :", min_value=0.0, value=5.0, step=0.5) / 100  # Divisé par 100
            volatility = st.number_input("Volatilité (%) :", min_value=0.0, value=20.0, step=1.0) / 100  # Divisé par 100

            # Si les inputs ont changé par rapport aux précédentes valeurs, réinitialiser l'état de la session
            if (getattr(st.session_state, 'previous_spot_price', None) != current_spot_price or
                getattr(st.session_state, 'previous_strike_price', None) != strike_price or
                getattr(st.session_state, 'previous_maturity', None) != maturity or
                getattr(st.session_state, 'previous_interest_rate', None) != interest_rate or
                getattr(st.session_state, 'previous_volatility', None) != volatility):
                
                # Effacer les valeurs stockées dans la session
                if 'put_price' in st.session_state:
                    del st.session_state.put_price
                if 'previous_spot_price' in st.session_state:
                    del st.session_state.previous_spot_price
                if 'previous_strike_price' in st.session_state:
                    del st.session_state.previous_strike_price
                if 'previous_maturity' in st.session_state:
                    del st.session_state.previous_maturity
                if 'previous_interest_rate' in st.session_state:
                    del st.session_state.previous_interest_rate
                if 'previous_volatility' in st.session_state:
                    del st.session_state.previous_volatility

            # Mise à jour des anciennes valeurs dans la session pour les comparer lors des futurs changements
            st.session_state.previous_spot_price = current_spot_price
            st.session_state.previous_strike_price = strike_price
            st.session_state.previous_maturity = maturity
            st.session_state.previous_interest_rate = interest_rate
            st.session_state.previous_volatility = volatility

            # Création de l'objet Put avec les paramètres
            put_option = Put(current_spot_price, strike_price, maturity, interest_rate, volatility)

            # Calcul du prix de l'option Put
            if st.button("Calculer le prix du Put"):
                put_price = put_option.price()  # Calcul du prix Put
                st.subheader("Caractéristiques (Long)")
                st.write(f"💶 **Prix du Put** : {put_price:.2f} €")

                # Afficher les valeurs des grecs
                st.write(f"**Δ** : {put_option.delta():.4f}")
                st.write(f"**Γ** : {put_option.gamma():.4f}")
                st.write(f"**ν** : {put_option.vega():.4f}")
                st.write(f"**θ** : {put_option.theta():.4f}")
                st.write(f"**ρ** : {put_option.rho():.4f}")

                # Stocker la valeur du prix dans une variable de session pour l'utiliser dans la colonne 2
                st.session_state.put_price = put_price

            # Bouton de réinitialisation
            if st.button("Réinitialiser"):
                st.session_state.clear()  # Réinitialiser l'état de la session

        # Colonne 2 (Graphiques à droite)
        with col2:
            # Espacement pour aligner le graphique
            st.markdown("<br>" * 2, unsafe_allow_html=True)

            # Vérification que le prix Put est bien défini
            if 'put_price' in st.session_state:
                put_price = st.session_state.put_price

                # Calcul des bornes
                lower_bound = max(current_spot_price - (volatility * current_spot_price * maturity) / 2, 0)  # Plage minimum ajustée
                upper_bound = current_spot_price + (volatility * current_spot_price * maturity) / 2  # Plage maximum ajustée

                # Utilisation de int() pour garantir des entiers dans range
                spot_prices = [i for i in range(int(lower_bound), int(upper_bound) + 1)]  # Plage de prix Spot

                # Calcul des payoffs
                long_payoffs = [put_option.payoff_long(spot) for spot in spot_prices]  
                short_payoffs = [put_option.payoff_short(spot) for spot in spot_prices]  

                # Création du graphique Long
                fig_long, ax_long = plt.subplots(figsize=(8, 5))
                ax_long.plot(spot_prices, long_payoffs, label="Long", color='green', linewidth=2)
                ax_long.set_title("Payoff Long Put")
                ax_long.set_xlabel("Prix Spot")
                ax_long.set_ylabel("Payoff (€)")
                ax_long.grid(True)
                ax_long.legend(loc="best")
                st.pyplot(fig_long)

                # Création du graphique Short
                fig_short, ax_short = plt.subplots(figsize=(8, 5))
                ax_short.plot(spot_prices, short_payoffs, label="Short", color='red', linewidth=2)
                ax_short.set_title("Payoff Short Put")
                ax_short.set_xlabel("Prix Spot")
                ax_short.set_ylabel("Payoff (€)")
                ax_short.grid(True)
                ax_short.legend(loc="best")
                st.pyplot(fig_short)
            else:
                # Centrer et positionner la phrase plus bas
                st.markdown(""" 
                <div style="display: flex; justify-content: center; align-items: center; height: 425px;">
                    <p style="text-align: center;">Cliquez sur 'Calculer le prix du Put' pour afficher les graphiques.</p>
                </div>
                """, unsafe_allow_html=True)
    elif option_type == "Straddle":
        # Créer une mise en page avec deux colonnes
        col1, col2 = st.columns(2)

        # Colonne 1 (Inputs à gauche)
        with col1:
            # Inputs
            st.write("### Option Straddle")

            # Récupérer les valeurs actuelles des inputs
            current_spot_price = st.number_input("Prix de l'actif sous-jacent (Spot) :", min_value=0.0, value=100.0, step=5.0)
            strike_price = st.number_input("Prix d'exercice (Strike) :", min_value=0.0, value=100.0, step=5.0)
            maturity = st.number_input("Maturité (en années) :", min_value=0.0, value=1.0, step=1.0)
            interest_rate = st.number_input("Taux d'intérêt annuel (%) :", min_value=0.0, value=5.0, step=0.5) / 100
            volatility = st.number_input("Volatilité (%) :", min_value=0.0, value=20.0, step=1.0) / 100

            # Si les inputs ont changé, réinitialiser l'état de la session
            if (getattr(st.session_state, 'previous_spot_price', None) != current_spot_price or
                getattr(st.session_state, 'previous_strike_price', None) != strike_price or
                getattr(st.session_state, 'previous_maturity', None) != maturity or
                getattr(st.session_state, 'previous_interest_rate', None) != interest_rate or
                getattr(st.session_state, 'previous_volatility', None) != volatility):
                
                # Effacer les valeurs stockées dans la session
                if 'straddle_price' in st.session_state:
                    del st.session_state.straddle_price
                st.session_state.previous_spot_price = current_spot_price
                st.session_state.previous_strike_price = strike_price
                st.session_state.previous_maturity = maturity
                st.session_state.previous_interest_rate = interest_rate
                st.session_state.previous_volatility = volatility

            # Création de l'objet Straddle
            straddle_option = Straddle(current_spot_price, strike_price, maturity, interest_rate, volatility)

            # Calcul du prix de l'option Straddle
            if st.button("Calculer le prix du Straddle"):
                straddle_price = straddle_option.price()
                st.subheader("Caractéristiques (Long)")
                st.write(f"💶 **Prix du Straddle** : {straddle_price:.2f} €")

                # Afficher les valeurs des grecs
                st.write(f"**Δ** : {straddle_option.delta():.4f}")
                st.write(f"**Γ** : {straddle_option.gamma():.4f}")
                st.write(f"**ν** : {straddle_option.vega():.4f}")
                st.write(f"**θ** : {straddle_option.theta():.4f}")
                st.write(f"**ρ** : {straddle_option.rho():.4f}")

                # Stocker la valeur du prix dans la session
                st.session_state.straddle_price = straddle_price

            # Bouton de réinitialisation
            if st.button("Réinitialiser"):
                st.session_state.clear()

        # Colonne 2 (Graphiques à droite)
        with col2:
            st.markdown("<br>" * 2, unsafe_allow_html=True)

            if 'straddle_price' in st.session_state:
                straddle_price = st.session_state.straddle_price

                # Calcul des bornes
                lower_bound = max(current_spot_price - (volatility * current_spot_price * maturity) / 2, 0)
                upper_bound = current_spot_price + (volatility * current_spot_price * maturity) / 2

                # Plage de prix Spot
                spot_prices = [i for i in range(int(lower_bound), int(upper_bound) + 1)]

                # Calcul des payoffs
                long_payoffs = [straddle_option.payoff_long(spot) for spot in spot_prices]
                short_payoffs = [straddle_option.payoff_short(spot) for spot in spot_prices]

                # Graphique Long
                fig_long, ax_long = plt.subplots(figsize=(8, 5))
                ax_long.plot(spot_prices, long_payoffs, label="Long", color='green', linewidth=2)
                ax_long.set_title("Payoff Long Straddle")
                ax_long.set_xlabel("Prix Spot")
                ax_long.set_ylabel("Payoff (€)")
                ax_long.grid(True)
                ax_long.legend(loc="best")
                st.pyplot(fig_long)

                # Graphique Short
                fig_short, ax_short = plt.subplots(figsize=(8, 5))
                ax_short.plot(spot_prices, short_payoffs, label="Short", color='red', linewidth=2)
                ax_short.set_title("Payoff Short Straddle")
                ax_short.set_xlabel("Prix Spot")
                ax_short.set_ylabel("Payoff (€)")
                ax_short.grid(True)
                ax_short.legend(loc="best")
                st.pyplot(fig_short)
            else:
                st.markdown(""" 
                <div style="display: flex; justify-content: center; align-items: center; height: 425px;">
                    <p style="text-align: center;">Cliquez sur 'Calculer le prix du Straddle' pour afficher les graphiques.</p>
                </div>
                """, unsafe_allow_html=True)
    elif option_type == "Strangle":
        col1, col2 = st.columns(2)

        with col1:
            st.write("### Option Strangle")
            # Inputs
            current_spot_price = st.number_input("Prix de l'actif sous-jacent (Spot) :", min_value=0.0, value=100.0, step=5.0)
            strike_price_put = st.number_input("Prix d'exercice du Put (Strike Put) :", min_value=0.0, value=95.0, step=5.0)
            strike_price_call = st.number_input("Prix d'exercice du Call (Strike Call) :", min_value=0.0, value=105.0, step=5.0)
            maturity = st.number_input("Maturité (en années) :", min_value=0.0, value=1.0, step=1.0)
            interest_rate = st.number_input("Taux d'intérêt annuel (%) :", min_value=0.0, value=5.0, step=0.5) / 100
            volatility = st.number_input("Volatilité (%) :", min_value=0.0, value=20.0, step=1.0) / 100

            # Gestion de l'état de la session
            if (getattr(st.session_state, 'previous_spot_price', None) != current_spot_price or
                getattr(st.session_state, 'previous_strike_price_put', None) != strike_price_put or
                getattr(st.session_state, 'previous_strike_price_call', None) != strike_price_call or
                getattr(st.session_state, 'previous_maturity', None) != maturity or
                getattr(st.session_state, 'previous_interest_rate', None) != interest_rate or
                getattr(st.session_state, 'previous_volatility', None) != volatility):

                for key in ['strangle_price', 'previous_spot_price', 'previous_strike_price_put', 
                            'previous_strike_price_call', 'previous_maturity', 'previous_interest_rate', 'previous_volatility']:
                    if key in st.session_state:
                        del st.session_state[key]

            st.session_state.previous_spot_price = current_spot_price
            st.session_state.previous_strike_price_put = strike_price_put
            st.session_state.previous_strike_price_call = strike_price_call
            st.session_state.previous_maturity = maturity
            st.session_state.previous_interest_rate = interest_rate
            st.session_state.previous_volatility = volatility

            # Création de l'objet Strangle
            strangle_option = Strangle(current_spot_price, strike_price_put, strike_price_call, maturity, interest_rate, volatility)

            # Calcul du prix de l'option Strangle
            if st.button("Calculer le prix du Strangle"):
                strangle_price = strangle_option.price()
                st.subheader("Caractéristiques (Long)")
                st.write(f"💶 **Prix du Strangle** : {strangle_price:.2f} €")

                # Afficher les valeurs des grecs
                st.write(f"**Δ** : {strangle_option.delta():.4f}")
                st.write(f"**Γ** : {strangle_option.gamma():.4f}")
                st.write(f"**ν** : {strangle_option.vega():.4f}")
                st.write(f"**θ** : {strangle_option.theta():.4f}")
                st.write(f"**ρ** : {strangle_option.rho():.4f}")

                st.session_state.strangle_price = strangle_price

            # Bouton de réinitialisation
            if st.button("Réinitialiser"):
                st.session_state.clear()

        with col2:
            st.markdown("<br>" * 2, unsafe_allow_html=True)

            if 'strangle_price' in st.session_state:
                strangle_price = st.session_state.strangle_price

                lower_bound = max(current_spot_price - (volatility * current_spot_price * maturity) / 2, 0)
                upper_bound = current_spot_price + (volatility * current_spot_price * maturity) / 2

                spot_prices = [i for i in range(int(lower_bound), int(upper_bound) + 1)]

                long_payoffs = [strangle_option.payoff_long(spot) for spot in spot_prices]
                short_payoffs = [strangle_option.payoff_short(spot) for spot in spot_prices]

                # Graphique Long
                fig_long, ax_long = plt.subplots(figsize=(8, 5))
                ax_long.plot(spot_prices, long_payoffs, label="Long", color='green', linewidth=2)
                ax_long.set_title("Payoff Long Strangle")
                ax_long.set_xlabel("Prix Spot")
                ax_long.set_ylabel("Payoff (€)")
                ax_long.grid(True)
                ax_long.legend(loc="best")
                st.pyplot(fig_long)

                # Graphique Short
                fig_short, ax_short = plt.subplots(figsize=(8, 5))
                ax_short.plot(spot_prices, short_payoffs, label="Short", color='red', linewidth=2)
                ax_short.set_title("Payoff Short Strangle")
                ax_short.set_xlabel("Prix Spot")
                ax_short.set_ylabel("Payoff (€)")
                ax_short.grid(True)
                ax_short.legend(loc="best")
                st.pyplot(fig_short)
            else:
                st.markdown(""" 
                <div style="display: flex; justify-content: center; align-items: center; height: 500px;">
                    <p style="text-align: center;">Cliquez sur 'Calculer le prix du Strangle' pour afficher les graphiques.</p>
                </div>
                """, unsafe_allow_html=True)
    elif option_type == "Call Spread":
        col1, col2 = st.columns(2)

        with col1:
            st.write("### Option Call Spread")
            # Inputs
            current_spot_price = st.number_input("Prix de l'actif sous-jacent (Spot) :", min_value=0.0, value=100.0, step=5.0)
            strike_price_long = st.number_input("Prix d'exercice du Long Call (Strike Long) :", min_value=0.0, value=95.0, step=5.0)
            strike_price_short = st.number_input("Prix d'exercice du Short Call (Strike Short) :", min_value=0.0, value=105.0, step=5.0)
            maturity = st.number_input("Maturité (en années) :", min_value=0.0, value=1.0, step=1.0)
            interest_rate = st.number_input("Taux d'intérêt annuel (%) :", min_value=0.0, value=5.0, step=0.5) / 100
            volatility = st.number_input("Volatilité (%) :", min_value=0.0, value=20.0, step=1.0) / 100

            # Gestion de l'état de la session
            if (getattr(st.session_state, 'previous_spot_price', None) != current_spot_price or
                getattr(st.session_state, 'previous_strike_price_long', None) != strike_price_long or
                getattr(st.session_state, 'previous_strike_price_short', None) != strike_price_short or
                getattr(st.session_state, 'previous_maturity', None) != maturity or
                getattr(st.session_state, 'previous_interest_rate', None) != interest_rate or
                getattr(st.session_state, 'previous_volatility', None) != volatility):

                for key in ['call_spread_price', 'previous_spot_price', 'previous_strike_price_long', 
                            'previous_strike_price_short', 'previous_maturity', 'previous_interest_rate', 'previous_volatility']:
                    if key in st.session_state:
                        del st.session_state[key]

            st.session_state.previous_spot_price = current_spot_price
            st.session_state.previous_strike_price_long = strike_price_long
            st.session_state.previous_strike_price_short = strike_price_short
            st.session_state.previous_maturity = maturity
            st.session_state.previous_interest_rate = interest_rate
            st.session_state.previous_volatility = volatility

            # Vérification des inputs
            if strike_price_long >= strike_price_short:
                st.error("❌ Erreur : Le strike du Long Call doit être **inférieur** au strike du Short Call.")
                disable_calculate = True  # Désactive le bouton de calcul
            else:
                disable_calculate = False  # Active le bouton de calcul

            # Création de l'objet CallSpread seulement si les inputs sont valides
            if not disable_calculate:
                call_spread_option = CallSpread(current_spot_price, strike_price_long, strike_price_short, maturity, interest_rate, volatility)

            # Calcul du prix de l'option Call Spread
            if st.button("Calculer le prix du Call Spread", disabled=disable_calculate):
                call_spread_price = call_spread_option.price()
                st.subheader("Caractéristiques (Long)")
                st.write(f"💶 **Prix du Call Spread** : {call_spread_price:.2f} €")

                # Afficher les valeurs des grecs
                st.write(f"**Δ** : {call_spread_option.delta():.4f}")
                st.write(f"**Γ** : {call_spread_option.gamma():.4f}")
                st.write(f"**ν** : {call_spread_option.vega():.4f}")
                st.write(f"**θ** : {call_spread_option.theta():.4f}")
                st.write(f"**ρ** : {call_spread_option.rho():.4f}")

                st.session_state.call_spread_price = call_spread_price

            # Bouton de réinitialisation
            if st.button("Réinitialiser"):
                st.session_state.clear()

        with col2:
            st.markdown("<br>" * 2, unsafe_allow_html=True)

            if 'call_spread_price' in st.session_state:
                call_spread_price = st.session_state.call_spread_price

                lower_bound = max(current_spot_price - volatility * current_spot_price * maturity, 0)
                upper_bound = current_spot_price + volatility * current_spot_price * maturity

                spot_prices = [i for i in range(int(lower_bound), int(upper_bound) + 1)]

                long_payoffs = [call_spread_option.payoff_long(spot) for spot in spot_prices]
                short_payoffs = [call_spread_option.payoff_short(spot) for spot in spot_prices]

                # Graphique Long
                fig_long, ax_long = plt.subplots(figsize=(8, 5))
                ax_long.plot(spot_prices, long_payoffs, label="Long", color='green', linewidth=2)
                ax_long.set_title("Payoff Long Call Spread")
                ax_long.set_xlabel("Prix Spot")
                ax_long.set_ylabel("Payoff (€)")
                ax_long.grid(True)
                ax_long.legend(loc="best")
                st.pyplot(fig_long)

                # Graphique Short
                fig_short, ax_short = plt.subplots(figsize=(8, 5))
                ax_short.plot(spot_prices, short_payoffs, label="Short", color='red', linewidth=2)
                ax_short.set_title("Payoff Short Call Spread")
                ax_short.set_xlabel("Prix Spot")
                ax_short.set_ylabel("Payoff (€)")
                ax_short.grid(True)
                ax_short.legend(loc="best")
                st.pyplot(fig_short)
            else:
                st.markdown(""" 
                <div style="display: flex; justify-content: center; align-items: center; height: 500px;">
                    <p style="text-align: center;">Cliquez sur 'Calculer le prix du Call Spread' pour afficher les graphiques.</p>
                </div>
                """, unsafe_allow_html=True)

#Section Suivi de Positions
elif section == "Suivi de Position":
    # Input du ticker
    ticker = st.text_input("Entrez le ticker de l'actif :")
    underlying = Underlying(ticker)
    underlying = st.session_state.get('underlying', underlying)
    r = FreeRate(0.03)
    #r.update_rate()

    # Création de 4 colonnes
    col1, col2, col3, col4 = st.columns([1, 1.4, 4, 5])

    # Bouton de validation
    with col1:
        if st.button("Valider"):
            if not ticker.strip():  # Vérifie si le champ est vide ou ne contient que des espaces
                st.session_state['validated'] = False
                with col3:
                    st.error("❌ Veuillez entrer un ticker avant de valider.")
            else:
                try:
                    underlying.update_data()
                    if underlying.data.empty:
                        st.session_state['validated'] = False
                        with col3:
                            st.error("❌ Ticker invalide. Veuillez réessayer.")
                    else:
                        st.session_state['underlying'] = underlying
                        st.session_state['validated'] = True
                        st.session_state['view_range'] = "1mo"  # Plage de vue par défaut
                except Exception as e:
                    st.session_state['validated'] = False
                    with col3:
                        st.error(f"❌ Ticker invalide. Veuillez réessayer.")

    # Bouton de réinitialisation
    with col2:
        if st.button("Réinitialiser"):
            st.session_state.clear()

    st.markdown("---")

    # Affichage du graphique si validation réussie
    if st.session_state.get('validated', False):

        # Affichage du titre centré avec le nom du sous-jacent
        if underlying:
            st.markdown(f"<h3 style='text-align: center;'>{underlying.name}</h3>", unsafe_allow_html=True)

        # Sélection de la plage de vue
        view_options = {
            "5 jours": "5d",
            "1 mois": "1mo",
            "6 mois": "6mo",
            "1 an": "1y",
            "All": "max"
        }

        selected_range = st.selectbox("Plage de vue :", list(view_options.keys()), index=3)
        st.session_state['view_range'] = view_options[selected_range]

        # Mettre à jour les données avec la période sélectionnée
        underlying.update_data(period=st.session_state['view_range'])

        # Récupération des données
        data = underlying.data  # Utilisation des données récupérées dans l'objet

        # Calcul de la variation du sous-jacent en pourcentage
        initial_price = data["Close"].iloc[0]  # Premier prix de clôture
        final_price = data["Close"].iloc[-1]  # Dernier prix de clôture
        variation = ((final_price - initial_price) / initial_price) * 100  # Variation en pourcentage

        # Récupérer les informations du sous-jacent
        spot_price = underlying.spot_price
        historical_vol = underlying.historical_vol
        implied_vol = underlying.implied_vol

        # Définir la couleur du graphique en fonction de la variation
        graph_color = 'green' if variation > 0 else 'red'

        # Graphique interactif avec Plotly
        fig = go.Figure()

        # Tracer les données de clôture avec la couleur dynamique
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name="Prix de Clôture", line=dict(color=graph_color)))

        # Informations à afficher sous le titre
        info_text = (
            f"Variation: {variation:.2f}% | "
            f"Spot Price: {spot_price:.2f} € | "
            f"Free Rate (US): {r.value*100:.2f}% | "
            f"Implied Vol: {implied_vol*100:.2f}% | "
            f"Historical Vol: {historical_vol*100:.2f}% | " if historical_vol is not None else "Volatilité historique indisponible | "
        )

        # Ajouter un titre au graphique
        fig.update_layout(
            title=f"<b>{underlying.name} - Closing Price</b><br><span style='font-size: 10px;'>{info_text}</span>",
        )

        # Mettre à jour les axes et titres
        fig.update_xaxes(title="Date")
        fig.update_yaxes(title="Prix (€)")

        # Afficher le graphique interactif
        st.plotly_chart(fig, use_container_width=True)

    # Création de deux colonnes pour les caractéristiques de l'option
    if st.session_state.get('validated', False):
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.write("### Caractéristiques")
            position = st.selectbox("Choisissez la position :", ["Long", "Short"], key="pos_type", index=0)
            option_type = st.selectbox("Choisissez l'option :", ["Call"], key="option_type", index=0)
            transaction_price = st.number_input("Prix d'achat de l'option :", min_value=0.0, value=5.0, step=5.0)
            K = st.number_input("Prix d'exercice (Strike) :", min_value=0.0, value=underlying.spot_price, step=5.0)
            maturity = st.date_input("Date d'échéance :", min_value=datetime.date.today(), value=datetime.date.today() + datetime.timedelta(days=365))

            if position != st.session_state.get('prev_position') or \
               option_type != st.session_state.get('prev_option_type') or \
               transaction_price != st.session_state.get('prev_transaction_price') or \
               K != st.session_state.get('prev_K') or \
               maturity != st.session_state.get('prev_maturity'):
                st.session_state['option'] = None

            st.session_state['prev_position'] = position
            st.session_state['prev_option_type'] = option_type
            st.session_state['prev_transaction_price'] = transaction_price
            st.session_state['prev_K'] = K
            st.session_state['prev_maturity'] = maturity

            # Création de l'option si validée
            if st.button("Suivre l'option"):
                time_to_maturity = TimeToMaturity(maturity_date=maturity)

                # Création de l'option selon le type choisi
                if st.session_state['option_type'] == "Call":
                    option = Call.from_instances(
                        underlying=st.session_state['underlying'],
                        strike=K,
                        time_to_maturity=time_to_maturity,
                        free_rate=r,
                        transaction_price=transaction_price
                    )
                st.session_state['option'] = option

        with col_right:
            # Récupérer l'option créée dans l'état de session
            option = st.session_state.get('option')
            if option:
                # Calculer le prix de l'option et son PnL
                option_price = option.price  # Calcul du prix de l'option

                if st.session_state['pos_type'] == "Long":
                    option.update_pnl("Long")
                elif st.session_state['pos_type'] == "Short":
                    option.update_pnl("Short")

                # Afficher le prix de l'option et le PnL
                st.write("### Détails en direct")
                st.write(f"💶 **Prix actuel de l'Option** : {option_price:.2f} €")
                st.write(f"⚖️ **PnL actuel** : {option.pnl:.2f} €")

                # Afficher les valeurs des grecs
                st.write(f"**Δ** : {option.delta(st.session_state['pos_type']):.4f}")
                st.write(f"**Γ** : {option.gamma(st.session_state['pos_type']):.4f}")
                st.write(f"**ν** : {option.vega(st.session_state['pos_type']):.4f}")
                st.write(f"**θ** : {option.theta(st.session_state['pos_type']):.4f}")
                st.write(f"**ρ** : {option.rho(st.session_state['pos_type']):.4f}")
            else:
                st.markdown(""" 
                <div style="display: flex; justify-content: center; align-items: center; height: 550px;">
                    <p style="text-align: center;">Cliquez sur 'Suivre l'option' pour afficher les détails en direct.</p>
                </div>
                """, unsafe_allow_html=True)
                
                

