from math import factorial
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def rysuj_trasy(df, rozwiazanie, show=False):
    fig, ax = plt.subplots()

    kolory = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

    for i, trasa in enumerate(rozwiazanie):
        punkty_x = df.iloc[trasa]['X'].tolist()
        punkty_y = df.iloc[trasa]['Y'].tolist()

        punkty_x.insert(0, df.iloc[0]['X'])
        punkty_y.insert(0, df.iloc[0]['Y'])

        punkty_x.append(df.iloc[0]['X'])
        punkty_y.append(df.iloc[0]['Y'])

        ax.plot(punkty_x, punkty_y, marker='o', color=kolory[i % len(kolory)], label=f'Pojazd {i + 1}')

    ax.legend()
    ax.set_title('Wizualizacja tras pojazdów')
    ax.set_xlabel('Współrzędna X')
    ax.set_ylabel('Współrzędna Y')

    if show:
        plt.show()

    return fig

def generuj_poczatkowe_rozwiazanie(df, liczba_pojazdow, max_ladownosc):
    rozwiazanie = [[] for _ in range(liczba_pojazdow)]
    ladownosci_pojazdow = [0] * liczba_pojazdow
    aktualny_pojazd = 0
    
    for index, punkt in df.iterrows():
        if ladownosci_pojazdow[aktualny_pojazd] + punkt['masa'] > max_ladownosc:
            aktualny_pojazd = (aktualny_pojazd + 1) % liczba_pojazdow  

        if ladownosci_pojazdow[aktualny_pojazd] + punkt['masa'] <= max_ladownosc:
            rozwiazanie[aktualny_pojazd].append(index)
            ladownosci_pojazdow[aktualny_pojazd] += punkt['masa']
        else:
            print(f"Nie można przydzielić punktu {index} do żadnego pojazdu bez przekroczenia maksymalnej ładowności.")
    
    return rozwiazanie

def ocen_rozwiazanie(rozwiazanie, df, max_ladownosc, max_droga):
    koszt_calkowity = 0
    kara_za_naruszenie_ładowności = 100000 
    kara_za_naruszenie_dystansu = 50000  
    
    for trasa in rozwiazanie:
        if not trasa:
            continue
            
        dystans_trasy = 0
        ladownosc_trasy = 0
        
        for i in range(len(trasa)):
            if i == 0:  
                dystans_trasy += np.sqrt((df.iloc[trasa[i]]['X'] - df.iloc[0]['X'])**2 + (df.iloc[trasa[i]]['Y'] - df.iloc[0]['Y'])**2)
            else:  
                dystans_trasy += np.sqrt((df.iloc[trasa[i]]['X'] - df.iloc[trasa[i-1]]['X'])**2 + (df.iloc[trasa[i]]['Y'] - df.iloc[trasa[i-1]]['Y'])**2)
            
            ladownosc_trasy += df.iloc[trasa[i]]['masa']
        
        if trasa:
            dystans_trasy += np.sqrt((df.iloc[trasa[-1]]['X'] - df.iloc[0]['X'])**2 + (df.iloc[trasa[-1]]['Y'] - df.iloc[0]['Y'])**2)
        
        if ladownosc_trasy > max_ladownosc:
            koszt_calkowity += kara_za_naruszenie_ładowności
        if dystans_trasy > max_droga:
            koszt_calkowity += kara_za_naruszenie_dystansu
        
        koszt_calkowity += dystans_trasy
    
    return koszt_calkowity

def generuj_sasiedztwo(aktualne_rozwiazanie, df, max_ladownosc, max_droga, liczba_zmian=2):
    sasiedztwo = []
    liczba_pojazdow = len(aktualne_rozwiazanie)
    
    for _ in range(liczba_zmian):
        nowe_rozwiazanie = [trasa.copy() for trasa in aktualne_rozwiazanie]
        
        if liczba_pojazdow > 1:
            pojazd_a, pojazd_b = np.random.choice(range(liczba_pojazdow), 2, replace=False)
            
            if not nowe_rozwiazanie[pojazd_a] or not nowe_rozwiazanie[pojazd_b]:
                continue

            punkt_a = np.random.choice(nowe_rozwiazanie[pojazd_a])
            punkt_b = np.random.choice(nowe_rozwiazanie[pojazd_b])

            nowe_rozwiazanie[pojazd_a].remove(punkt_a)
            nowe_rozwiazanie[pojazd_b].remove(punkt_b)
            nowe_rozwiazanie[pojazd_a].append(punkt_b)
            nowe_rozwiazanie[pojazd_b].append(punkt_a)
        else:
            # Gdy mamy tylko jeden pojazd, wykonujemy permutację w jego trasie
            if len(nowe_rozwiazanie[0]) > 1:
                np.random.shuffle(nowe_rozwiazanie[0])

        sasiedztwo.append(nowe_rozwiazanie)
    
    return sasiedztwo

def aktualizuj_liste_tabu(lista_tabu, nowy_element, rozmiar_listy_tabu):
    lista_tabu.append(nowy_element)
    while len(lista_tabu) > rozmiar_listy_tabu:
        lista_tabu.pop(0) 

def tabu_search(df, liczba_pojazdow, max_ladownosc, max_droga, iteracje, rozmiar_listy_tabu, rysuj_etapy=False):
    najlepsze_rozwiazanie = None
    najlepszy_koszt = float('inf')
    lista_tabu = []
    aktualne_rozwiazanie = generuj_poczatkowe_rozwiazanie(df, liczba_pojazdow, max_ladownosc)
    aktualny_koszt = ocen_rozwiazanie(aktualne_rozwiazanie, df, max_ladownosc, max_droga)
    wykresy = []

    if rysuj_etapy:
        wykresy.append(rysuj_trasy(df, aktualne_rozwiazanie))

    for iteracja in range(iteracje):
        sasiedztwo = generuj_sasiedztwo(aktualne_rozwiazanie, df, max_ladownosc, max_droga)
        sasiedztwo = [r for r in sasiedztwo if r not in lista_tabu]
        
        najlepsze_sasiedztwo = None
        najlepszy_koszt_sasiedztwa = float('inf')
        
        for kandydat in sasiedztwo:
            koszt_kandydata = ocen_rozwiazanie(kandydat, df, max_ladownosc, max_droga)
            if koszt_kandydata < najlepszy_koszt_sasiedztwa:
                najlepsze_sasiedztwo = kandydat
                najlepszy_koszt_sasiedztwa = koszt_kandydata

            #print("----------")
            #print(najlepszy_koszt_sasiedztwa)
            #print("VS")
            #print(najlepszy_koszt)
            #print("----------")
        if najlepszy_koszt_sasiedztwa < najlepszy_koszt:
            print("Vin")
            najlepsze_rozwiazanie = najlepsze_sasiedztwo
            najlepszy_koszt = najlepszy_koszt_sasiedztwa
            aktualizuj_liste_tabu(lista_tabu, najlepsze_sasiedztwo, rozmiar_listy_tabu)
            
            if rysuj_etapy:
                wykresy.append(rysuj_trasy(df, najlepsze_rozwiazanie))
        
    return najlepsze_rozwiazanie, wykresy

def oszacuj_czas_brute_force(liczba_punktow):
    liczba_kombinacji = factorial(liczba_punktow - 1)
    czas_w_sekundach = liczba_kombinacji * 1e-6
    return liczba_kombinacji, czas_w_sekundach

punkt_startowy = 0
liczba_pojazdow = 4
max_ladownosc = 4
max_droga = 3000
iteracje = 1000
rozmiar_listy_tabu = 100

plik_excel = 'dane.xlsx'
df = pd.read_excel(plik_excel, usecols=['X', 'Y', 'masa'])
#print(df)

liczba_punktow = len(df)
liczba_kombinacji, czas_w_sekundach = oszacuj_czas_brute_force(liczba_punktow)
print(f"Liczba możliwych kombinacji: {liczba_kombinacji}, Oszacowany czas (s): {czas_w_sekundach}")

najlepsze_rozwiazanie, wykresy = tabu_search(df, liczba_pojazdow, max_ladownosc, max_droga, iteracje, rozmiar_listy_tabu, rysuj_etapy=True)


if najlepsze_rozwiazanie is not None:
    koszt_najlepszego_rozwiazania = ocen_rozwiazanie(najlepsze_rozwiazanie, df, max_ladownosc, max_droga)
    print("Najlepsze znalezione rozwiązanie:")
    for nr, trasa in enumerate(najlepsze_rozwiazanie):
        print(f"Pojazd {nr + 1}: Trasa - {trasa}")
    print(f"Całkowity koszt najlepszego rozwiązania: {koszt_najlepszego_rozwiazania}")
else:
    print("Nie znaleziono żadnego dopuszczalnego rozwiązania.")

for fig in wykresy:
    plt.figure(fig.number)
    plt.show()
