import asyncio, json, os, time
from pathlib import Path
from playwright.async_api import async_playwright

DATA=Path("/data")
MAX_PAGES=int(os.getenv("AUDIT_MAX_PAGES","8"))
TIMEOUT=int(os.getenv("AUDIT_TIMEOUT_MS","15000"))

PAYMENT_MARKERS={
 "stripe":["stripe","js.stripe.com","checkout.stripe.com"],
 "paypal":["paypal"],
 "wompi":["wompi"],
 "payu":["payu"],
 "mercadopago":["mercadopago","mercadopago.com"],
 "adyen":["adyen"],
}

async def audit(record):
    url=record["request"]["url"]
    evidence={"url":url,"started_at":time.time(),"pages":[],"findings":[],"providers":[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT)
            text=(await page.locator("body").inner_text())[:50000].lower()
            html=(await page.content()).lower()
            providers=[]
            for name, markers in PAYMENT_MARKERS.items():
                if any(m in text or m in html for m in markers):
                    providers.append(name)
            evidence["providers"]=sorted(set(providers))
            forms=await page.locator("form").count()
            inputs=await page.locator("input").count()
            evidence["pages"].append({"url":page.url,"forms":forms,"inputs":inputs})
            if not providers:
                evidence["findings"].append({
                    "severity":"info",
                    "title":"Pasarela no identificada heurísticamente",
                    "detail":"Requiere revisión manual o configuración específica del gateway."
                })
        except Exception as e:
            evidence["findings"].append({
                "severity":"error",
                "title":"No se pudo inspeccionar el checkout",
                "detail":str(e)[:500]
            })
        finally:
            await browser.close()
    evidence["finished_at"]=time.time()
    record["status"]="completed"
    record["result"]=evidence
    (DATA/f'{record["id"]}.json').write_text(
        json.dumps(record,ensure_ascii=False,indent=2),
        encoding="utf-8"
    )

async def main():
    while True:
        for p in DATA.glob("*.json"):
            try:
                record=json.loads(p.read_text(encoding="utf-8"))
                if record.get("status")=="queued":
                    await audit(record)
            except Exception:
                pass
        await asyncio.sleep(2)

asyncio.run(main())
