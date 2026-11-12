"""Fictional cases only. Evidence is a demonstration record, never real patient data."""
from datetime import date

def evidence(kind, case_id, text=None):
    return {"id": f"EV-{case_id}-{kind}", "kind": kind, "title": kind.replace('_', ' ').title(),
            "author": "Northstar Health demo team", "date": date.today().isoformat(),
            "system_version": "1.0", "content": text or f"Synthetic {kind.replace('_', ' ')} for this case, system version 1.0. Named owner and governance reviewer must validate scope before release.", "synthetic": True}

def seeds():
    basics = [
        ("GK-001", "Staff policy knowledge assistant", "Operations", "Maya Chen", "Internal", "northstar-assist", False, False, False, False, False, ["oversight"], "Find current hospital operating policies for staff with cited answers. No patient information is processed."),
        ("GK-002", "Patient message drafting", "Patient Experience", "Jordan Lee", "PHI", "care-draft", True, False, True, False, False, ["oversight", "data_flow"], "Draft patient portal replies for nurse review. External vendor processes synthetic patient-context data; humans send every message."),
        ("GK-003", "Clinical note summarization", "Clinical Informatics", "Sam Rivera", "PHI", "care-draft", False, True, True, True, False, ["oversight", "data_flow", "baa", "clinical_validation"], "Summarize visit notes for clinician verification. Vendor questionnaire and terms conflict about secondary training use."),
        ("GK-004", "Research cohort exploration", "Research", "Alex Morgan", "De-identified", "research-studio", False, False, True, False, False, ["oversight"], "Explore a synthetic research cohort. Submit documented de-identification methodology before review."),
        ("GK-005", "Discharge instruction drafting", "Nursing", "Taylor Brooks", "PHI", "care-draft", True, True, True, False, True, ["oversight", "data_flow", "baa", "clinical_validation", "evaluation", "monitoring"], "Draft discharge instructions with clinician sign-off. This case simulates an unavailable tools register until retry."),
        ("GK-006", "Autonomous prescription assistant", "Innovation", "Casey Patel", "PHI", "open-chat", True, True, True, False, False, ["oversight"], "Proposed autonomous prescribing without clinician approval. Outside permitted demo scope.")
    ]
    out=[]
    for cid,title,dept,owner,data,tool,patient,clinical,external,conflict,fault,evs,purpose in basics:
        out.append({"id":cid,"title":title,"department":dept,"owner":owner,"data_class":data,"tool_id":tool,"patient_facing":patient,"clinical":clinical,"external":external,"vendor_conflict":conflict,"simulate_failure":fault,"autonomous_prescribing":cid=="GK-006","purpose":purpose,"system_version":"1.0","evidence":[evidence(k,cid) for k in evs]})
    return out
