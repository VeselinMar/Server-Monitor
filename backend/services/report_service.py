import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Brand colours ──
BLUE        = colors.HexColor("#2563eb")
BLUE_LIGHT  = colors.HexColor("#eff6ff")
GREEN       = colors.HexColor("#16a34a")
RED         = colors.HexColor("#ef4444")
RED_LIGHT   = colors.HexColor("#fef2f2")
AMBER       = colors.HexColor("#f59e0b")
AMBER_LIGHT = colors.HexColor("#fffbeb")
LIGHT_GREY  = colors.HexColor("#f5f3ef")
MID_GREY    = colors.HexColor("#e2ddd6")
TEXT        = colors.HexColor("#1a1714")
TEXT_2      = colors.HexColor("#6b6460")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def _styles():
    return {
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=TEXT,
            spaceAfter=4,
            leading=26,
        ),
        "section": ParagraphStyle(
            "section",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=BLUE,
            spaceBefore=14,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=TEXT,
            spaceAfter=4,
            leading=14,
        ),
        "small": ParagraphStyle(
            "small",
            fontName="Helvetica",
            fontSize=8,
            textColor=TEXT_2,
            spaceAfter=2,
            leading=11,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=7.5,
            textColor=TEXT_2,
            alignment=TA_CENTER,
        ),
        "finding": ParagraphStyle(
            "finding",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=TEXT,
            spaceAfter=3,
            leading=14,
            leftIndent=10,
        ),
    }


def _fmt_minutes(minutes: int) -> str:
    if not minutes:
        return "0 min"
    if minutes < 60:
        return f"{minutes} min"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if m else f"{h}h"


def _fmt_speed(val) -> str:
    return f"{val:.1f} Mbps" if val is not None else "—"


def _pct(n, d) -> str:
    if not d:
        return "0%"
    return f"{(n / d * 100):.1f}%"


def _header_table(from_date: date, to_date: date, sub: dict) -> Table:
    """Two-column header: report title left, subscriber details right."""
    s = _styles()
    left = [
        Paragraph("Network Performance", ParagraphStyle(
            "h1", fontName="Helvetica-Bold", fontSize=18,
            textColor=TEXT, leading=22, spaceAfter=2)),
        Paragraph("Complaint Report", ParagraphStyle(
            "h2", fontName="Helvetica-Bold", fontSize=18,
            textColor=BLUE, leading=22, spaceAfter=8)),
        Paragraph(
            f"Reporting period: <b>{from_date.strftime('%d %B %Y')}</b> "
            f"to <b>{to_date.strftime('%d %B %Y')}</b>",
            s["body"]),
        Paragraph(
            f"Submitted to: <b>{sub['provider']}</b>",
            s["body"]),
        Paragraph(
            f"Plan: <b>{sub['plan']}</b>",
            s["body"]),
    ]

    right_data = [
        ["Subscriber Name",   sub["name"]],
        ["Address",           sub["address"]],
        ["Account Number",    sub["account_number"]],
        ["Email",             sub["email"]],
        ["Phone",             sub["phone"]],
        ["Report Date",       date.today().strftime("%d %B %Y")],
    ]
    right_rows = []
    for label, value in right_data:
        right_rows.append([
            Paragraph(f'<font size="7.5" color="#6b6460">{label}</font>', s["body"]),
            Paragraph(f'<font size="8"><b>{value}</b></font>', s["body"]),
        ])

    right_inner = Table(right_rows, colWidths=[34*mm, 56*mm])
    right_inner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_GREY),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, MID_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))

    outer = Table([[left, right_inner]],
                  colWidths=[PAGE_W - 2*MARGIN - 95*mm, 95*mm])
    outer.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return outer


def _findings_box(findings: list) -> Table:
    """Highlighted blue box listing key findings as bullet points."""
    s = _styles()
    if not findings:
        findings = ["No significant findings for this period."]
    rows = [[Paragraph(f"&#x2022;  {f}", s["finding"])] for f in findings]
    t = Table(rows, colWidths=[PAGE_W - 2*MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BLUE_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 1, BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    return t


def _stat_table(stats: list) -> Table:
    """Row of stat boxes: (label, value, sub)."""
    s = _styles()
    data = [[
        Paragraph(
            f'<font size="7.5" color="#6b6460">{label}</font><br/>'
            f'<font size="16"><b>{value}</b></font><br/>'
            f'<font size="7.5" color="#6b6460">{sub}</font>',
            s["body"])
        for label, value, sub in stats
    ]]
    col_w = (PAGE_W - 2*MARGIN) / len(stats)
    t = Table(data, colWidths=[col_w] * len(stats))
    t.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, MID_GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, MID_GREY),
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _data_table(headers: list, rows: list, col_widths: list,
                highlight_fn=None) -> Table:
    """
    Styled data table with optional per-row colour highlighting.
    highlight_fn(row_index, row_data) -> color | None
    """
    s = _styles()
    header_row = [
        Paragraph(f'<font size="8"><b>{h}</b></font>', s["body"])
        for h in headers
    ]
    data_rows = [
        [Paragraph(f'<font size="8">{cell}</font>', s["body"]) for cell in row]
        for row in rows
    ]

    t = Table([header_row] + data_rows, colWidths=col_widths)

    style_cmds = [
        ("BACKGROUND",     (0, 0), (-1, 0),  BLUE),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("GRID",           (0, 0), (-1, -1), 0.4, MID_GREY),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]

    if highlight_fn:
        for i, row in enumerate(rows):
            c = highlight_fn(i, row)
            if c:
                style_cmds.append(("BACKGROUND", (0, i+1), (-1, i+1), c))

    t.setStyle(TableStyle(style_cmds))
    return t


def generate_report(
    from_date: date,
    to_date: date,
    summaries: list,
    incidents: list,
    settings: dict,
) -> bytes:
    """
    Generate a PDF network health complaint report for the given date range.

    Subscriber details and thresholds are read from the settings dict,
    which is fetched from the database at request time so changes made
    via the UI are reflected immediately without restarting the server.
    """
    # Build subscriber dict from settings
    sub = {
        "name":           settings.get("subscriber_name", ""),
        "address":        settings.get("subscriber_address", ""),
        "account_number": settings.get("subscriber_account_number", ""),
        "email":          settings.get("subscriber_email", ""),
        "phone":          settings.get("subscriber_phone", ""),
        "plan":           settings.get("subscriber_plan", ""),
        "provider":       settings.get("subscriber_provider", ""),
    }

    # Read guaranteed minimum from settings
    download_guarantee = float(settings.get("download_degraded_mbps", "75.0"))
    contracted_dl      = float(settings.get("contracted_download_mbps", "150.0"))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=f"Network Performance Complaint Report {from_date} to {to_date}",
        author=sub["name"],
        subject=f"ISP Service Level Complaint — {sub['provider']}",
    )

    s = _styles()
    story = []

    # ── Header ──
    story.append(_header_table(from_date, to_date, sub))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=10))

    # ── Pre-compute key statistics ──
    total_outage_mins = sum(s_.outage_total_minutes or 0 for s_ in summaries)
    total_outages     = sum(s_.outage_count or 0 for s_ in summaries)
    total_failed      = sum(s_.failed_tests or 0 for s_ in summaries)
    total_tests       = sum(s_.total_tests or 0 for s_ in summaries)
    days_covered      = len(summaries)
    valid_dl          = [s_.avg_download_mbps for s_ in summaries if s_.avg_download_mbps]
    avg_dl            = sum(valid_dl) / len(valid_dl) if valid_dl else None
    below_guarantee   = sum(
        1 for s_ in summaries
        if s_.avg_download_mbps and s_.avg_download_mbps < download_guarantee
    )
    all_mins  = [s_.min_download_mbps for s_ in summaries if s_.min_download_mbps]
    worst_dl  = min(all_mins) if all_mins else None
    worst_day = min(
        (s_ for s_ in summaries if s_.min_download_mbps),
        key=lambda x: x.min_download_mbps,
        default=None,
    )

    # ── Complaint statement ──
    story.append(Paragraph("Formal Complaint Statement", s["section"]))
    story.append(Paragraph(
        f"I, <b>{sub['name']}</b>, a subscriber to the <b>{sub['plan']}</b> "
        f"plan with account number <b>{sub['account_number']}</b>, hereby formally "
        f"submit this complaint regarding repeated and sustained failures to meet the "
        f"contracted service level during the period from "
        f"<b>{from_date.strftime('%d %B %Y')}</b> to "
        f"<b>{to_date.strftime('%d %B %Y')}</b>.",
        s["body"],
    ))
    story.append(Paragraph(
        "The following data was collected by automated monitoring software running "
        "continuously on the subscriber's premises. Speedtests were conducted using "
        "the official Speedtest CLI at regular intervals, and connectivity was verified "
        "every 20 minutes via ICMP ping to 8.8.8.8. All timestamps are local time (CET/CEST).",
        s["body"],
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"<b>Contractual basis:</b> Under the {sub['plan']} plan, {sub['provider']} "
        f"guarantees a minimum download speed of <b>{download_guarantee:.0f} Mbps</b> "
        f"(50% of the advertised {contracted_dl:.0f} Mbps maximum). "
        f"The data below demonstrates that this guarantee was breached "
        f"on <b>{below_guarantee} of {days_covered} monitored days</b> "
        f"({_pct(below_guarantee, days_covered)} of the reporting period).",
        s["body"],
    ))
    story.append(Spacer(1, 6))

    # ── Key findings ──
    findings = []
    if avg_dl:
        if avg_dl < download_guarantee:
            findings.append(
                f"Average download speed was <b>{avg_dl:.1f} Mbps</b> — "
                f"{(download_guarantee - avg_dl) / download_guarantee * 100:.1f}% "
                f"below the guaranteed minimum of {download_guarantee:.0f} Mbps."
            )
        else:
            findings.append(
                f"Average download speed was <b>{avg_dl:.1f} Mbps</b> across "
                f"{days_covered} monitored days, though significant variation occurred."
            )
    if worst_dl and worst_day:
        findings.append(
            f"Worst recorded day: <b>{worst_dl:.1f} Mbps</b> minimum download on "
            f"<b>{str(worst_day.period_date)}</b> — "
            f"only {worst_dl / contracted_dl * 100:.1f}% of the contracted "
            f"{contracted_dl:.0f} Mbps speed."
        )
    if total_outages:
        findings.append(
            f"<b>{total_outages} distinct outage event{'s' if total_outages != 1 else ''}</b> "
            f"recorded, totalling <b>{_fmt_minutes(total_outage_mins)}</b> of complete "
            f"loss of service."
        )
    if below_guarantee:
        findings.append(
            f"The contracted {download_guarantee:.0f} Mbps minimum was not met on "
            f"<b>{below_guarantee} of {days_covered} days</b> "
            f"({_pct(below_guarantee, days_covered)} of the reporting period)."
        )
    if total_failed:
        findings.append(
            f"<b>{total_failed} speedtest{'s' if total_failed != 1 else ''} failed</b> "
            f"to complete ({_pct(total_failed, total_tests)} of {total_tests} attempts), "
            f"consistent with periods of total service unavailability."
        )

    story.append(Paragraph("Key Findings", s["section"]))
    story.append(_findings_box(findings))
    story.append(Spacer(1, 8))

    # ── Summary stat boxes ──
    story.append(Paragraph("Summary Statistics", s["section"]))
    _stats = [
        ("Total Outage Time",
         _fmt_minutes(total_outage_mins),
         f"{total_outages} distinct event{'s' if total_outages != 1 else ''}"),
        ("Period Avg Download",
         f"{avg_dl:.1f} Mbps" if avg_dl else "—",
         f"vs {download_guarantee:.0f} Mbps guaranteed min"),
        ("Worst Day Download",
         f"{worst_dl:.1f} Mbps" if worst_dl else "—",
         str(worst_day.period_date) if worst_day else "—"),
        ("Days Below Guarantee",
         str(below_guarantee),
         f"of {days_covered} days · {_pct(below_guarantee, days_covered)}"),
        ("Failed Speedtests",
         str(total_failed),
         f"of {total_tests} total · {_pct(total_failed, total_tests)}"),
    ]
    if _stats:
        story.append(_stat_table(_stats))
    story.append(Spacer(1, 8))

    # ── Incident log ──
    if incidents:
        story.append(Paragraph("Incident Log", s["section"]))
        story.append(Paragraph(
            "Consecutive periods of outage, degraded performance, or speedtest failure. "
            "Red rows indicate complete loss of service. Amber rows indicate degraded performance.",
            s["small"],
        ))
        story.append(Spacer(1, 4))

        TYPE_LABELS = {
            "FAILURE":     "Test Failed",
            "CRITICAL":    "Critical",
            "DEGRADED":    "Degraded",
            "NO INTERNET": "No Internet",
        }
        TYPE_SEVERITY = {
            "NO INTERNET": RED_LIGHT,
            "CRITICAL":    RED_LIGHT,
            "DEGRADED":    AMBER_LIGHT,
            "FAILURE":     AMBER_LIGHT,
        }

        inc_rows  = []
        inc_types = []
        for inc in sorted(incidents, key=lambda x: x["start"]):
            inc_rows.append([
                TYPE_LABELS.get(inc["type"], inc["type"]),
                str(inc["start"])[:16],
                str(inc["end"])[:16],
                _fmt_minutes(inc["duration_minutes"]),
                _fmt_speed(inc.get("avg_download_mbps")),
                _fmt_speed(inc.get("avg_upload_mbps")),
                str(inc["sample_count"]),
            ])
            inc_types.append(inc["type"])

        def inc_highlight(i, row):
            return TYPE_SEVERITY.get(inc_types[i])

        cw = PAGE_W - 2*MARGIN
        story.append(KeepTogether([
            _data_table(
                ["Type", "Start", "End", "Duration",
                 "Avg Down", "Avg Up", "Samples"],
                inc_rows,
                [cw*0.14, cw*0.18, cw*0.18, cw*0.12,
                 cw*0.13, cw*0.13, cw*0.12],
                highlight_fn=inc_highlight,
            )
        ]))
        story.append(Spacer(1, 8))

    # ── Daily performance log ──
    if summaries:
        story.append(Paragraph("Daily Performance Log", s["section"]))
        story.append(Paragraph(
            f"Days marked with * had an average download below the contracted "
            f"{download_guarantee:.0f} Mbps minimum and are highlighted in red.",
            s["small"],
        ))
        story.append(Spacer(1, 4))

        sorted_summaries = sorted(summaries, key=lambda x: x.period_date)
        daily_rows  = []
        below_flags = []

        for s_ in sorted_summaries:
            below = bool(s_.avg_download_mbps and s_.avg_download_mbps < download_guarantee)
            below_flags.append(below)
            avg_dl_str = (
                f"{s_.avg_download_mbps:.1f} *" if below
                else f"{s_.avg_download_mbps:.1f}"
            ) if s_.avg_download_mbps else "—"

            daily_rows.append([
                str(s_.period_date),
                avg_dl_str,
                f"{s_.min_download_mbps:.1f}" if s_.min_download_mbps else "—",
                f"{s_.avg_upload_mbps:.1f}"   if s_.avg_upload_mbps   else "—",
                f"{s_.avg_ping:.1f}"           if s_.avg_ping          else "—",
                str(s_.successful_tests or 0),
                str(s_.failed_tests or 0),
                str(s_.outage_count or 0),
                _fmt_minutes(s_.outage_total_minutes or 0),
            ])

        def daily_highlight(i, row):
            return RED_LIGHT if below_flags[i] else None

        cw = PAGE_W - 2*MARGIN
        story.append(
            _data_table(
                ["Date", "Avg DL", "Min DL", "Avg UL", "Ping",
                 "OK", "Failed", "Outages", "Outage Time"],
                daily_rows,
                [cw*0.12, cw*0.09, cw*0.09, cw*0.09, cw*0.08,
                 cw*0.07, cw*0.08, cw*0.09, cw*0.29],
                highlight_fn=daily_highlight,
            )
        )

    # ── Footer ──
    story.append(Spacer(1, 14))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=MID_GREY, spaceAfter=5))
    story.append(Paragraph(
        f"This report was generated automatically by ServerMonitor on "
        f"{date.today().strftime('%d %B %Y')}. "
        f"Data was collected via automated speedtest and connectivity monitoring "
        f"software running on the subscriber's premises. "
        f"Raw monitoring logs are available upon request.",
        s["footer"],
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()