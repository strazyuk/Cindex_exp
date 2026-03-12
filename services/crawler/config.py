BANGLADESH_ENGLISH_NEWS_SOURCES = {
    "general": {
        "The Daily Star": "https://www.thedailystar.net",
        "Dhaka Tribune": "https://www.dhakatribune.com",
        "Prothom Alo": "https://en.prothomalo.com"
    },
    "crime_sections": {
        "The Daily Star": "https://www.thedailystar.net/crime/rss.xml",
        "Dhaka Tribune": "https://www.dhakatribune.com/bangladesh/crime",
        "Prothom Alo": "https://en.prothomalo.com/bangladesh/crime"
    },
    "selectors": {
        "The Daily Star": {
            "body": ["div.field-items", "div.node-content", "article", "div.pb-20"]
        },
        "Dhaka Tribune": {
            "body": ["div.field-items", "div.node-content", "article div.text-element"]
        },
        "Prothom Alo": {
            "body": ["div.story-element-text-cms-one"]
        }
    }
}
