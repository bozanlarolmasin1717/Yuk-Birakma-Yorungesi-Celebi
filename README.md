# Yük Bırakma Yörüngesi — Çelebi

Hareket halindeki bir İHA'dan bırakılan faydalı yükün yerçekimi, hava sürtünmesi ($C_d$) ve rüzgar etkileri altındaki düşüş yörüngesini görselleştiren ve tersine hedefleme (Release Point) analizini sunan simülasyon arayüzü.

## Mimari ve Klasör Yapısı

```text
├── app.py                         # Streamlit etkileşimli arayüz giriş noktası
├── requirements.txt
├── src/
│   ├── ui/                        # Tema (açık/koyu), kenar çubuğu ve metrik panelleri
│   ├── visualization/             # Saf Python grafik motoru (Plotly + statik Matplotlib)
│   ├── integration/               # Demo sağlayıcı ve gerçek fizik motoru adaptörü
│   └── targeting/                 # 7.3 Tersine hesaplama modülü alanı
└── tests/
    └── test_visualization.py      # Şema ve grafik doğrulama testleri
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
