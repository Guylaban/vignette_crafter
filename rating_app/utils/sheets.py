import streamlit as st
import requests


def _headers() -> dict:
    key = st.secrets["supabase"]["key"]
    return {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal",
    }


def _url(table: str) -> str:
    base = st.secrets["supabase"]["url"].rstrip("/")
    return f"{base}/rest/v1/{table}"


def append_rating(row: dict):
    resp = requests.post(_url("ratings"), json=row, headers=_headers(), timeout=10)
    resp.raise_for_status()


def get_completed_vignette_ids(rater_id: str) -> set:
    resp = requests.get(
        _url("ratings"),
        params={"rater_id": f"eq.{rater_id}", "select": "vignette_id"},
        headers=_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    return {r["vignette_id"] for r in resp.json()}


def save_demographics(row: dict):
    resp = requests.post(_url("rater_demographics"), json=row, headers=_headers(), timeout=10)
    resp.raise_for_status()


def get_demographics(rater_id: str) -> dict | None:
    resp = requests.get(
        _url("rater_demographics"),
        params={"rater_id": f"eq.{rater_id}", "select": "*", "limit": "1"},
        headers=_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else None
