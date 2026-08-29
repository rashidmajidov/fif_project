import pandas as pd
import numpy as np
import re

def check_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hər sütunda neçə missing dəyərin olduğunu yoxlayır.
    """
    return df.isnull().sum().to_frame(name='missing_values').sort_values(by='missing_values', ascending=False)

def check_duplicates(df: pd.DataFrame) -> int:
    """
    DataFrame-də neçə təkrarlanan sətrin olduğunu yoxlayır.
    """
    return df.duplicated().sum()

def drop_missing_critical(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()
    df = df.dropna(subset=['Year'])
    return df

def fix_year_dtype(df: pd.DataFrame) -> pd.DataFrame:
    """
    Year sütununu int tipinə çevirir.
    """
    df = df.copy()
    df['Year'] = df['Year'].astype(int)
    return df

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame-dəki təkrarlanan sətrləri silir.
    """
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates()
    print(f"Removed {before - len(df)} duplicate rows.")
    return df

def filter_valid_years(df: pd.DataFrame, min_year: int = 1980, max_year: int = 2023) -> pd.DataFrame:
    """
    Verilən aralıqda olmayan illəri filterləyir.
    """
    df = df.copy()
    df = df[(df['Year'] >= min_year) & (df['Year'] <= max_year)]
    return df



def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bütün təmizləmə addımlarını birləşdirir.
    """
    df = df.copy()
    df = drop_missing_critical(df)
    df = fix_year_dtype(df)
    df = remove_duplicates(df)
    df = filter_valid_years(df)
    return df


# ---------------------------------------------------------------------------
# Rəsmi sponsor adları və onların bilinən yazılış variantlarını tanıyan
# regex şablonları. Yeni bir yazılış forması aşkar olunsa, yalnız bu
# lüğəti genişləndirmək kifayətdir — funksiyalara toxunmaq lazım deyil.
# ---------------------------------------------------------------------------
import re
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Rəsmi sponsor adları və onların bilinən yazılış variantlarını tanıyan
# regex şablonları. Yeni bir yazılış forması aşkar olunsa, yalnız bu
# lüğəti genişləndirmək kifayətdir — funksiyalara toxunmaq lazım deyil.
#
# QEYD: Hər sponsor üçün YALNIZ BİR qayda saxlanılıb (əvvəlki versiyada
# HUNER GROUP üçün 3 dublikat qayda var idi, bu da lazımsız təkrar
# işləmə və qarışıqlığa səbəb olurdu).
# ---------------------------------------------------------------------------
SPONSOR_PATTERNS: list[tuple[str, str]] = [
    (r'(?i)\bh[uü]n[əe]r\s*(q[uıi]?rup|group)?\b|\bhg\b', 'HUNER GROUP'),
    (r'(?i)\bada\s*store\b', 'Ada Store'),
    (r'(?i)\btovuz\s*su(yu)?\b', 'Tovuz Su'),
    (r'(?i)\baz\s*group\b', 'Az Group'),
    (r'(?i)\boyal\b', 'Oyal'),
    (r'(?i)\bb[öo]y[üu]k\s*q[ıi]şlaq\s*su(yu)?(\s*hauder)?\b', 'Böyük Qışlaq Su'),
    (r'(?i)\bkapital\s*bank\s*plakat\b', 'Kapital Bank Plakat'),
    (r'(?i)\btovuz\s*mall\b', 'Tovuz Mall'),
    (r'[fF][iIıİ][fF]\b', 'FİF'),
    (r'(?i)\btanix\b', 'Tanix'),
]

CANONICAL_SPONSORS: list[str] = [replacement for _, replacement in SPONSOR_PATTERNS]
_CANONICAL_LOOKUP = {name.lower(): name for name in CANONICAL_SPONSORS}

_COMPILED_SPONSOR_PATTERNS = [(re.compile(p), r) for p, r in SPONSOR_PATTERNS]

# Sponsor adları arasındakı ayırıcılar: vergül, slash, nöqtə, ;  +  &,
# 'və' sözü, boşluq(lar)
_SPLIT_PATTERN = re.compile(r'[,/;+&.]+|\bv[əe]\b|\s+', re.IGNORECASE)

_NULL_LIKE_TOKENS = {'nan', 'none', '', '0'}

# Çoxsözlü adları qorumaq üçün istifadə olunan görünməz placeholder simvollar
_SPACE_PLACEHOLDER = '\u2423'
_DOT_PLACEHOLDER = '\u2422'


def _is_null_like(text) -> bool:
    """Dəyərin (istənilən tipdə olsa belə) faktiki 'boş' sayılıb-sayılmadığını yoxlayır."""
    if pd.isna(text):
        return True
    return str(text).strip().lower() in _NULL_LIKE_TOKENS


def _standardize_sponsor_text(text: str) -> str:
    """Sponsor adlarındakı yazılış fərqlərini rəsmi ada çevirir."""
    cleaned = text
    for pattern, replacement in _COMPILED_SPONSOR_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned.strip()


def _protect_canonical_names(text: str) -> str:
    """
    Çox sözlü / nöqtəli rəsmi sponsor adlarını müvəqqəti simvollarla
    qoruyur ki, bölmə (split) zamanı öz daxilindəki boşluq/nöqtəyə görə
    yanlışlıqla parçalanmasınlar.
    """
    for name in sorted(CANONICAL_SPONSORS, key=len, reverse=True):
        protected = name.replace(' ', _SPACE_PLACEHOLDER).replace('.', _DOT_PLACEHOLDER)
        text = re.sub(re.escape(name), protected, text, flags=re.IGNORECASE)
    return text


def _unprotect(token: str) -> str:
    return token.replace(_SPACE_PLACEHOLDER, ' ').replace(_DOT_PLACEHOLDER, '.')


def _extract_sponsor_list(text: str) -> list[str]:
    """
    Standartlaşdırılmış mətndən yalnız RƏSMİ 10 sponsordan birinə uyğun
    gələn tokenləri çıxarır, dublikatları təmizləyir və sırasını qoruyaraq
    siyahı qaytarır. Tanınmayan/artıq sözlər (heç bir rəsmi ada uyğun
    gəlməyən mətn parçaları) nəzərə alınmır.
    """
    protected = _protect_canonical_names(text)
    raw_tokens = [t for t in _SPLIT_PATTERN.split(protected) if t.strip()]

    result: list[str] = []
    seen: set[str] = set()
    for tok in raw_tokens:
        candidate = _unprotect(tok).strip()
        canonical = _CANONICAL_LOOKUP.get(candidate.lower())
        if canonical is None:
            continue
        if canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


def clean_sponsor_columns(
    df: pd.DataFrame,
    count_col: str = "Stadionda neçə sponsor reklamı gördünüz?",
    names_col: str = "Bunlar hansılardır?",
) -> pd.DataFrame:
    df = df.copy()

    raw_counts = df[count_col].apply(lambda x: str(x).strip().lower() if pd.notna(x) else '')
    raw_names = df[names_col].apply(lambda x: str(x).strip().lower() if pd.notna(x) else '')

    final_counts = []
    final_names = []

    for count_text, names_text in zip(raw_counts, raw_names):
        if not _is_null_like(names_text) and not re.fullmatch(r'\d+', names_text):
            source_text = names_text
        elif not _is_null_like(count_text) and not re.fullmatch(r'\d+', count_text):
            source_text = count_text
        else:
            source_text = ''

        if _is_null_like(source_text):
            final_counts.append(0)
            final_names.append(np.nan)
            continue

        standardized = _standardize_sponsor_text(source_text)
        sponsors = _extract_sponsor_list(standardized)

        final_counts.append(len(sponsors))
        final_names.append(', '.join(sponsors) if sponsors else np.nan)

    df[count_col] = pd.Series(final_counts, index=df.index).astype(int)
    df[names_col] = pd.Series(final_names, index=df.index)

    return df



# ---------------------------------------------------------------------------
# Rayon/kənd adlarının normallaşdırılması üçün regex şablonları.
# Sponsor adları üçün istifadə olunan eyni məntiq: hər kənd/şəhər üçün
# bilinən yazılış fərqlərini tutan regex, RƏSMİ ada çevrilir.
# SIRA VACİBDİR — spesifik kənd şablonları əvvəldə, ümumi "Tovuz şəhəri"
# fallback-i ən sonda yoxlanılır (əks halda "Tovuz R.N Azaflı kend" kimi
# sətirlər səhvən "Tovuz şəhəri"nə düşərdi).
# ---------------------------------------------------------------------------
REGION_PATTERNS: list[tuple[str, str]] = [
    (r'(?i)d[üu]z\s*[cç][ıi]rdaxan', 'Düz Cırdaxan kəndi'),
    (r'(?i)[əe]srik\s*[cç][ıi]rdaxan|[əe]srik\s*k[əe]nd', 'Əsrik Cırdaxan kəndi'),
    (r'(?i)azafl[ıi]', 'Azaflı kəndi'),
    (r'(?i)[əe]lim[əe]rdanl[ıi]', 'Əlimərdanlı kəndi'),
    (r'(?i)c[əe]lilli', 'Cəlilli kəndi'),
    (r'(?i)qovlar|qovullar', 'Qovlar kəndi'),
    (r'(?i)k[öo]hn[əe]\s*qala', 'Köhnəqala kəndi'),
    (r'(?i)alakol', 'Alakol kəndi'),
    (r'(?i)aşağı\s*qu[şs][çc]u|aşğıqul?şu', 'Aşağı Quşçu kəndi'),
    (r'(?i)\bbak[ıi]\b', 'Bakı şəhəri'),
    (r'(?i)bozalqanl[ıi]|bozaqanl[ıi]|qozaqanl[ıi]', 'Bozalqanlı kəndi'),
    (r'(?i)quzanl[ıi]', 'Quzanlı kəndi'),
    (r'(?i)xat[ıi]nl[ıi]', 'Xatınlı kəndi'),
    # Konkret kənd qeyd olunmayıb, sadəcə Tovuz şəhərinin özü nəzərdə tutulub
    (r'(?i)\btovuz\b|\bşəhər', 'Tovuz şəhəri'),
]

CANONICAL_REGIONS: list[str] = [replacement for _, replacement in REGION_PATTERNS]
_COMPILED_REGION_PATTERNS = [(re.compile(p), r) for p, r in REGION_PATTERNS]


def clean_region_column(
    df: pd.DataFrame,
    col: str = 'Harada yaşayırsınız, oyunu izləməyə haradan gəlmisiniz? rayon/kəndin adını qeyd edin',
) -> pd.DataFrame:
    """
    Rayon/kənd sütunundakı yazılış fərqlərini (Tovuz r, tovuz rayonu,
    Tovuz R.N Azaflı kend, bozaqanlı, Qozaqanlı və s.) rəsmi kənd/şəhər
    adlarına çevirir. Heç bir şablona uyğun gəlməyən dəyərlər olduğu kimi
    saxlanılır və konsola xəbərdarlıq kimi çap olunur ki, əl ilə yoxlanıla
    bilsin (yeni yazılış forması aşkar olunsa, sadəcə REGION_PATTERNS
    lüğətini genişləndirmək kifayətdir).
    """
    df = df.copy()

    def _standardize(value):
        if pd.isna(value):
            return value
        text = str(value).strip()
        if not text:
            return np.nan
        for pattern, canonical in _COMPILED_REGION_PATTERNS:
            if pattern.search(text):
                return canonical
        return text  # tanınmadı — orijinal dəyər saxlanılır

    cleaned = df[col].apply(_standardize)

    unmatched = sorted(set(
        v for v in cleaned.dropna().unique()
        if v not in CANONICAL_REGIONS
    ))
    if unmatched:
        print("Diqqət: aşağıdakı dəyərlər heç bir kənd/şəhər şablonuna uyğun "
              "gəlmədi və olduğu kimi saxlanıldı (əl ilə yoxlayın):")
        for v in unmatched:
            print(f"  - {v}")

    df[col] = cleaned
    return df