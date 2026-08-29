import pandas as pd
from pathlib import Path
from src.config import DATA_RAW, DATA_PROCESSED


def load_raw(filename: str, sep: str = ",", sheet_name=0) -> pd.DataFrame:
    """
    data/raw/ qovluğundan CSV və ya Excel (.xlsx/.xls) faylını oxuyur.
    Fayl uzantısına görə avtomatik düzgün oxuma metodunu seçir.
    """
    filepath = DATA_RAW / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Fayl tapılmadı: {filepath}")

    suffix = filepath.suffix.lower()

    # --- Excel faylları ---
    if suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        print(f"'{filename}' Excel faylı kimi oxundu. Shape: {df.shape}")
        return df

    # --- CSV faylları ---
    encodings_to_try = ["utf-8", "latin-1", "cp1252"]
    for enc in encodings_to_try:
        try:
            df = pd.read_csv(
                filepath,
                encoding=enc,
                sep=sep,
                engine="python",
                on_bad_lines="warn",
            )
            print(f"'{filename}' '{enc}' encoding ilə uğurla oxundu. Shape: {df.shape}")
            return df
        except UnicodeDecodeError:
            continue
        except pd.errors.ParserError as e:
            print(f"Parser xətası ({enc}): {e}")
            continue

    raise ValueError(f"'{filename}' heç bir encoding ilə oxuna bilmədi: {encodings_to_try}")


def save_processed(df: pd.DataFrame, filename: str) -> None:
    """Təmizlənmiş DataFrame-i data/processed/ qovluğuna yazır (Excel və utf-8 uyğun)."""
    filepath = DATA_PROCESSED / filename
    
    # float_format='%.2f' onluq kəsrləri standart formaya salır (məs: 7.50)
    # bu parametr Excel-in rəqəmləri avtomatik Tarixə (07.may) çevirməsinin qarşısını alır
    df.to_csv(
        filepath, 
        index=False, 
        encoding="utf-8-sig", 
        sep=";", 
        float_format="%.2f"
    )
    
    print(f"Fayl saxlanıldı: {filepath} (shape: {df.shape})")

def load_processed(filename: str) -> pd.DataFrame:
    """data/processed/ qovluğundan artıq təmizlənmiş faylı oxuyur."""
    filepath = DATA_PROCESSED / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Fayl tapılmadı: {filepath}")
        
    # Saxlayanda utf-8-sig istifadə edildiyi üçün oxuyanda da utf-8-sig istifadə edirik
    df = pd.read_csv(filepath, encoding="utf-8-sig", sep=";", parse_dates=['Timestamp'])
    print(f"'{filename}' oxundu. Shape: {df.shape}")
    return df