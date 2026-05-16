"""
stock_agent.py — Stock journal and physical stock voucher entry in Tally
Handles intra-godown transfers and stock adjustment entries.
"""

from modules.tally_connector import send_to_tally


def xml_stock_journal(date: str, item: str, qty: float,
                      from_godown: str, to_godown: str, rate: float) -> str:
    """
    Build XML for a stock journal (transfer between godowns).
    
    Args:
        date: Date in YYYYMMDD format
        item: Stock item name (must match Tally exactly)
        qty: Quantity to transfer
        from_godown: Source godown name
        to_godown: Destination godown name
        rate: Rate per unit
    """
    amt = round(qty * rate, 2)
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="Stock Journal" ACTION="Create">
<DATE>{date}</DATE>
<VOUCHERTYPENAME>Stock Journal</VOUCHERTYPENAME>
<ALLINVENTORYENTRIES.LIST>
  <STOCKITEMNAME>{item}</STOCKITEMNAME>
  <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
  <GODOWNNAME>{from_godown}</GODOWNNAME>
  <ACTUALQTY>{qty}</ACTUALQTY>
  <BILLEDQTY>{qty}</BILLEDQTY>
  <RATE>{rate}</RATE>
  <AMOUNT>{amt}</AMOUNT>
</ALLINVENTORYENTRIES.LIST>
<ALLINVENTORYENTRIES.LIST>
  <STOCKITEMNAME>{item}</STOCKITEMNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <GODOWNNAME>{to_godown}</GODOWNNAME>
  <ACTUALQTY>{qty}</ACTUALQTY>
  <BILLEDQTY>{qty}</BILLEDQTY>
  <RATE>{rate}</RATE>
  <AMOUNT>-{amt}</AMOUNT>
</ALLINVENTORYENTRIES.LIST>
</VOUCHER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def xml_physical_stock(date: str, item: str, qty: float,
                       godown: str, rate: float) -> str:
    """
    Build XML for a physical stock voucher (stock count adjustment).
    Used to update Tally with actual physical stock on hand.
    """
    amt = round(qty * rate, 2)
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<VOUCHER VCHTYPE="Physical Stock" ACTION="Create">
<DATE>{date}</DATE>
<VOUCHERTYPENAME>Physical Stock</VOUCHERTYPENAME>
<ALLINVENTORYENTRIES.LIST>
  <STOCKITEMNAME>{item}</STOCKITEMNAME>
  <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
  <GODOWNNAME>{godown}</GODOWNNAME>
  <ACTUALQTY>{qty}</ACTUALQTY>
  <BILLEDQTY>{qty}</BILLEDQTY>
  <RATE>{rate}</RATE>
  <AMOUNT>-{amt}</AMOUNT>
</ALLINVENTORYENTRIES.LIST>
</VOUCHER>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def xml_create_stock_item(name: str, unit: str = "Nos", gst_rate: float = 18.0,
                           hsn: str = "") -> str:
    """Build XML to create a stock item master in Tally."""
    hsn_tag = f"<HSNCODE>{hsn}</HSNCODE>" if hsn else ""
    return f"""<ENVELOPE>
<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
<BODY><IMPORTDATA>
<REQUESTDESC><REPORTNAME>All Masters</REPORTNAME></REQUESTDESC>
<REQUESTDATA><TALLYMESSAGE xmlns:UDF="TallyUDF">
<STOCKITEM NAME="{name}" ACTION="Create">
<NAME>{name}</NAME>
<BASEUNITS>{unit}</BASEUNITS>
<TAXCLASSIFICATIONNAME>GST@{int(gst_rate)}%</TAXCLASSIFICATIONNAME>
{hsn_tag}
</STOCKITEM>
</TALLYMESSAGE></REQUESTDATA>
</IMPORTDATA></BODY>
</ENVELOPE>"""


def create_stock_journal(date: str, item: str, qty: float,
                          from_godown: str, to_godown: str, rate: float) -> dict:
    """Post a stock transfer journal to Tally."""
    try:
        if qty <= 0 or rate < 0:
            return {"success": False, "message": "Quantity must be positive; rate cannot be negative", "data": {}}
        xml = xml_stock_journal(date, item, round(qty, 3), from_godown, to_godown, round(rate, 2))
        result = send_to_tally(xml)
        return {
            "success": result["success"],
            "message": f"Stock transferred: {qty} x {item} from {from_godown} to {to_godown}" if result["success"] else result["error"],
            "data": {"item": item, "qty": qty, "from": from_godown, "to": to_godown, "rate": rate}
        }
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}


def create_physical_stock(date: str, item: str, qty: float,
                           godown: str, rate: float) -> dict:
    """Post a physical stock count voucher to Tally."""
    try:
        if qty < 0:
            return {"success": False, "message": "Quantity cannot be negative", "data": {}}
        xml = xml_physical_stock(date, item, round(qty, 3), godown, round(rate, 2))
        result = send_to_tally(xml)
        return {
            "success": result["success"],
            "message": f"Physical stock updated: {qty} x {item} in {godown}" if result["success"] else result["error"],
            "data": {"item": item, "qty": qty, "godown": godown, "rate": rate}
        }
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}


def create_stock_item(name: str, unit: str = "Nos",
                       gst_rate: float = 18.0, hsn: str = "") -> dict:
    """Create a new stock item master in Tally."""
    try:
        if not name.strip():
            return {"success": False, "message": "Stock item name cannot be empty", "data": {}}
        xml = xml_create_stock_item(name.strip(), unit, gst_rate, hsn)
        result = send_to_tally(xml)
        return {
            "success": result["success"],
            "message": f"Stock item '{name}' created ({unit}, GST {gst_rate}%)" if result["success"] else result["error"],
            "data": {"name": name, "unit": unit, "gst_rate": gst_rate, "hsn": hsn}
        }
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "data": {}}
