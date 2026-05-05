const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    ignoreHTTPSErrors: true
  });
  
  try {
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    });
    const page = await context.newPage();

    page.on('request', request => {
      const url = request.url();
      if (url.includes('algolia')) {
        const headers = request.headers();
        console.log('=== ALGOLIA TROUVÉ ===');
        console.log('URL:', url);
        console.log('App-Id:', headers['x-algolia-application-id']);
        console.log('API-Key:', headers['x-algolia-api-key']);
      }
    });

    page.on('requestfinished', async request => {
      const url = request.url();
      if (url.includes('algolia')) {
        try {
          const body = request.postData();
          if (body) console.log('POST Body:', body.substring(0, 500));
        } catch(e) {}
      }
    });

    console.log('Navigation vers studentjob.fr...');
    await page.goto('https://www.studentjob.fr/offres-emploi', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });

    await page.waitForTimeout(5000);

    const content = await page.content();
    const algoliaMatches = content.match(/algolia[^"']*["']?\s*[:=]\s*["']([^"']{8,})/gi);
    if (algoliaMatches) {
      console.log('=== Algolia dans HTML ===');
      algoliaMatches.forEach(m => console.log(m));
    }
  } finally {
    await browser.close();
  }
})();
