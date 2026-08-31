# Turan Tovuz PFK — Oyun Günü Sorğusu Təhlili

Turan Tovuz PFK-nın stadionunda keçirilmiş **oyun günü təcrübəsi sorğusunun** (52 respondent) tam təmizlənməsi, kəşfiyyat analizi (EDA) və nəticə əsaslı tövsiyələr paketi. Xam Excel məlumatı təmiz, analiz-hazır formaya salınıb, sonra Power BI dashboard üçün ayrıca export edilib.

## 📁 Layihə strukturu

```
fif_project/
├── data/
│   ├── raw/
│   │   └── Turan_oyun günü sorğusu.xlsx      # Xam Google Forms/Excel məlumatı
│   └── processed/
├── notebooks/
│   ├── 01_data_cleaning.ipynb                # Xam datanın təmizlənməsi
│   └── 02_eda.ipynb                          # Kəşfiyyat analizi + Insight & Solutions bölməsi
├── outputs/
│   ├── figures/                              # Notebook-larda yaradılan qrafiklər
│   └── reports/
│       └── Turan_Tovuz_dashboards.pbix       # Power BI dashboard
├── src/
│   ├── config.py                             # Data yolları (DATA_RAW, DATA_PROCESSED)
│   ├── data_loader.py                        # load_raw / save_processed / load_processed
│   └── preprocessing.py                      # Bütün təmizləmə funksiyaları (aşağıda)
├── main.py
├── pyproject.toml
└── uv.lock
```

## 🔄 İş axını

```
data/raw/*.xlsx
      │
      ▼
01_data_cleaning.ipynb  ──►  data/processed/cleaned_survey_data.csv
      │
      ▼
02_eda.ipynb  ──►  data/processed/*.csv (dashboard üçün 6 ayrı fayl)
      │
      ▼
Power BI  ──►  outputs/reports/Turan_Tovuz_dashboards.pbix
```

## 🧹 Data təmizləmə (`01_data_cleaning.ipynb`)

Xam sorğu datasında əsas problem: bir çox sual **sərbəst mətn** şəklində cavablandırılıb (multi-select yox), ona görə eyni fikir onlarla fərqli yazılışla gəlib. Bunun üçün `src/preprocessing.py`-də **regex-əsaslı whitelist** yanaşması qurulub — hər real dəyər üçün bütün bilinən yazılış variantlarını tutan bir pattern yazılıb, tanınmayan mətnlər isə səssizcə atılmır, ayrıca xəbərdarlıq kimi çıxarılır.

| Sütun | Problem | Həll |
|---|---|---|
| **Sütun adları** | Boşluq/sətir sonu uyğunsuzluqları | Regex ilə normallaşdırma (`\s+` → tək boşluq, durğu işarəsindən əvvəlki boşluq atılır) |
| **Sponsor adları** (`Bunlar hansılardır?`) | Bir neçə sponsor vergül/slash/boşluqla qarışıq yazılıb, eyni sponsorun 5+ yazılış forması var (huner qrup, hünər grup, hg...) | `clean_sponsor_columns()` — hər sponsor üçün regex pattern, standartlaşdırma + vergüllə ayrılmış təmiz siyahı |
| **Rayon/kənd adları** | 14 real yerin ~30 yazılış forması (Tovuz r, tovuz rayonu, Aşğıqulşu, bozaqanlı...) | `clean_region_column()` — spesifikdən ümumiyə sıralanmış regex, Azərbaycan hərf variasiyalarına (ə/e, ı/i, ş/s...) dözümlü |
| **Pul xərci sualları** | "10 AZN", "5manat", "3-4" (aralıq), "7-dən çox" kimi qarışıq mətn | `parse_money()` — rəqəmi çıxarır, aralığın ortasını götürür, "çox" ifadəsini təxmini rəqəmə çevirir |
| **Yaş** | "1985 martın 14", "Tovuz" kimi mətn cavablar | Əlavə kontekstdən (digər sütunlar) əsaslanaraq əl ilə düzəldilib, sonra rəqəmə çevrilib |
| **Neçə nəfər gəlib / uşaq var idi** | "3-4", "Tək gəlmişəm", "2 Oğul ilə" kimi sərbəst mətn | Məntiqi əsaslandırma ilə əl ilə map edilib, sonra `Int64`-ə çevrilib |
| **Ailəyə uyğunluq** | "50 faiz", "Söyüş söyülməsi" kimi izahlı cavablar | Mənasına görə 3 kateqoriyaya (Bəli/Qismən/Xeyr) map edilib |
| **Boş dəyərlər** | Sualın aid olmadığı strukturaldan yaranan NaN-lar | Kontekstə uyğun default dəyərlərlə dolduruldu (məs. "Stadionda baxıram", "Qeyd olunmayıb") |

Nəticə `data/processed/cleaned_survey_data.csv`-ə yazılır.

## 📊 Kəşfiyyat analizi (`02_eda.ipynb`)

8 bölmədən ibarətdir, hər biri ayrıca sual qrupuna baxır:

1. **Sponsor görünürlüyü vs reytinqlər** — sponsor sayı artdıqca məmnuniyyət necə dəyişir
2. **Xərcləmə davranışı** — qida/fanşop xərci cins, yaş, məşğuliyyət, uşaqla gəlmə üzrə
3. **Loyallıq və tövsiyə** — geri qayıtma niyyətinə görə reytinq fərqləri, rayon üzrə loyallıq
4. **Ümumi problem tezliyi** — 18 problemlik whitelist/regex sistemi ilə bütün 52 respondent üzrə etibarlı təhlil (sadə `split(',')` yalnız kiçik alt-qrup üçün doğrudur, ona görə eyni prinsiplə tam regex whitelist qurulub)
5. **Coğrafi/demoqrafik profil** — rayon/kənd, yaş, cins, nəqliyyat seçimi
6. **Reytinqlər arası korrelyasiya** — hansı təcrübə sahələri "birgə hərəkət edir"
7. **Məlumat mənbəyi və bilet kanalı** — whitelist ilə 6 kateqoriyaya salınmış bilet kanalları, kanala görə loyallıq
8. **Ailə təcrübəsi** — ailəyə uyğunluq, uşaqla/uşaqsız qrupların fərqli problemləri

Notebook-un sonunda **Power BI üçün 6 ayrı export** aparılır (yuxarıdakı struktur cədvəlinə bax) və bütün insight/tövsiyələr `## Turan Tovuz PFK — Əsas Nəticələr və Tövsiyələr` bölməsində yazılı formada toplanıb.

## 💡 Əsas insight-lar

| # | Tapıntı | Tövsiyə |
|---|---|---|
| 1 | **Çıxışda sıxlıq** ən çox bildirilən problemdir (8 nəfər), demək olar tamamilə **uşaqlı ailələrə** aiddir | Fazalı çıxış, ailə üçün ayrıca yaxın çıxış/parkinq |
| 2 | Ailəyə uyğunluğa **"Xeyr"** deyənlərin faizi uşaqla gəl**məyənlər** arasında daha yüksəkdir (52% vs 31%) — insanlar şərait uyğun olmadığı üçün uşağı **gətirmirlər**, sonradan narazı qalmırlar | Konkret "ailə paketi" (uşaq zonası, endirim) yaratmaq və elan etmək |
| 3 | Fanşopdan cəmi **17%** alış-veriş edib, orta xərc kişi/qadın arasında 3 dəfə fərqlənir (30.29 AZN vs 10 AZN) | Fanşopu daha görünən yerə çıxarmaq, aşağı qiymətli suvenir xətti əlavə etmək |
| 4 | Sponsor görməyən qrupda ümumi məmnuniyyət **kəskin aşağıdır** (7.27 vs 10.00); tanınan sponsorların **73%-i tək bir marka** (HUNER GROUP) | Sponsor reklamlarının stadionda bərabər paylanması |
| 5 | Biletlərin **73%-i** fiziki kassadan alınır, alternativ kanal demək olar yoxdur | Onlayn/mobil bilet satışını sosial media üzərindən təşviq etmək |
| 6 | Respondentlərin **94%-i kişi** — nəticələr, xüsusən qadın/ailə seqmentinə aid olanlar, ehtiyatla şərh olunmalıdır | Növbəti sorğunu daha geniş/balanslaşdırılmış auditoriyaya yaymaq |

Tam əsaslandırma, rəqəmlər və metodologiya qeydi `02_eda.ipynb`-in son bölməsindədir.

## 🚀 Layihəni UV ilə işə salmaq

Bu layihə asılılıqları idarə etmək üçün [uv](https://docs.astral.sh/uv/) istifadə edir (`pyproject.toml` + `uv.lock`).

```bash
# 1. Repo-nu klonla
git clone https://github.com/rashidmajidov/fif_project.git
cd fif_project

# 2. uv quraşdırılmayıbsa (bir dəfəlik)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Asılılıqları quraşdır (uv.lock-a əsasən, .venv avtomatik yaranır)
uv sync

# 4a. Notebook-ları Jupyter-də açmaq üçün
uv run jupyter lab
# sonra notebooks/01_data_cleaning.ipynb → notebooks/02_eda.ipynb ardıcıllığı ilə işə sal

# 4b. Əsas skripti işə salmaq üçün (əgər main.py bütün pipeline-ı çağırırsa)
uv run python main.py
```

> **Qeyd:** `data/raw/Turan_oyun günü sorğusu.xlsx` faylı mövcud olmalıdır ki, `01_data_cleaning.ipynb` işə düşsün. Notebook-lar ardıcıl işlədilməlidir, çünki `02_eda.ipynb` `01_data_cleaning.ipynb`-in çıxardığı `cleaned_survey_data.csv` faylını oxuyur.
