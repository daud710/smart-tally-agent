"""
gstr1_generator.py — Generate GSTR-1 JSON for GST portal upload
Produces a standard GSTR-1 JSON file with B2B and B2C sections.
"""

import json
import os
from datetime import datetime


def generate_gstr1_json(sales_data: list, gstin: str, period: str) -> dict:
    """
    Generate a GSTR-1 JSON file from sales transaction data.
    
    Args:
        sales_data: list of sale dicts:
            {
              "invoice_no": str,
              "date": str (YYYYMMDD),
              "party_name": str,
              "party_gstin": str (empty for B2C),
              "taxable": float,
              "cgst": float,
              "sgst": float,
              "igst": float,
              "gst_rate": float,
              "total": float
            }
        gstin:  Company GSTIN (15 chars)
        period: Filing period, e.g. "032024" (MMYYYY)
    
    Returns:
        {"success": True, "file": str, "summary": dict}
    """
    try:
        gstr1 = {
            "gstin":  gstin,
            "fp":     period,
            "gt":     round(sum(s["total"] for s in sales_data), 2),
            "cur_gt": round(sum(s["total"] for s in sales_data), 2),
            "b2b":    [],
            "b2cs":   [],
            "nil":    {"inv": []},
        }

        # Group B2B (GST registered parties) by GSTIN
        b2b_map: dict = {}
        for sale in sales_data:
            party_gstin = sale.get("party_gstin", "").strip()
            if party_gstin and len(party_gstin) == 15:
                if party_gstin not in b2b_map:
                    b2b_map[party_gstin] = []
                b2b_map[party_gstin].append({
                    "inum": sale.get("invoice_no", ""),
                    "idt":  _format_gst_date(sale.get("date", "")),
                    "val":  round(sale.get("total", 0), 2),
                    "pos":  gstin[:2],
                    "rchrg": "N",
                    "itms": [{
                        "num": 1,
                        "itm_det": {
                            "txval": round(sale.get("taxable", 0), 2),
                            "rt":    sale.get("gst_rate", 18),
                            "camt":  round(sale.get("cgst", 0), 2),
                            "samt":  round(sale.get("sgst", 0), 2),
                            "iamt":  round(sale.get("igst", 0), 2),
                            "csamt": 0
                        }
                    }]
                })

        for ctin, invoices in b2b_map.items():
            gstr1["b2b"].append({"ctin": ctin, "inv": invoices})

        # B2C (unregistered parties)
        b2c_sales = [s for s in sales_data
                     if not s.get("party_gstin", "").strip() or len(s.get("party_gstin", "")) != 15]
        if b2c_sales:
            gstr1["b2cs"].append({
                "sply_tp": "INTRA",
                "pos":     gstin[:2],
                "typ":     "OE",
                "txval":   round(sum(s.get("taxable", 0) for s in b2c_sales), 2),
                "rt":      18,
                "camt":    round(sum(s.get("cgst", 0) for s in b2c_sales), 2),
                "samt":    round(sum(s.get("sgst", 0) for s in b2c_sales), 2),
                "csamt":   0
            })

        # Save JSON file
        filename = f"GSTR1_{gstin}_{period}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(gstr1, f, indent=2, ensure_ascii=False)

        summary = {
            "total_invoices": len(sales_data),
            "b2b_invoices":   sum(len(b["inv"]) for b in gstr1["b2b"]),
            "b2c_supplies":   len(b2c_sales),
            "total_taxable":  round(sum(s.get("taxable", 0) for s in sales_data), 2),
            "total_tax":      round(sum(s.get("cgst", 0) + s.get("sgst", 0) + s.get("igst", 0) for s in sales_data), 2),
            "grand_total":    round(sum(s.get("total", 0) for s in sales_data), 2),
        }

        return {"success": True, "file": filename, "summary": summary}

    except Exception as e:
        return {"success": False, "error": f"GSTR-1 generation failed: {str(e)}"}


def _format_gst_date(date_str: str) -> str:
    """Convert YYYYMMDD to DD-MM-YYYY for GSTR-1 format."""
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        return dt.strftime("%d-%m-%Y")
    except Exception:
        return date_str
