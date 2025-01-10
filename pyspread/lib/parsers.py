try:
    import pycel
    from pycel import excelformula
except ImportError:
    pycel = None


def spreadsheet_formula_to_code(formula: str) -> str:
    """ Converts spreadsheet formula into Python code via pycel """
    if pycel is None:
        return formula

    ex = excelformula.ExcelFormula(formula)
    return ex.python_code
