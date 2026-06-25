import os
import json
from playwright.sync_api import sync_playwright

def run():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("http://127.0.0.1:8501/")
            page.wait_for_selector(".bejo-card")
            
            report = page.evaluate('''() => {
              const card = document.querySelector('.bejo-card');
              if (!card) return { error: "No se encontró .bejo-card" };
              const cslides = card.querySelector('.cslides');
              const li = cslides.querySelector('li');
              const imgLbl = li.querySelector('.img-lbl');
              const img = imgLbl.querySelector('img');
              const info = li.querySelector('.slide-info');
              const cta = info.querySelector('.slide-cta') || info.querySelector('.slide-cta-agotado');
              
              const getStyles = (el) => {
                if (!el) return null;
                const s = window.getComputedStyle(el);
                return {
                  width: el.offsetWidth,
                  height: el.offsetHeight,
                  display: s.display,
                  position: s.position,
                  maxWidth: s.maxWidth,
                  maxHeight: s.maxHeight,
                  padding: s.padding,
                  margin: s.margin,
                  float: s.float,
                  boxSizing: s.boxSizing
                };
              };
              
              return {
                bejoCard: getStyles(card),
                cslides: getStyles(cslides),
                li: getStyles(li),
                imgLbl: getStyles(imgLbl),
                img: getStyles(img),
                info: getStyles(info),
                cta: getStyles(cta)
              };
            }''')
            
            out_path = r"C:\Users\usuario\Desktop\tienda_accesorios\scratch\computed_styles.json"
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print("SUCCESS")
            print(json.dumps(report, indent=2))
            browser.close()
    except Exception as e:
        print("ERROR:", e)

if __name__ == '__main__':
    run()
