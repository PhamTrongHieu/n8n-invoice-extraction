"""Generate 3 fictional sample invoices for the invoice extraction demo.

- invoice-1.pdf            : clean PDF, as exported by accounting software (AUD, 10% GST)
- invoice-2.jpg            : phone photo, slightly tilted, uneven lighting (USD)
- invoice-3-scanned.png    : skewed black-and-white scan with noise and a PAID stamp (EUR, 19% VAT)

Every company, address, phone number, tax ID and account number is made up.
Numbers are computed in code, so they always add up: line items -> subtotal -> tax -> total.
"""
import io
import math
import os
import random
import pathlib

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

OUT = pathlib.Path(__file__).parent / "samples"
OUT.mkdir(exist_ok=True)
random.seed(18092026)

DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DEJAVU_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def money(x):
    return f"{x:,.2f}"


def totals(items, tax_rate):
    subtotal = round(sum(i["amount"] for i in items), 2)
    tax = round(subtotal * tax_rate, 2)
    return subtotal, tax, round(subtotal + tax, 2)


# ---------------------------------------------------------------- invoice 1
INV1 = dict(
    vendor="Harbour Supply Co. Pty Ltd",
    address=["Unit 4, 12 Dock Road", "Pyrmont NSW 2009, Australia"],
    extra=["ABN 65 402 118 773 (fictional)", "accounts@harboursupply.example"],
    bill_to=["Lorikeet Dental Studio", "88 Sunrise Parade", "Manly NSW 2095"],
    number="HS-2041",
    date="03 August 2026",
    due="31 August 2026",
    currency="AUD",
    tax_label="GST 10%",
    items=[
        dict(desc="A4 copy paper, box of 5 reams", qty=10, unit=42.00, amount=420.00),
        dict(desc="Toner cartridge TN-450 (black)", qty=4, unit=205.00, amount=820.00),
        dict(desc="Sterile gloves, size M, box of 100", qty=12, unit=18.50, amount=222.00),
        dict(desc="Delivery - metro Sydney", qty=1, unit=35.00, amount=35.00),
    ],
)


def build_pdf(path):
    inv = INV1
    subtotal, tax, total = totals(inv["items"], 0.10)
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    y = h - 25 * mm

    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, y, inv["vendor"])
    c.setFont("Helvetica", 9.5)
    for line in inv["address"] + inv["extra"]:
        y -= 5 * mm
        c.drawString(20 * mm, y, line)

    c.setFont("Helvetica-Bold", 22)
    c.drawRightString(w - 20 * mm, h - 25 * mm, "TAX INVOICE")
    c.setFont("Helvetica", 10)
    c.drawRightString(w - 20 * mm, h - 33 * mm, f"Invoice no: {inv['number']}")
    c.drawRightString(w - 20 * mm, h - 39 * mm, f"Invoice date: {inv['date']}")
    c.drawRightString(w - 20 * mm, h - 45 * mm, f"Due date: {inv['due']}")

    y -= 14 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Bill to")
    c.setFont("Helvetica", 10)
    for line in inv["bill_to"]:
        y -= 5 * mm
        c.drawString(20 * mm, y, line)

    y -= 12 * mm
    c.setFillColorRGB(0.93, 0.94, 0.96)
    c.rect(20 * mm, y - 2 * mm, w - 40 * mm, 8 * mm, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(22 * mm, y, "Description")
    c.drawRightString(w - 88 * mm, y, "Qty")
    c.drawRightString(w - 55 * mm, y, "Unit price")
    c.drawRightString(w - 22 * mm, y, f"Amount ({inv['currency']})")

    c.setFont("Helvetica", 9.5)
    for it in inv["items"]:
        y -= 8 * mm
        c.drawString(22 * mm, y, it["desc"])
        c.drawRightString(w - 88 * mm, y, str(it["qty"]))
        c.drawRightString(w - 55 * mm, y, money(it["unit"]))
        c.drawRightString(w - 22 * mm, y, money(it["amount"]))

    y -= 6 * mm
    c.line(w - 95 * mm, y, w - 20 * mm, y)
    for label, value, bold in [
        ("Subtotal", subtotal, False),
        (inv["tax_label"], tax, False),
        (f"Total due ({inv['currency']})", total, True),
    ]:
        y -= 7 * mm
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 11 if bold else 9.5)
        c.drawRightString(w - 55 * mm, y, label)
        c.drawRightString(w - 22 * mm, y, money(value))

    y -= 16 * mm
    c.setFont("Helvetica", 8.5)
    c.drawString(20 * mm, y, "Payment: Harbour Supply Co. - BSB 000-000 - Account 0000 0000 (fictional details)")
    c.drawString(20 * mm, y - 5 * mm, "Sample document created for the automateowned demo. Not a real invoice.")
    c.showPage()
    c.save()
    return subtotal, tax, total


# ---------------------------------------------------------------- shared image renderer
def render_invoice_image(inv, tax_rate, size=(1240, 1754), scale=1.0):
    """Draw the invoice on a white image; return (image, subtotal, tax, total)."""
    subtotal, tax, total = totals(inv["items"], tax_rate)
    img = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(img)
    f = lambda s, bold=False, mono=False: ImageFont.truetype(
        MONO if mono else (DEJAVU_BOLD if bold else DEJAVU), int(s * scale))

    m = int(70 * scale)
    y = m
    d.text((m, y), inv["vendor"], font=f(34, bold=True), fill="black")
    y += int(48 * scale)
    for line in inv["address"] + inv["extra"]:
        d.text((m, y), line, font=f(20), fill=(40, 40, 40))
        y += int(28 * scale)

    right = size[0] - m
    d.text((right, m), inv["title"], font=f(38, bold=True), fill="black", anchor="ra")
    d.text((right, m + int(58 * scale)), f"Invoice no: {inv['number']}", font=f(21), fill="black", anchor="ra")
    d.text((right, m + int(88 * scale)), f"Date: {inv['date']}", font=f(21), fill="black", anchor="ra")
    d.text((right, m + int(118 * scale)), f"Due: {inv['due']}", font=f(21), fill="black", anchor="ra")

    y += int(30 * scale)
    d.text((m, y), "Bill to", font=f(21, bold=True), fill="black")
    y += int(30 * scale)
    for line in inv["bill_to"]:
        d.text((m, y), line, font=f(21), fill=(30, 30, 30))
        y += int(28 * scale)

    y += int(30 * scale)
    d.rectangle([m, y, right, y + int(40 * scale)], fill=(235, 238, 242))
    d.text((m + int(12 * scale), y + int(9 * scale)), "Description", font=f(20, bold=True), fill="black")
    d.text((right - int(430 * scale), y + int(9 * scale)), "Qty", font=f(20, bold=True), fill="black", anchor="ra")
    d.text((right - int(240 * scale), y + int(9 * scale)), "Unit", font=f(20, bold=True), fill="black", anchor="ra")
    d.text((right - int(12 * scale), y + int(9 * scale)), f"Amount ({inv['currency']})",
           font=f(20, bold=True), fill="black", anchor="ra")
    y += int(52 * scale)

    for it in inv["items"]:
        d.text((m + int(12 * scale), y), it["desc"], font=f(20), fill="black")
        d.text((right - int(430 * scale), y), str(it["qty"]), font=f(20), fill="black", anchor="ra")
        d.text((right - int(240 * scale), y), money(it["unit"]), font=f(20), fill="black", anchor="ra")
        d.text((right - int(12 * scale), y), money(it["amount"]), font=f(20), fill="black", anchor="ra")
        y += int(40 * scale)
        d.line([m, y - int(8 * scale), right, y - int(8 * scale)], fill=(215, 215, 215))

    y += int(20 * scale)
    for label, value, bold in [
        ("Subtotal", subtotal, False),
        (inv["tax_label"], tax, False),
        (f"TOTAL ({inv['currency']})", total, True),
    ]:
        d.text((right - int(240 * scale), y), label, font=f(24 if bold else 20, bold=bold), fill="black", anchor="ra")
        d.text((right - int(12 * scale), y), money(value), font=f(24 if bold else 20, bold=bold),
               fill="black", anchor="ra")
        y += int(40 * scale)

    y += int(30 * scale)
    for line in inv["footer"]:
        d.text((m, y), line, font=f(18), fill=(70, 70, 70))
        y += int(26 * scale)

    return img, subtotal, tax, total


INV2 = dict(
    title="INVOICE",
    vendor="Northbridge Print & Signs LLC",
    address=["1408 W Granville Ave, Suite 6", "Chicago, IL 60660, USA"],
    extra=["EIN 00-0000000 (fictional)", "billing@northbridgeprint.example", "+1 (312) 555-0148"],
    bill_to=["Riverside Family Clinic", "77 Oak Street", "Evanston, IL 60201"],
    number="NB-10457",
    date="Sep 11, 2026",
    due="Oct 11, 2026",
    currency="USD",
    tax_label="Sales tax 8.25%",
    items=[
        dict(desc="Roll-up banner 850x2000mm, full colour", qty=2, unit=139.00, amount=278.00),
        dict(desc="Waiting room poster A2, laminated", qty=15, unit=12.40, amount=186.00),
        dict(desc="Reception counter decal, cut vinyl", qty=1, unit=245.50, amount=245.50),
        dict(desc="Design revision (1 hour)", qty=1, unit=85.00, amount=85.00),
    ],
    footer=[
        "Payment due 30 days from invoice date. Late payments incur 1.5% monthly interest.",
        "Sample document created for the automateowned demo. Not a real invoice.",
    ],
)

INV3 = dict(
    title="RECHNUNG / INVOICE",
    vendor="Bergmann Laborbedarf GmbH",
    address=["Industriestrasse 44", "80939 Munchen, Germany"],
    extra=["USt-IdNr DE000000000 (fictional)", "rechnung@bergmann-labor.example"],
    bill_to=["Praxis Dr. Keller", "Lindenallee 7", "80331 Munchen"],
    number="2026-0847",
    date="24.07.2026",
    due="07.08.2026",
    currency="EUR",
    tax_label="MwSt 19%",
    items=[
        dict(desc="Pipettenspitzen 1000ul, Beutel 500 Stk", qty=6, unit=27.90, amount=167.40),
        dict(desc="Nitrilhandschuhe Gr. L, Karton", qty=8, unit=41.25, amount=330.00),
        dict(desc="Desinfektionsmittel 5 L", qty=3, unit=36.80, amount=110.40),
        dict(desc="Versandkosten", qty=1, unit=14.90, amount=14.90),
    ],
    footer=[
        "Zahlbar innerhalb von 14 Tagen ohne Abzug. / Payable within 14 days.",
        "Sample document created for the automateowned demo. Not a real invoice.",
    ],
)


def build_photo(path):
    """invoice-2.jpg: fake phone photo - slight tilt, uneven light, JPEG compression."""
    img, s, t, tot = render_invoice_image(INV2, 0.0825)
    img = img.rotate(-1.6, resample=Image.BICUBIC, expand=True, fillcolor=(245, 243, 238))

    # uneven light: bright top-left, darker towards bottom-right
    w, h = img.size
    grad = Image.new("L", (w, h))
    gd = ImageDraw.Draw(grad)
    for i in range(0, h, 4):
        shade = int(255 - 55 * (i / h))
        gd.rectangle([0, i, w, i + 4], fill=shade)
    grad = grad.filter(ImageFilter.GaussianBlur(120))
    img = Image.composite(img, Image.new("RGB", (w, h), (30, 30, 30)), grad)

    # desk background around the sheet
    bg = Image.new("RGB", (w + 120, h + 120), (72, 66, 60))
    bg.paste(img, (60, 60))
    bg = bg.filter(ImageFilter.GaussianBlur(0.4))
    bg = bg.resize((int(bg.width * 0.8), int(bg.height * 0.8)), Image.LANCZOS)
    bg.save(path, "JPEG", quality=68)
    return s, t, tot


def build_scan(path):
    """invoice-3-scanned.png: black-and-white skewed scan with noise and a PAID stamp."""
    img, s, t, tot = render_invoice_image(INV3, 0.19)
    d = ImageDraw.Draw(img)

    # rotated PAID stamp
    stamp = Image.new("RGBA", (640, 200), (255, 255, 255, 0))
    sd = ImageDraw.Draw(stamp)
    sd.rounded_rectangle([4, 4, 636, 196], radius=18, outline=(190, 40, 40, 255), width=7)
    sd.text((320, 100), "PAID 05.08.2026", font=ImageFont.truetype(DEJAVU_BOLD, 52), fill=(190, 40, 40, 255), anchor="mm")
    stamp = stamp.rotate(11, resample=Image.BICUBIC, expand=True)
    img.paste(stamp, (470, 980), stamp)

    img = img.convert("L")
    img = img.rotate(-2.4, resample=Image.BICUBIC, expand=True, fillcolor=250)

    # scan noise + slight blur + dark edges
    px = img.load()
    w, h = img.size
    for _ in range(int(w * h * 0.012)):
        x, y = random.randrange(w), random.randrange(h)
        px[x, y] = max(0, min(255, px[x, y] + random.choice([-70, -45, 45, 70])))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    edge = Image.new("L", (w, h), 255)
    ed = ImageDraw.Draw(edge)
    ed.rectangle([0, 0, w - 1, h - 1], outline=120, width=14)
    edge = edge.filter(ImageFilter.GaussianBlur(9))
    img = Image.composite(img, Image.new("L", (w, h), 190), edge.point(lambda v: 255 if v > 200 else v))
    img.convert("RGB").save(path, "PNG", optimize=True)
    return s, t, tot


if __name__ == "__main__":
    r1 = build_pdf(OUT / "invoice-1.pdf")
    r2 = build_photo(OUT / "invoice-2.jpg")
    r3 = build_scan(OUT / "invoice-3-scanned.png")
    for name, (s, t, tot) in zip(["invoice-1.pdf", "invoice-2.jpg", "invoice-3-scanned.png"], [r1, r2, r3]):
        p = OUT / name
        print(f"{name:24} subtotal={s:10,.2f} tax={t:9,.2f} total={tot:10,.2f}  {p.stat().st_size/1024:6.0f} KB")
