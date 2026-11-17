# Yük Bırakma Yörüngesi — Çelebi

Hareket halindeki bir İHA'dan bırakılan faydalı yükün yerçekimi, hava sürtünmesi ($C_d$) ve rüzgar etkileri altındaki düşüş yörüngesini hesaplayan, tersine hedefleme (Release Point) çözen ve canlı olarak görselleştiren simülasyon arayüzü.

## Modüller

- **7.1 Balistik Hareket Denklemleri (`balistik_motor.compute_vacum_ballistics`):** İlk hız, bırakılma irtifası ve yerçekimi ile sürtünmesiz analitik düşüş hesabı.
- **7.2 Hava Sürtünmesi ve Rüzgar (`balistik_motor.simulate_trajectory`):** RK4 (`dt = 0.01 s`) integrasyonu, kuadratik hava sürüklemesi ($C_d$), ISA yoğunluk ve yükseklikle değişen rüzgar modeli.
- **7.3 Hedefleme Algoritması (`src/targeting/release_solver.py`):** Sabit-nokta vektör kaydırma, sönümlü 2B Newton-Raphson ve sabit hat 1B Sekant çözücüleri ile ideal bırakma noktası hesabı.

## Mimari ve Klasör Yapısı

```text
├── app.py                         # Streamlit ana arayüzü (7.1 / 7.2 / 7.3 modül seçimi)
├── koordinatsistemi.py            # ENU koordinat sistemi ve fiziksel veri yapıları
├── balistik_motor.py              # 7.1 analitik vakum ve 7.2 RK4 ileri fizik motoru
├── requirements.txt
└── src/
    ├── targeting/                 # 7.3 Tersine bırakma noktası çözücüsü ve sözleşmeler
    ├── integration/adapter.py     # İleri fizik motoru ile 7.3/görselleştirme köprüsü
    ├── visualization/             # Saf Python grafik motoru (Plotly + statik Matplotlib)
    └── ui/                        # Tema (açık/koyu), 2B yön kadranları, canlı simülatör
```

## Kurulum ve Çalıştırma

MSYS2 Python'un PATH üzerinde olması durumunda kaynak derleme hatalarını önlemek için kurulumu `uv` ile yönetilen standart Windows CPython 3.12 üzerinden yapın:

```powershell
uv venv --python 3.12 --python-preference only-managed
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
streamlit run app.py
```

## Testler

```powershell
pytest
```
