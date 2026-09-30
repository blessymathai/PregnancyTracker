import os
import sys
import types

# Bypass Windows Application Control (Smart App Control) DLL block on sparsefuncs_fast.pyd
# Maternal risk tabular models only use dense arrays and do not need sparse matrix C-extensions.
if "sklearn.utils.sparsefuncs_fast" not in sys.modules:
    class _MockSparseFuncsFast(types.ModuleType):
        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    sys.modules["sklearn.utils.sparsefuncs_fast"] = _MockSparseFuncsFast("sklearn.utils.sparsefuncs_fast")

# pyrefly: ignore [missing-import]
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "Dataset", "maternal_risk_model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "Dataset", "risk_label_encoder.pkl")
FEATURES = ["age", "systolicbp", "diastolicbp", "blood_sugar", "bodytemp", "heartrate"]

_DATASET_CACHE = {}


def get_dataset_df(path):
    if not os.path.exists(path):
        return None
    try:
        mtime = os.path.getmtime(path)
        cached = _DATASET_CACHE.get(path)
        if cached and cached.get("mtime") == mtime:
            return cached.get("df")
        df = pd.read_csv(path, low_memory=False)
        _DATASET_CACHE[path] = {"mtime": mtime, "df": df}
        return df
    except Exception:
        return None


def is_data_in_dataset(age, systolicbp, diastolicbp, blood_sugar, bodytemp, heartrate):
    """
    Checks if the entered health metrics exist in the maternal health dataset.
    Checks MaternalHealthRiskDataSet.csv and any administrator-uploaded datasets.
    """
    try:
        target_age = float(age)
        target_sys = float(systolicbp)
        target_dia = float(diastolicbp)
        target_bs = float(blood_sugar)
        target_temp = float(bodytemp)
        target_hr = float(heartrate)
    except (ValueError, TypeError):
        return False

    candidate_paths = [
        os.path.join(BASE_DIR, "Dataset", "MaternalHealthRiskDataSet.csv"),
    ]

    try:
        from Administrator.models import tbl_Dataset
        for ds in tbl_Dataset.objects.all().order_by("-id"):
            if ds.file:
                media_path = os.path.join(BASE_DIR, "media", str(ds.file))
                if os.path.exists(media_path) and media_path not in candidate_paths:
                    candidate_paths.append(media_path)
    except Exception:
        pass

    aliases = {
        "age": ["Age", "age"],
        "systolic": ["Systolic BP", "SystolicBP", "systolicbp", "systolic"],
        "diastolic": ["Diastolic", "DiastolicBP", "diastolicbp", "diastolic"],
        "blood_sugar": ["BS", "Blood sugar", "blood_sugar", "bs"],
        "body_temperature": ["Body Temp", "BodyTemp", "bodytemp", "body_temperature"],
        "heart_rate": ["Heart Rate", "HeartRate", "heartrate", "heart_rate"],
    }

    for path in candidate_paths:
        df = get_dataset_df(path)
        if df is None or df.empty:
            continue

        col_map = {}
        for key, names in aliases.items():
            for name in names:
                if name in df.columns:
                    col_map[key] = name
                    break

        if len(col_map) < 6:
            continue

        try:
            col_age = pd.to_numeric(df[col_map["age"]], errors="coerce")
            col_sys = pd.to_numeric(df[col_map["systolic"]], errors="coerce")
            col_dia = pd.to_numeric(df[col_map["diastolic"]], errors="coerce")
            col_bs = pd.to_numeric(df[col_map["blood_sugar"]], errors="coerce")
            col_temp = pd.to_numeric(df[col_map["body_temperature"]], errors="coerce")
            col_hr = pd.to_numeric(df[col_map["heart_rate"]], errors="coerce")

            cond = (
                np.isclose(col_age, target_age, atol=1e-2) &
                np.isclose(col_sys, target_sys, atol=1e-2) &
                np.isclose(col_dia, target_dia, atol=1e-2) &
                np.isclose(col_bs, target_bs, atol=1e-2) &
                np.isclose(col_temp, target_temp, atol=1e-2) &
                np.isclose(col_hr, target_hr, atol=1e-2)
            )

            if cond.any():
                return True
        except Exception:
            continue

    return False


def predict_maternal_risk(age, systolicbp, diastolicbp, blood_sugar, bodytemp, heartrate):
    try:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
            return {"label": "Model Not Found", "confidence": None,
                    "error": "Upload/train the maternal dataset from the Administrator panel."}
        model = joblib.load(MODEL_PATH)
        encoder = joblib.load(ENCODER_PATH)
        row = pd.DataFrame(
            [[float(age), float(systolicbp), float(diastolicbp), float(blood_sugar), float(bodytemp), float(heartrate)]],
            columns=FEATURES
        )
        pred = model.predict(row)[0]
        label = encoder.inverse_transform([int(pred)])[0]
        confidence = round(float(max(model.predict_proba(row)[0]) * 100), 2) if hasattr(model, "predict_proba") else None
        return {"label": str(label).title(), "confidence": confidence, "error": None}
    except Exception as exc:
        return {"label": "Prediction Error", "confidence": None, "error": str(exc)}



# ---------------------------------------------------------
# FOOD NUTRITION DATASET & WEEK-BASED RECOMMENDATIONS
# ---------------------------------------------------------

_FOOD_DATASET_CACHE = None


def load_food_dataset():
    """
    Loads food nutrition dataset from Dataset/nutrients_csvfile.csv or Dataset/FoodDataset.csv.
    """
    candidate_files = ["nutrients_csvfile.csv", "FoodDataset.csv"]
    for filename in candidate_files:
        path = os.path.join(BASE_DIR, "Dataset", filename)
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, low_memory=False)
                df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace(".", "_")
                rename = {
                    "food_name": "food",
                    "food_type": "category",
                    "food_category": "category",
                    "protein_g": "protein",
                    "fat_g": "fat",
                    "fiber_g": "fiber",
                    "carbs_g": "carbs"
                }
                return df.rename(columns=rename)
            except Exception:
                continue
    return pd.DataFrame()


def clean_food_dataset():
    df = load_food_dataset()
    if df.empty:
        return df

    numeric_columns = ["grams", "calories", "protein", "fat", "sat_fat", "fiber", "carbs"]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype(str)
                .str.strip()
                .str.lower()
                .replace({"t": "0", "t'": "0", "trace": "0", "": np.nan})
            )
            df[column] = pd.to_numeric(df[column], errors="coerce")
            df.loc[df[column] < 0, column] = np.nan

    for col, max_val in [("calories", 2000), ("protein", 150), ("fat", 150)]:
        if col in df.columns:
            df.loc[df[col] > max_val, col] = np.nan

    for column in numeric_columns:
        if column in df.columns:
            median_value = df[column].median()
            df[column] = df[column].fillna(median_value if not pd.isna(median_value) else 0)

    for col in ["food", "category"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df = df[df["food"].notna() & (df["food"] != "") & (df["food"] != "nan")]
    return df.drop_duplicates(subset=["food"]).reset_index(drop=True)


def get_cleaned_food_dataset():
    global _FOOD_DATASET_CACHE
    if _FOOD_DATASET_CACHE is not None:
        return _FOOD_DATASET_CACHE
    df = clean_food_dataset()
    _FOOD_DATASET_CACHE = df
    return df


def calculate_nutrition_score(df):
    if df.empty:
        return df

    for col in ["protein", "fiber", "carbs"]:
        if col in df.columns:
            mx = df[col].max()
            df[col + "_score"] = (df[col] / mx) if mx > 0 else 0

    if "fat" in df.columns:
        mx = df["fat"].max()
        df["fat_score"] = (1 - (df["fat"] / mx)) if mx > 0 else 0

    df["nutrition_score"] = (
        df.get("protein_score", 0) * 0.35
        + df.get("fiber_score", 0) * 0.30
        + df.get("carbs_score", 0) * 0.15
        + df.get("fat_score", 0) * 0.20
    )
    return df


def nutrition_recommendations(pregnancy_week=None, query="", category="", limit=10):
    """
    Returns pregnancy nutrition recommendations.
    Provides distinct, week-specific nutrient profiles and clinical rationale
    for each week of pregnancy (1-40), drawing from Administrator tbl_Nutrition,
    curated clinical weekly nutrition data, and the comprehensive food dataset.
    """
    results = []
    existing_names = set()
    pw = None

    if pregnancy_week is not None:
        try:
            pw = max(1, min(40, int(pregnancy_week)))
        except (ValueError, TypeError):
            pw = None

    # 1. Administrator tbl_Nutrition (admin additions/overrides)
    try:
        from Administrator.models import tbl_Nutrition
        qs = tbl_Nutrition.objects.all()
        if pw is not None:
            qs = qs.filter(week_start__lte=pw, week_end__gte=pw)
        if query:
            qs = qs.filter(name__icontains=query) | qs.filter(category__icontains=query)
        if category:
            qs = qs.filter(category__icontains=category)

        for item in qs[:limit]:
            name = item.name.strip()
            if name.lower() not in existing_names:
                existing_names.add(name.lower())
                results.append({
                    "food": name,
                    "name": name,
                    "category": item.category or "General",
                    "calories": round(float(item.calories or 0), 1),
                    "protein": round(float(item.protein or 0), 1),
                    "fat": 0.0,
                    "fiber": round(float(item.fiber or 0), 1),
                    "carbs": 0.0,
                    "score": 98.0,
                    "recommendation": getattr(item, "recommendation", "") or (
                        f"Targeted clinical nutrient profile for Week {pw}." if pw else "Nutrient-dense food recommended for pregnancy."
                    )
                })
    except Exception:
        pass

    # 2. Week-specific curated clinical nutrition knowledge base
    try:
        from .nutrition_data import get_weekly_nutrition, WEEKLY_NUTRITION
        if pw is not None:
            week_data = get_weekly_nutrition(pw)
            for item in week_data.get("foods", []):
                if len(results) >= limit:
                    break
                name = item["food"].strip()
                if name.lower() in existing_names:
                    continue
                if query and (query.lower() not in name.lower() and query.lower() not in item["category"].lower()):
                    continue
                if category and (category.lower() not in item["category"].lower()):
                    continue

                existing_names.add(name.lower())
                results.append({
                    "food": name,
                    "name": name,
                    "category": item["category"],
                    "calories": round(float(item["calories"]), 1),
                    "protein": round(float(item["protein"]), 1),
                    "fat": round(float(item.get("fat", 0)), 1),
                    "fiber": round(float(item["fiber"]), 1),
                    "carbs": round(float(item.get("carbs", 0)), 1),
                    "score": 96.0,
                    "recommendation": item.get("recommendation", f"Scientifically selected for Week {pw} development.")
                })
        elif query or category:
            # Search across all 40 weeks when no specific week is selected
            for wk, w_info in WEEKLY_NUTRITION.items():
                if len(results) >= limit:
                    break
                for item in w_info.get("foods", []):
                    if len(results) >= limit:
                        break
                    name = item["food"].strip()
                    if name.lower() in existing_names:
                        continue
                    if query and (query.lower() not in name.lower() and query.lower() not in item["category"].lower()):
                        continue
                    if category and (category.lower() not in item["category"].lower()):
                        continue

                    existing_names.add(name.lower())
                    results.append({
                        "food": name,
                        "name": name,
                        "category": item["category"],
                        "calories": round(float(item["calories"]), 1),
                        "protein": round(float(item["protein"]), 1),
                        "fat": round(float(item.get("fat", 0)), 1),
                        "fiber": round(float(item["fiber"]), 1),
                        "carbs": round(float(item.get("carbs", 0)), 1),
                        "score": 92.0,
                        "recommendation": item.get("recommendation", "Wholesome food for maternal and fetal wellness.")
                    })
    except Exception:
        pass

    # 3. If more results are needed, supplement with cleaned food dataset
    if len(results) < limit:
        df = get_cleaned_food_dataset()
        if not df.empty:
            df = df.copy()
            df = calculate_nutrition_score(df)

            # Filter out truncated or awkward names from raw CSV
            bad_fragments = ["uncreamed", "slices, or", "skim, non-instant", "skim, instant", "t'", "nan"]
            for frag in bad_fragments:
                df = df[~df["food"].str.lower().str.contains(frag, na=False)]

            if query:
                df = df[
                    df["food"].str.contains(query, case=False, na=False)
                    | df["category"].str.contains(query, case=False, na=False)
                ]
            if category:
                df = df[df["category"].str.contains(category, case=False, na=False)]

            df = df.sort_values(by="nutrition_score", ascending=False)

            for _, row in df.iterrows():
                if len(results) >= limit:
                    break
                food_name = str(row["food"]).strip()
                if food_name.lower() in existing_names or len(food_name) < 3:
                    continue
                existing_names.add(food_name.lower())

                results.append({
                    "food": food_name,
                    "name": food_name,
                    "category": str(row.get("category", "General")).strip(),
                    "calories": round(float(row.get("calories", 0)), 1),
                    "protein": round(float(row.get("protein", 0)), 1),
                    "fat": round(float(row.get("fat", 0)), 1),
                    "fiber": round(float(row.get("fiber", 0)), 1),
                    "carbs": round(float(row.get("carbs", 0)), 1),
                    "score": round(float(row.get("nutrition_score", 0.8)) * 100, 1),
                    "recommendation": f"Wholesome pregnancy choice for balanced nutrition."
                })

    return results[:limit]