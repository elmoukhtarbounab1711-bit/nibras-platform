const puppeteer = require("puppeteer");
(async () => {
  const browser = await puppeteer.launch({ headless: true, args: ["--no-sandbox"] });
  const page = await browser.newPage();
  
  const logs = [];
  const errors = [];
  page.on("console", (msg) => {
    const entry = `[${msg.type()}] ${msg.text()}`;
    logs.push(entry);
    if (msg.type() === "error") errors.push(msg.text());
  });
  page.on("pageerror", (err) => errors.push(`PAGE_ERROR: ${err.message}`));

  try {
    await page.goto("https://nibras-law-platforme.vercel.app/#/library", {
      waitUntil: "networkidle2",
      timeout: 30000,
    });
  } catch (e) {
    logs.push(`NAVIGATION_ERROR: ${e.message}`);
  }

  await new Promise((r) => setTimeout(r, 3000));

  const viewContent = await page.evaluate(() => {
    const view = document.getElementById("view");
    return view ? view.innerHTML.substring(0, 2000) : "NO_VIEW_ELEMENT";
  });

  console.log("=== CONSOLE LOGS ===");
  logs.forEach((l) => console.log(l));
  console.log("\n=== ERRORS ===");
  errors.forEach((e) => console.log(e));
  console.log("\n=== VIEW CONTENT (first 2000 chars) ===");
  console.log(viewContent);

  await browser.close();
})();
