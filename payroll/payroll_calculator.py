"""
payroll_calculator.py — Salary, PF, ESI, TDS, and Professional Tax calculations
Runs independently of Tally (pure Python).
"""


def calculate_tds(annual_income: float) -> float:
    """
    Calculate TDS (Tax Deducted at Source) on annual income.
    Uses standard income tax slabs for FY 2024-25 (old regime).
    
    Returns annual TDS amount.
    """
    # Standard deduction of Rs. 50,000
    taxable = annual_income - 50_000
    if taxable <= 0:
        return 0.0
    if taxable <= 2_50_000:
        tax = 0.0
    elif taxable <= 5_00_000:
        tax = (taxable - 2_50_000) * 0.05
    elif taxable <= 10_00_000:
        tax = 12_500 + (taxable - 5_00_000) * 0.20
    else:
        tax = 1_12_500 + (taxable - 10_00_000) * 0.30
    # Add 4% health & education cess
    tax = tax * 1.04
    return round(tax, 2)


def calculate_salary(basic: float, hra_pct: float = 40.0, da_pct: float = 10.0) -> dict:
    """
    Calculate complete salary breakdown for an employee.
    
    Args:
        basic: Basic salary amount
        hra_pct: HRA as percentage of basic (default 40%)
        da_pct: DA as percentage of basic (default 10%)
    
    Returns:
        Complete salary breakdown dict with gross, deductions, and net pay.
    """
    hra   = round(basic * hra_pct / 100, 2)
    da    = round(basic * da_pct  / 100, 2)
    gross = round(basic + hra + da, 2)

    # PF: 12% of basic (employee contribution)
    pf = round(basic * 0.12, 2)

    # ESI: 0.75% of gross (employee contribution) — only if gross <= Rs. 21,000
    esi = round(gross * 0.0075, 2) if gross <= 21_000 else 0.0

    # Professional Tax (Karnataka/Maharashtra slab — common default)
    if gross <= 15_000:
        prof_tax = 0.0
    elif gross <= 20_000:
        prof_tax = 150.0
    else:
        prof_tax = 200.0

    # Monthly TDS
    annual_gross = gross * 12
    tds_monthly  = round(calculate_tds(annual_gross) / 12, 2)

    total_deductions = round(pf + esi + prof_tax + tds_monthly, 2)
    net_pay = round(gross - total_deductions, 2)

    return {
        "basic":       basic,
        "hra":         hra,
        "da":          da,
        "gross":       gross,
        "pf":          pf,
        "esi":         esi,
        "prof_tax":    prof_tax,
        "tds":         tds_monthly,
        "total_deductions": total_deductions,
        "net_pay":     net_pay,
        # Employer contributions
        "employer_pf":  round(basic * 0.12, 2),   # 12% of basic
        "employer_esi": round(gross * 0.0325, 2) if gross <= 21_000 else 0.0,  # 3.25% of gross
    }


def calculate_payroll_for_team(employees: list) -> list:
    """
    Calculate payroll for a list of employees.
    
    Args:
        employees: list of {"name": str, "emp_id": str, "dept": str, "basic": float}
    
    Returns:
        list of dicts with complete salary breakdown for each employee.
    """
    results = []
    for emp in employees:
        salary = calculate_salary(emp.get("basic", 0))
        results.append({
            "name":   emp.get("name", ""),
            "emp_id": emp.get("emp_id", ""),
            "dept":   emp.get("dept", ""),
            **salary
        })
    return results


def summarize_payroll(payroll_data: list) -> dict:
    """
    Summarize total payroll figures across all employees.
    """
    total_gross   = sum(e["gross"]    for e in payroll_data)
    total_pf      = sum(e["pf"]       for e in payroll_data)
    total_esi     = sum(e["esi"]      for e in payroll_data)
    total_tds     = sum(e["tds"]      for e in payroll_data)
    total_net     = sum(e["net_pay"]  for e in payroll_data)
    employer_pf   = sum(e["employer_pf"]  for e in payroll_data)
    employer_esi  = sum(e["employer_esi"] for e in payroll_data)

    return {
        "employee_count":   len(payroll_data),
        "total_gross":      round(total_gross,  2),
        "total_pf":         round(total_pf,     2),
        "total_esi":        round(total_esi,    2),
        "total_tds":        round(total_tds,    2),
        "total_net_pay":    round(total_net,    2),
        "total_employer_pf":  round(employer_pf,  2),
        "total_employer_esi": round(employer_esi, 2),
        "total_ctc":        round(total_gross + employer_pf + employer_esi, 2),
    }
