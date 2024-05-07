from math import factorial
import time
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def rysuj_trasy(df, rozwiazanie, koszt, show=False):
    fig, ax = plt.subplots()

    kolory = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    marker_start = 's'  # Kwadratowy marker dla punktu startowego/koncowego
    marker_normal = 'o'  # Okrągły marker dla pozostałych punktów

    # Rysowanie tras dla każdego pojazdu
    for i, trasa in enumerate(rozwiazanie):
        punkty_x = df.iloc[trasa]['X'].tolist()
        punkty_y = df.iloc[trasa]['Y'].tolist()

        # Wstaw punkt startowy i końcowy na początek i koniec listy
        punkty_x.insert(0, df.iloc[0]['X'])
        punkty_y.insert(0, df.iloc[0]['Y'])
        punkty_x.append(df.iloc[0]['X'])
        punkty_y.append(df.iloc[0]['Y'])

        # Rysuj trasę z odpowiednim kolorem i markerem
        ax.plot(punkty_x, punkty_y, marker=marker_normal, color=kolory[i % len(kolory)], label=f'Pojazd {i + 1}')
        # Oznacz punkt startowy/koncowy innym kolorem i markerem
        ax.plot(df.iloc[0]['X'], df.iloc[0]['Y'], marker=marker_start, color='black')

    # Dodanie legendy i tytułu z kosztem
    ax.legend()
    ax.set_title(f'Wizualizacja tras pojazdów (Całkowity koszt: {koszt})')
    ax.set_xlabel('Współrzędna X')
    ax.set_ylabel('Współrzędna Y')
    ax.set_aspect('equal', adjustable='datalim')  # Zapewnia równą skalę osi

    # Opcjonalne wyświetlanie wykresu
    if show:
        plt.show()

    return fig

def generuj_poczatkowe_rozwiazanie(df, liczba_pojazdow, max_ladownosc):
    rozwiazanie = [[] for _ in range(liczba_pojazdow)]
    ladownosci_pojazdow = [0] * liczba_pojazdow
    do_odwiedzenia = set(df.index[1:])  # Zakładamy, że punkt 0 to baza

    # Startujemy każdy pojazd w bazie
    for aktualny_pojazd in range(liczba_pojazdow):
        if not do_odwiedzenia:
            break
        obecny_punkt = 0  # Start z bazy
        while do_odwiedzenia:
            # Wybór najbliższego sąsiada, który nie przekracza maksymalnej ładowności
            najblizszy = None
            min_dystans = float('inf')
            for punkt in do_odwiedzenia:
                dystans = np.sqrt((df.loc[punkt, 'X'] - df.loc[obecny_punkt, 'X'])**2 + (df.loc[punkt, 'Y'] - df.loc[obecny_punkt, 'Y'])**2)
                if dystans < min_dystans and ladownosci_pojazdow[aktualny_pojazd] + df.loc[punkt, 'masa'] <= max_ladownosc:
                    min_dystans = dystans
                    najblizszy = punkt

            if najblizszy is None:
                break  # Jeżeli żaden punkt nie spełnia kryteriów, zakończ trasę tego pojazdu

            # Dodaj punkt do trasy aktualnego pojazdu
            rozwiazanie[aktualny_pojazd].append(najblizszy)
            ladownosci_pojazdow[aktualny_pojazd] += df.loc[najblizszy, 'masa']
            do_odwiedzenia.remove(najblizszy)
            obecny_punkt = najblizszy

    return rozwiazanie

def ocen_rozwiazanie(rozwiazanie, df, max_ladownosc, max_droga):
    koszt_calkowity = 0
    kara_za_naruszenie_ładowności = 100000
    kara_za_naruszenie_dystansu = 50000
    suma_ladunkow = sum(df['masa'])  # Suma wszystkich ładunków
    oczekiwana_ladownosc = suma_ladunkow / len(rozwiazanie)  # Teoretyczna równa ładowność każdego pojazdu

    for trasa in rozwiazanie:
        if not trasa:
            continue
        
        dystans_trasy = 0
        ladownosc_trasy = 0
        
        for i in range(len(trasa)):
            if i == 0:  # Odległość od bazy do pierwszego punktu w trasie
                dystans_trasy += np.sqrt((df.iloc[trasa[i]]['X'] - df.iloc[0]['X'])**2 + (df.iloc[trasa[i]]['Y'] - df.iloc[0]['Y'])**2)
            else:  # Odległość między kolejnymi punktami w trasie
                dystans_trasy += np.sqrt((df.iloc[trasa[i]]['X'] - df.iloc[trasa[i-1]]['X'])**2 + (df.iloc[trasa[i]]['Y'] - df.iloc[trasa[i-1]]['Y'])**2)
            
            ladownosc_trasy += df.iloc[trasa[i]]['masa']
        
        # Dolicz powrót do bazy
        dystans_trasy += np.sqrt((df.iloc[trasa[-1]]['X'] - df.iloc[0]['X'])**2 + (df.iloc[trasa[-1]]['Y'] - df.iloc[0]['Y'])**2)
        
        # Kara za przekroczenie maksymalnej ładowności
        if ladownosc_trasy > max_ladownosc:
            koszt_calkowity += kara_za_naruszenie_ładowności
        
        # Kara za przekroczenie maksymalnej długości trasy
        if dystans_trasy > max_droga:
            koszt_calkowity += kara_za_naruszenie_dystansu
        
        # Kara za nierównomierne rozłożenie ładunków
        koszt_calkowity += (ladownosc_trasy - oczekiwana_ladownosc)**2
        
        koszt_calkowity += dystans_trasy
    
    return koszt_calkowity

def generuj_sasiedztwo(aktualne_rozwiazanie, df, max_ladownosc, max_droga, liczba_zmian=2):
    sasiedztwo = []
    liczba_pojazdow = len(aktualne_rozwiazanie)
    
    for _ in range(liczba_zmian):
        operacja = random.choice(['swap', 'reverse', 'relocate', 'intra_swap', 'intra_reverse'])
        nowe_rozwiazanie = [trasa.copy() for trasa in aktualne_rozwiazanie]

        if operacja == 'swap' and liczba_pojazdow > 1:
            pojazd_a, pojazd_b = random.sample(range(liczba_pojazdow), 2)
            if nowe_rozwiazanie[pojazd_a] and nowe_rozwiazanie[pojazd_b]:
                punkt_a = random.choice(nowe_rozwiazanie[pojazd_a])
                punkt_b = random.choice(nowe_rozwiazanie[pojazd_b])
                nowe_rozwiazanie[pojazd_a].remove(punkt_a)
                nowe_rozwiazanie[pojazd_b].remove(punkt_b)
                nowe_rozwiazanie[pojazd_a].append(punkt_b)
                nowe_rozwiazanie[pojazd_b].append(punkt_a)

        elif operacja == 'reverse' and any(len(trasa) > 1 for trasa in nowe_rozwiazanie):
            pojazd = random.choice([i for i, trasa in enumerate(nowe_rozwiazanie) if len(trasa) > 1])
            start_idx, end_idx = sorted(random.sample(range(len(nowe_rozwiazanie[pojazd])), 2))
            nowe_rozwiazanie[pojazd][start_idx:end_idx] = reversed(nowe_rozwiazanie[pojazd][start_idx:end_idx])

        elif operacja == 'relocate' and liczba_pojazdow > 1:
            pojazd_a, pojazd_b = random.sample(range(liczba_pojazdow), 2)
            if nowe_rozwiazanie[pojazd_a]:
                punkt = random.choice(nowe_rozwiazanie[pojazd_a])
                if sum(df.loc[p]['masa'] for p in nowe_rozwiazanie[pojazd_b]) + df.loc[punkt, 'masa'] <= max_ladownosc:
                    nowe_rozwiazanie[pojazd_a].remove(punkt)
                    nowe_rozwiazanie[pojazd_b].append(punkt)

        elif operacja == 'intra_swap' and any(len(trasa) > 1 for trasa in nowe_rozwiazanie):
            pojazd = random.choice([i for i, trasa in enumerate(nowe_rozwiazanie) if len(trasa) > 1])
            idx1, idx2 = random.sample(range(len(nowe_rozwiazanie[pojazd])), 2)
            nowe_rozwiazanie[pojazd][idx1], nowe_rozwiazanie[pojazd][idx2] = nowe_rozwiazanie[pojazd][idx2], nowe_rozwiazanie[pojazd][idx1]

        elif operacja == 'intra_reverse' and any(len(trasa) > 1 for trasa in nowe_rozwiazanie):
            pojazd = random.choice([i for i, trasa in enumerate(nowe_rozwiazanie) if len(trasa) > 1])
            start_idx, end_idx = sorted(random.sample(range(len(nowe_rozwiazanie[pojazd])), 2))
            nowe_rozwiazanie[pojazd][start_idx:end_idx] = nowe_rozwiazanie[pojazd][start_idx:end_idx][::-1]

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
        wykresy.append(rysuj_trasy(df, aktualne_rozwiazanie, aktualny_koszt))

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

        if najlepszy_koszt_sasiedztwa < najlepszy_koszt:
            najlepsze_rozwiazanie = najlepsze_sasiedztwo
            najlepszy_koszt = najlepszy_koszt_sasiedztwa
            aktualizuj_liste_tabu(lista_tabu, najlepsze_sasiedztwo, rozmiar_listy_tabu)
            
            if rysuj_etapy:
                wykresy.append(rysuj_trasy(df, najlepsze_rozwiazanie, najlepszy_koszt))  # Tutaj aktualizujemy koszt
        
    return najlepsze_rozwiazanie, wykresy

def oszacuj_czas_brute_force(liczba_punktow):
    liczba_kombinacji = factorial(liczba_punktow - 1)
    czas_w_sekundach = liczba_kombinacji * 1e-6
    return liczba_kombinacji, czas_w_sekundach

punkt_startowy = 0
liczba_pojazdow = 4
max_ladownosc = 4
max_droga = 3000
iteracje = 5000
rozmiar_listy_tabu = 10

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
