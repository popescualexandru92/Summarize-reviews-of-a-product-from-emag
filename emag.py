from pyppeteer import launch
import google.generativeai as genai
import asyncio
import config


async def scrape_reviews(url):
    reviews = []
    browser = await launch({"headless": True, "args": ["--window-size=800,800",]})
    page = await browser.newPage()
    await page.setViewport({"width": 800, "height": 2000})
    await page.goto(url)

    # consent google`s policy
    # List of possible button selectors
    button_selectors = [
        'button[aria-label="Refuse all"]',
        'button[aria-label="Respinge tot"]'
    ]
    for selector in button_selectors:
        try:
            await page.waitForSelector(selector, {'timeout': 500})
            await page.click(selector)
            break
        except Exception as e:
            pass

    async def read_reviews():
        await page.waitForSelector('.mrg-btm-xs.js-review-body.review-body-container')
        elements = await page.querySelectorAll('.mrg-btm-xs.js-review-body.review-body-container')
        ids = []
        for element in elements:
            id_value = await page.evaluate('(element) => element.id', element)
            ids.append(id_value)
        for id in ids:
            element = await page.waitForSelector(f'#{id}')
            text = await page.evaluate('(element) => element.textContent', element)
            reviews.append(text)

    await read_reviews()

    i = 2
    while i < 20:
        try:
            next = await page.waitForSelector(f'a[href="#page-{i}"]', {'timeout': 500})
            await next.click()
            await asyncio.sleep(0.5)
            await read_reviews()
            i = i+1
        except Exception as e:
            break

    await browser.close()
    return reviews


def summarize(reviews, model,):
    prompt = "Am colectat cateva recenzii despre un produs. Te rog fa un rezumat in maxim 200 de cuvinte despre parerile cumparatorilor despre produsul respectiv. Recenziile sunt: "
    for review in reviews:
        prompt += "\n"+review
    # print("\n"+prompt+"\n")

    completion = model.generate_content(prompt,)
    return completion


genai.configure(api_key=config.API_KEY)
model = genai.GenerativeModel(
    "gemini-1.5-flash", generation_config=genai.GenerationConfig())


url = input("Enter url: ")

reviews = asyncio.get_event_loop().run_until_complete(scrape_reviews(url))
response = summarize(reviews=reviews, model=model)
print("\n" + "Raspunsul este:" + "\n\n" + response.text)
