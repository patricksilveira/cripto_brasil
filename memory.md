# Project Memory

This file logs the significant changes, updates, and developments made to the Cripto Brasil project over time.

## 2026-08-31
*   **Data & Dashboard Update (RFB 2026-08-26 / Data up to June 2026):**
    *   Committed new raw dataset `criptoativos_dados_abertos_20260826.xls`.
    *   Created backup of previous CSVs at `saida_csv_archive_20260415/`.
    *   Updated `data_clean.py` with dynamic sheet header detection and processed the dataset into `saida_csv/`.
    *   Updated Tab INTRO in `dashboard.py` with recalculated market statistics (historical volume R$ 2.012T, 12M volume R$ 559.8B, stablecoin share 86.4%, CPFs/CNPJs active counts).

## 2026-04-17
*   **Data & Dashboard Modernization:** 
    *   Updated `data_clean.py` script to automate data ingestion for the latest Receita Federal data (up to April 2026).
    *   Modernized the dashboard's introduction text to reflect the current market dynamics, particularly the institutional and stablecoin-led aspects.
    *   Updated the `README.md` to reflect the latest data update date (2026-04-15).
*   **Project Infrastructure:**
    *   Added a formal project specification (`spec.md`) and initialization script (`init.sh`) to the repository.

## Previous Updates
*   **Visual & Functional Overhaul:**
    *   Implemented a Shadcn-inspired theme for a visual overhaul.
    *   Added new overview charts and fixed chart styling, including a new yearly overview section.
    *   Introduced a USD currency toggle with FX normalization capabilities.
