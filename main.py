from math import factorial
import time
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generuj_sasiedztwo(aktualne_rozwiazanie, df, max_ladownosc, max_droga, aktualny_koszt):
    """Generuje listę sąsiednich rozwiązań poprzez zamianę dwóch dowolnych punktów oraz lokalną optymalizację 2-opt i 3-opt."""
    sasiedztwo = []
    liczba_pojazdow = len(aktualne_rozwiazanie)
    
    # Zamiana punktów między trasami
    for _ in range(20):  # Zwiększenie liczby sąsiednich rozwiązań
        rozwiazanie_kopia = [trasa[:] for trasa in aktualne_rozwiazanie if isinstance(trasa, list) and len(trasa) > 0]
        if len(rozwiazanie_kopia) < 2:
            continue  # Przerywamy iterację, jeśli mniej niż dwie trasy są odpowiednie do zamiany

        pojazd1, pojazd2 = random.sample(range(len(rozwiazanie_kopia)), 2)
        trasa1, trasa2 = rozwiazanie_kopia[pojazd1], rozwiazanie_kopia[pojazd2]

        index1, index2 = random.randint(0, len(trasa1) - 1), random.randint(0, len(trasa2) - 1)
        # Zamiana punktów
        trasa1[index1], trasa2[index2] = trasa2[index2], trasa1[index1]
        
        sasiedztwo.append(rozwiazanie_kopia)

    # Zamiana punktów wewnątrz tras
    for trasa in aktualne_rozwiazanie:
        if len(trasa) < 2:
            continue
        for _ in range(10):  # Dodanie kilku zamian wewnątrz tras
            rozwiazanie_kopia = [t[:] for t in aktualne_rozwiazanie]
            trasa_kopia = trasa[:]
            i, j = random.sample(range(len(trasa_kopia)), 2)
            trasa_kopia[i], trasa_kopia[j] = trasa_kopia[j], trasa_kopia[i]
            rozwiazanie_kopia[aktualne_rozwiazanie.index(trasa)] = trasa_kopia
            sasiedztwo.append(rozwiazanie_kopia)

    # Lokalna optymalizacja 2-opt i 3-opt dla każdej trasy w każdym rozwiązaniu
    for rozwiazanie in aktualne_rozwiazanie:
        for idx, trasa in enumerate(rozwiazanie):
            if isinstance(trasa, list) and len(trasa) > 2:
                nowa_trasa = optimize_2opt(trasa[:], df)
                nowe_rozwiazanie = [tr[:] for tr in aktualne_rozwiazanie]
                nowe_rozwiazanie[idx] = nowa_trasa
                sasiedztwo.append(nowe_rozwiazanie)
                
                # Dodanie 3-opt
                if len(trasa) > 3:
                    nowa_trasa_3opt = optimize_3opt(trasa[:], df)
                    nowe_rozwiazanie_3opt = [tr[:] for tr in aktualne_rozwiazanie]
                    nowe_rozwiazanie_3opt[idx] = nowa_trasa_3opt
                    sasiedztwo.append(nowe_rozwiazanie_3opt)

    return sasiedztwo

def optimize_2opt(route, df):
    """Optymalizacja 2-opt dla jednej trasy."""
    best_route = route
    best_distance = calculate_distance(route, df)
    improved = True

    while improved:
        improved = False
        for i in range(1, len(route) - 1):
            for j in range(i + 1, len(route)):
                new_route = route[:i] + route[i:j][::-1] + route[j:]
                new_distance = calculate_distance(new_route, df)
                if new_distance < best_distance:
                    best_route = new_route
                    best_distance = new_distance
                    improved = True
        route = best_route

    return best_route

def optimize_3opt(route, df):
    """Optymalizacja 3-opt dla jednej trasy."""
    best_route = route
    best_distance = calculate_distance(route, df)
    improved = True

    while improved:
        improved = False
        for i in range(1, len(route) - 2):
            for j in range(i + 1, len(route) - 1):
                for k in range(j + 1, len(route)):
                    new_routes = [
                        route[:i] + route[i:j][::-1] + route[j:k][::-1] + route[k:],
                        route[:i] + route[j:k] + route[i:j] + route[k:],
                        route[:i] + route[j:k][::-1] + route[i:j][::-1] + route[k:],
                    ]
                    for new_route in new_routes:
                        new_distance = calculate_distance(new_route, df)
                        if new_distance < best_distance:
                            best_route = new_route
                            best_distance = new_distance
                            improved = True
        route = best_route

    return best_route

def sprawdz_ograniczenia(rozwiazanie, df, max_ladownosc, max_droga):
    przekroczenie_ladownosci = False
    przekroczenie_dystansu = False

    for trasa in rozwiazanie:
        dystans_trasy = 0
        ladownosc_trasy = 0
        
        for i in range(len(trasa)):
            if i == 0:
                dystans_trasy += np.sqrt((df.iloc[trasa[i]]['X'] - df.iloc[0]['X'])**2 + (df.iloc[trasa[i]]['Y'] - df.iloc[0]['Y'])**2)
            else:
                dystans_trasy += np.sqrt((df.iloc[trasa[i]]['X'] - df.iloc[trasa[i-1]]['X'])**2 + (df.iloc[trasa[i]]['Y'] - df.iloc[trasa[i-1]]['Y'])**2)
            
            ladownosc_trasy += df.iloc[trasa[i]]['masa']
        
        dystans_trasy += np.sqrt((df.iloc[trasa[-1]]['X'] - df.iloc[0]['X'])**2 + (df.iloc[trasa[-1]]['Y'] - df.iloc[0]['Y'])**2)
        
        if ladownosc_trasy > max_ladownosc:
            przekroczenie_ladownosci = True
        
        if dystans_trasy > max_droga:
            przekroczenie_dystansu = True

    return przekroczenie_ladownosci, przekroczenie_dystansu

def calculate_distance(route, df):
    """Oblicza całkowity dystans dla danej trasy."""
    distance = 0
    # Oblicz dystans pomiędzy kolejnymi punktami
    for i in range(1, len(route)):
        distance += np.sqrt((df.iloc[route[i]]['X'] - df.iloc[route[i-1]]['X'])**2 + (df.iloc[route[i]]['Y'] - df.iloc[route[i-1]]['Y'])**2)
    # Dodaj dystans powrotu do punktu startowego
    distance += np.sqrt((df.iloc[route[-1]]['X'] - df.iloc[route[0]]['X'])**2 + (df.iloc[route[-1]]['Y'] - df.iloc[route[0]]['Y'])**2)
    return distance

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
    else:
        plt.close(fig)

    return fig

def generuj_poczatkowe_rozwiazanie(df, liczba_pojazdow, max_ladownosc):
    rozwiazanie = [[] for _ in range(liczba_pojazdow)]
    ladownosci_pojazdow = [0] * liczba_pojazdow
    do_odwiedzenia = set(df.index[1:])  # Zakładamy, że punkt 0 to baza

    while do_odwiedzenia:
        for aktualny_pojazd in range(liczba_pojazdow):
            if not do_odwiedzenia:
                break
            obecny_punkt = 0 if not rozwiazanie[aktualny_pojazd] else rozwiazanie[aktualny_pojazd][-1]
            najblizszy = None
            min_dystans = float('inf')
            for punkt in do_odwiedzenia:
                dystans = np.sqrt((df.loc[punkt, 'X'] - df.loc[obecny_punkt, 'X'])**2 + (df.loc[punkt, 'Y'] - df.loc[obecny_punkt, 'Y'])**2)
                if dystans < min_dystans and ladownosci_pojazdow[aktualny_pojazd] + df.loc[punkt, 'masa'] <= max_ladownosc:
                    min_dystans = dystans
                    najblizszy = punkt

            if najblizszy is None:
                continue

            rozwiazanie[aktualny_pojazd].append(najblizszy)
            ladownosci_pojazdow[aktualny_pojazd] += df.loc[najblizszy, 'masa']
            do_odwiedzenia.remove(najblizszy)

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

def aktualizuj_liste_tabu(lista_tabu, nowy_element, rozmiar_listy_tabu):
    lista_tabu.append(nowy_element)
    while len(lista_tabu) > rozmiar_listy_tabu:
        lista_tabu.pop(0) 

def tabu_search(df, liczba_pojazdow, max_ladownosc, max_droga, iteracje, rozmiar_listy_tabu):
    najlepsze_rozwiazanie = None
    najlepszy_koszt = float('inf')
    lista_tabu = []
    aktualne_rozwiazanie = generuj_poczatkowe_rozwiazanie(df, liczba_pojazdow, max_ladownosc)
    aktualny_koszt = ocen_rozwiazanie(aktualne_rozwiazanie, df, max_ladownosc, max_droga)
    brak_poprawy_iteracje = 0
    maks_brak_poprawy_iteracje = 100

    for iteracja in range(iteracje):
        sasiedztwo = generuj_sasiedztwo(aktualne_rozwiazanie, df, max_ladownosc, max_droga, aktualny_koszt)
        sasiedztwo = [r for r in sasiedztwo if r not in lista_tabu]
        
        najlepsze_sasiedztwo = None
        najlepszy_koszt_sasiedztwa = float('inf')
        
        for kandydat in sasiedztwo:
            koszt_kandydata = ocen_rozwiazanie(kandydat, df, max_ladownosc, max_droga)
            if koszt_kandydata < najlepszy_koszt_sasiedztwa:
                najlepsze_sasiedztwo = kandydat
                najlepszy_koszt_sasiedztwa = koszt_kandydata

        if najlepsze_sasiedztwo is not None and najlepszy_koszt_sasiedztwa < najlepszy_koszt:
            najlepsze_rozwiazanie = najlepsze_sasiedztwo
            najlepszy_koszt = najlepszy_koszt_sasiedztwa
            aktualne_rozwiazanie = najlepsze_sasiedztwo
            aktualny_koszt = najlepszy_koszt_sasiedztwa
            aktualizuj_liste_tabu(lista_tabu, najlepsze_sasiedztwo, rozmiar_listy_tabu)
            brak_poprawy_iteracje = 0
        else:
            brak_poprawy_iteracje += 1
        
        if brak_poprawy_iteracje > maks_brak_poprawy_iteracje:
            aktualne_rozwiazanie = generuj_poczatkowe_rozwiazanie(df, liczba_pojazdow, max_ladownosc)
            aktualny_koszt = ocen_rozwiazanie(aktualne_rozwiazanie, df, max_ladownosc, max_droga)
            brak_poprawy_iteracje = 0
        
    przekroczenie_ladownosci, przekroczenie_dystansu = sprawdz_ograniczenia(najlepsze_rozwiazanie, df, max_ladownosc, max_droga)
    return najlepsze_rozwiazanie, najlepszy_koszt, przekroczenie_ladownosci, przekroczenie_dystansu

def oszacuj_czas_brute_force(liczba_punktow):
    liczba_kombinacji = factorial(liczba_punktow - 1)
    czas_w_sekundach = liczba_kombinacji * 1e-6
    return liczba_kombinacji, czas_w_sekundach

#Ladownosc: 
#dane - masa 4x4 = 16
#dane2 - masa 4x3900 trasa 230x4
#dane3 - masa 47 trasa 4x16000

#DATASET1
punkt_startowy = 0
liczba_pojazdow = 4
max_ladownosc = 4
max_droga = 1600
iteracje = 100
rozmiar_listy_tabu = 10
plik_excel = 'dane.xlsx'

#DATASET 2
"""punkt_startowy = 0
liczba_pojazdow = 4
max_ladownosc = 3900
max_droga = 230
iteracje = 10000
rozmiar_listy_tabu = 50
plik_excel = 'dane2.xlsx'
"""

#DATASET 3
"""punkt_startowy = 0
liczba_pojazdow = 4
max_ladownosc = 13
max_droga = 16000
iteracje = 10000
rozmiar_listy_tabu = 100
plik_excel = 'dane3.xlsx'
"""

df = pd.read_excel(plik_excel, usecols=['X', 'Y', 'masa'])
liczba_punktow = len(df)
liczba_kombinacji, czas_w_sekundach = oszacuj_czas_brute_force(liczba_punktow)
print(f"Liczba możliwych kombinacji: {liczba_kombinacji}, Oszacowany czas (s): {czas_w_sekundach}")

najlepsze_rozwiazanie, koszt_najlepszego_rozwiazania, przekroczenie_ladownosci, przekroczenie_dystansu = tabu_search(df, liczba_pojazdow, max_ladownosc, max_droga, iteracje, rozmiar_listy_tabu)

if najlepsze_rozwiazanie is not None:
    print("Najlepsze znalezione rozwiązanie:")
    for nr, trasa in enumerate(najlepsze_rozwiazanie):
        full_trasa = [0] + trasa + [0]
        print(f"Pojazd {nr + 1}: Trasa - {full_trasa}")
    print(f"Całkowity koszt najlepszego rozwiązania: {koszt_najlepszego_rozwiazania}")

    if przekroczenie_ladownosci:
        print("Przekroczono maksymalną ładowność.")
    if przekroczenie_dystansu:
        print("Przekroczono maksymalną długość trasy.")
        
    fig = rysuj_trasy(df, najlepsze_rozwiazanie, koszt_najlepszego_rozwiazania, show=True)
else:
    print("Nie znaleziono żadnego dopuszczalnego rozwiązania.")

