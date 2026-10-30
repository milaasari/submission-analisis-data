# Proyek Analisis Data: E-Commerce Public Dataset (Olist)
By : Mila Sari Rusadi

Analisis data e-commerce untuk menuntaskan submission dicoding, analisis ini dibuat untuk menjawab pertanyaan berikut:
1. Kategori produk apa yang menyumbang revenue tertinggi/terendah dan bagaimana tren bulanan 5 kategori teratas?
2. Bagaimana sebaran segmen pelanggan (RFM) dan negara bagian mana yang paling besar kontribusi revenue-nya?

## Struktur Folder
```
submission
├── dashboard
│   ├── main_data.csv
│   ├── state_geo.csv
│   └── dashboard.py
├── data
│   └── *.csv  (dataset asli)
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment
```
python -m venv venv
venv\Scripts\activate        # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```

## Menjalankan Dashboard
Dari folder `submission`:
```
streamlit run dashboard/dashboard.py
```
Dashboard terbuka di http://localhost:8501.

## Menjalankan Notebook
Buka `notebook.ipynb` (Jupyter/VS Code/Colab) dari folder `submission` lalu jalankan semua cell (`Run All`). Cell terakhir akan membuat ulang `dashboard/main_data.csv` dan `dashboard/state_geo.csv`.
