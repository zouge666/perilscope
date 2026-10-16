def data_quality(data):
    files = {}
    for name, report in data.reports.items():
        files[name] = {
            "rows": report.rows,
            "kept": report.kept,
            "excluded": report.excluded,
            "fixed": report.fixed,
        }
    amounts = {reason: round(value, 2) for reason, value in data.excluded_incurred_dkk.items()}
    return {"files": files, "excluded_incurred_dkk": amounts}
