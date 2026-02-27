"""
assets/_data.py
Local data layer — handles offline persistence for asset caching.
"""
import os
import re
import json
import sqlite3
from datetime import datetime, timedelta

_DB_PATH = os.path.join(os.path.dirname(__file__), "data.cache")

# ── Sample records ──────────────────────────────────────────────────────────
_SEED = [
    # ── Bloomberg Markets ────────────────────────────────────────────────
    {"video_id":"bm001","title":"Federal Reserve Holds Rates — Wall Street Reacts","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-26T14:30:00Z","view_count":1_420_300,"like_count":18_200,"comment_count":3_410,"duration":612,"description":"The Federal Reserve kept its benchmark rate unchanged. Markets responded with a sharp rally as investors digested the decision and forward guidance.","url":"https://www.youtube.com/watch?v=bm001","thumbnail":"https://i.ytimg.com/vi/bm001/hqdefault.jpg","tags":["fed","rates","wallstreet"],"source":"seed"},
    {"video_id":"bm002","title":"S&P 500 Eyes Record Highs After Jobs Report Beat","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-25T15:00:00Z","view_count":980_100,"like_count":11_050,"comment_count":2_100,"duration":540,"description":"US payrolls added 290,000 jobs in January, smashing forecasts. The S&P 500 surged toward all-time highs in after-hours trading.","url":"https://www.youtube.com/watch?v=bm002","thumbnail":"https://i.ytimg.com/vi/bm002/hqdefault.jpg","tags":["SP500","jobs","economy"],"source":"seed"},
    {"video_id":"bm003","title":"Oil Surges 4% on Middle East Supply Fears","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-24T10:15:00Z","view_count":760_400,"like_count":9_300,"comment_count":1_870,"duration":480,"description":"Crude oil jumped more than 4% as geopolitical tensions in the Middle East raised concerns about global crude supply disruptions.","url":"https://www.youtube.com/watch?v=bm003","thumbnail":"https://i.ytimg.com/vi/bm003/hqdefault.jpg","tags":["oil","commodities","OPEC"],"source":"seed"},
    {"video_id":"bm004","title":"Tesla Stock Falls 8% — What Analysts Are Saying","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-23T18:45:00Z","view_count":2_100_500,"like_count":24_700,"comment_count":6_200,"duration":720,"description":"Tesla shares plunged after weaker-than-expected delivery numbers. Bloomberg analysts break down what it means for EV demand in 2026.","url":"https://www.youtube.com/watch?v=bm004","thumbnail":"https://i.ytimg.com/vi/bm004/hqdefault.jpg","tags":["Tesla","EV","stocks"],"source":"seed"},
    {"video_id":"bm005","title":"Bitcoin Breaks $120,000 — Institutional Buying Surges","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-22T09:00:00Z","view_count":3_400_200,"like_count":45_600,"comment_count":9_800,"duration":660,"description":"Bitcoin crossed the $120,000 mark for the first time as ETF inflows reach record levels and institutional adoption accelerates.","url":"https://www.youtube.com/watch?v=bm005","thumbnail":"https://i.ytimg.com/vi/bm005/hqdefault.jpg","tags":["Bitcoin","crypto","ETF"],"source":"seed"},
    {"video_id":"bm006","title":"Dollar Weakens as Inflation Data Surprises Markets","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-21T13:00:00Z","view_count":640_800,"like_count":7_100,"comment_count":1_300,"duration":420,"description":"CPI came in below expectations for the third straight month, triggering a broad dollar sell-off and lifting risk assets.","url":"https://www.youtube.com/watch?v=bm006","thumbnail":"https://i.ytimg.com/vi/bm006/hqdefault.jpg","tags":["dollar","inflation","CPI"],"source":"seed"},
    {"video_id":"bm007","title":"Europe Markets: DAX Climbs on Germany Recovery Data","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-20T08:30:00Z","view_count":410_200,"like_count":4_800,"comment_count":850,"duration":360,"description":"German manufacturing data beat estimates, sending the DAX to its highest level since 2025 and lifting European equities broadly.","url":"https://www.youtube.com/watch?v=bm007","thumbnail":"https://i.ytimg.com/vi/bm007/hqdefault.jpg","tags":["DAX","Europe","Germany"],"source":"seed"},
    {"video_id":"bm008","title":"Goldman Sachs Q4 Profits Jump 35% on Trading Boom","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-19T16:00:00Z","view_count":870_300,"like_count":10_200,"comment_count":2_400,"duration":590,"description":"Goldman Sachs reported Q4 earnings that crushed estimates, powered by record bond trading revenue and a surge in M&A advisory fees.","url":"https://www.youtube.com/watch?v=bm008","thumbnail":"https://i.ytimg.com/vi/bm008/hqdefault.jpg","tags":["Goldman","banks","earnings"],"source":"seed"},
    {"video_id":"bm009","title":"Nvidia Unveils Next-Gen AI Chip — Share Price Soars","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-18T11:00:00Z","view_count":4_210_000,"like_count":62_000,"comment_count":14_300,"duration":780,"description":"Nvidia's new Blackwell Ultra GPU promises a 3x performance leap over previous gen. Shares hit an all-time high as AI demand shows no signs of slowing.","url":"https://www.youtube.com/watch?v=bm009","thumbnail":"https://i.ytimg.com/vi/bm009/hqdefault.jpg","tags":["Nvidia","AI","semiconductor"],"source":"seed"},
    {"video_id":"bm010","title":"US Treasury Yields Spike — Bond Sell-Off Explained","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-17T14:00:00Z","view_count":530_600,"like_count":6_200,"comment_count":1_100,"duration":450,"description":"10-year Treasury yields approached 5% as bond investors reassessed the path of Fed rate cuts amid resilient economic data.","url":"https://www.youtube.com/watch?v=bm010","thumbnail":"https://i.ytimg.com/vi/bm010/hqdefault.jpg","tags":["bonds","yields","treasury"],"source":"seed"},
    {"video_id":"bm011","title":"Amazon Stock Rises 6% After Cloud Revenue Beats","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-15T20:00:00Z","view_count":1_750_000,"like_count":21_000,"comment_count":4_600,"duration":630,"description":"Amazon Web Services grew 34% year-over-year, far surpassing analyst expectations and pushing Amazon shares to record territory.","url":"https://www.youtube.com/watch?v=bm011","thumbnail":"https://i.ytimg.com/vi/bm011/hqdefault.jpg","tags":["Amazon","AWS","cloud"],"source":"seed"},
    {"video_id":"bm012","title":"Apple Reports iPhone Sales Decline in China Market","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-14T09:30:00Z","view_count":2_300_000,"like_count":28_000,"comment_count":7_100,"duration":700,"description":"Apple's revenues from Greater China dropped 15% amid stiff competition from Huawei. The company maintained overall guidance on strength in services.","url":"https://www.youtube.com/watch?v=bm012","thumbnail":"https://i.ytimg.com/vi/bm012/hqdefault.jpg","tags":["Apple","China","iPhone"],"source":"seed"},
    {"video_id":"bm013","title":"Emerging Markets Rally as Dollar Index Falls","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-12T12:00:00Z","view_count":380_100,"like_count":4_200,"comment_count":780,"duration":390,"description":"A weaker US dollar lifted emerging market currencies and equities, with India and Brazil leading the gains in Asia and Latin America.","url":"https://www.youtube.com/watch?v=bm013","thumbnail":"https://i.ytimg.com/vi/bm013/hqdefault.jpg","tags":["EM","dollar","India","Brazil"],"source":"seed"},
    {"video_id":"bm014","title":"Recession Risk 2026: What the Yield Curve Is Telling Us","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-10T10:00:00Z","view_count":1_200_000,"like_count":14_500,"comment_count":3_800,"duration":840,"description":"Bloomberg economists analyze inverted yield curves and whether a recession is imminent in the US in the second half of 2026.","url":"https://www.youtube.com/watch?v=bm014","thumbnail":"https://i.ytimg.com/vi/bm014/hqdefault.jpg","tags":["recession","yieldcurve","macro"],"source":"seed"},
    {"video_id":"bm015","title":"JPMorgan Warns of Market Correction Risk","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-08T15:30:00Z","view_count":900_000,"like_count":10_800,"comment_count":2_900,"duration":560,"description":"JPMorgan's chief strategist warned that equity valuations are stretched and a 10-15% correction is plausible in the near term.","url":"https://www.youtube.com/watch?v=bm015","thumbnail":"https://i.ytimg.com/vi/bm015/hqdefault.jpg","tags":["JPMorgan","correction","valuations"],"source":"seed"},
    {"video_id":"bm016","title":"Gold Hits New All-Time High Above $3,000/oz","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-06T08:00:00Z","view_count":2_800_000,"like_count":38_000,"comment_count":8_500,"duration":600,"description":"Gold prices breached $3,000 per ounce for the first time ever, driven by central bank buying and geopolitical safe-haven demand.","url":"https://www.youtube.com/watch?v=bm016","thumbnail":"https://i.ytimg.com/vi/bm016/hqdefault.jpg","tags":["gold","commodities","safehaven"],"source":"seed"},
    {"video_id":"bm017","title":"Microsoft Azure Growth Slows — Cloud War Heats Up","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-04T17:00:00Z","view_count":1_100_000,"like_count":13_200,"comment_count":3_100,"duration":650,"description":"Microsoft's Azure revenue growth decelerated to 28% against expectations of 31%, raising concerns that the AI-driven cloud wave may be peaking.","url":"https://www.youtube.com/watch?v=bm017","thumbnail":"https://i.ytimg.com/vi/bm017/hqdefault.jpg","tags":["Microsoft","Azure","cloud"],"source":"seed"},
    {"video_id":"bm018","title":"Natural Gas Prices Plunge on Warm Winter Forecasts","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-02-02T11:00:00Z","view_count":350_000,"like_count":3_800,"comment_count":620,"duration":390,"description":"Natural gas futures dropped 12% as above-average temperatures across North America and Europe reduce heating demand outlook.","url":"https://www.youtube.com/watch?v=bm018","thumbnail":"https://i.ytimg.com/vi/bm018/hqdefault.jpg","tags":["naturalgas","energy","weather"],"source":"seed"},
    {"video_id":"bm019","title":"China GDP Growth Beats at 5.2% — Recovery Confirmed","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-01-30T06:00:00Z","view_count":1_600_000,"like_count":19_000,"comment_count":5_400,"duration":720,"description":"China's official GDP growth came in at 5.2%, beating the government's own 5% target and sending Asian markets higher.","url":"https://www.youtube.com/watch?v=bm019","thumbnail":"https://i.ytimg.com/vi/bm019/hqdefault.jpg","tags":["China","GDP","Asia"],"source":"seed"},
    {"video_id":"bm020","title":"Meta Beats Earnings, Raises Dividend for First Time","channel":"Bloomberg Markets","channel_id":"UCIALMKvObZNtJ6AmdCLP7Lg","upload_date":"2026-01-28T20:30:00Z","view_count":1_900_000,"like_count":22_000,"comment_count":5_600,"duration":670,"description":"Meta Platforms reported stronger-than-forecast Q4 results and surprised investors by initiating its first-ever quarterly dividend.","url":"https://www.youtube.com/watch?v=bm020","thumbnail":"https://i.ytimg.com/vi/bm020/hqdefault.jpg","tags":["Meta","Facebook","dividend"],"source":"seed"},

    # ── ANI News India ───────────────────────────────────────────────────
    {"video_id":"ani001","title":"PM Modi Meets US President at White House — Key Takeaways","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-26T16:00:00Z","view_count":3_800_000,"like_count":52_000,"comment_count":12_400,"duration":540,"description":"Prime Minister Narendra Modi held bilateral talks with the US President at the White House covering trade, defence, and tech cooperation.","url":"https://www.youtube.com/watch?v=ani001","thumbnail":"https://i.ytimg.com/vi/ani001/hqdefault.jpg","tags":["Modi","USA","India","WhiteHouse"],"source":"seed"},
    {"video_id":"ani002","title":"India's GDP Growth Forecast Raised to 7.4% by IMF","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-25T09:30:00Z","view_count":1_200_000,"like_count":18_000,"comment_count":3_900,"duration":480,"description":"The International Monetary Fund raised India's 2026 GDP growth forecast to 7.4%, calling it the world's fastest-growing major economy.","url":"https://www.youtube.com/watch?v=ani002","thumbnail":"https://i.ytimg.com/vi/ani002/hqdefault.jpg","tags":["India","GDP","IMF","economy"],"source":"seed"},
    {"video_id":"ani003","title":"India-Pakistan Border Tensions Rise After Ceasefire Violation","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-24T12:00:00Z","view_count":5_600_000,"like_count":74_000,"comment_count":22_000,"duration":690,"description":"Indian Army reported ceasefire violations along the Line of Control in Jammu and Kashmir, prompting a strong response from defence forces.","url":"https://www.youtube.com/watch?v=ani003","thumbnail":"https://i.ytimg.com/vi/ani003/hqdefault.jpg","tags":["India","Pakistan","LOC","defence"],"source":"seed"},
    {"video_id":"ani004","title":"ISRO Successfully Launches Chandrayaan-4 Mission","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-23T07:00:00Z","view_count":8_200_000,"like_count":120_000,"comment_count":31_000,"duration":780,"description":"India's space agency ISRO successfully launched the Chandrayaan-4 lunar sample return mission from the Satish Dhawan Space Centre.","url":"https://www.youtube.com/watch?v=ani004","thumbnail":"https://i.ytimg.com/vi/ani004/hqdefault.jpg","tags":["ISRO","Chandrayaan","space","India"],"source":"seed"},
    {"video_id":"ani005","title":"Budget 2026: Finance Minister Announces ₹10 Lakh Crore Infrastructure Push","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-22T11:00:00Z","view_count":4_100_000,"like_count":58_000,"comment_count":14_200,"duration":840,"description":"Finance Minister presented the Union Budget for 2026-27 with a record ₹10 lakh crore capital expenditure on roads, railways and ports.","url":"https://www.youtube.com/watch?v=ani005","thumbnail":"https://i.ytimg.com/vi/ani005/hqdefault.jpg","tags":["budget","India","infrastructure","economy"],"source":"seed"},
    {"video_id":"ani006","title":"USA Imposes New Tariffs on Indian Steel, India Warns of Retaliation","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-21T14:30:00Z","view_count":2_700_000,"like_count":35_000,"comment_count":9_800,"duration":600,"description":"The US announced 25% tariffs on Indian steel and aluminium imports. India's trade ministry warned of proportionate retaliatory measures.","url":"https://www.youtube.com/watch?v=ani006","thumbnail":"https://i.ytimg.com/vi/ani006/hqdefault.jpg","tags":["USA","India","tariffs","trade"],"source":"seed"},
    {"video_id":"ani007","title":"Delhi Gets Its First Metro Line Expansion Under Phase 4","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-20T10:00:00Z","view_count":890_000,"like_count":12_000,"comment_count":2_800,"duration":420,"description":"Prime Minister inaugurated the first phase of Delhi Metro's Phase 4 expansion, adding 28 new stations across the capital.","url":"https://www.youtube.com/watch?v=ani007","thumbnail":"https://i.ytimg.com/vi/ani007/hqdefault.jpg","tags":["Delhi","metro","infrastructure","India"],"source":"seed"},
    {"video_id":"ani008","title":"Virat Kohli Announces Test Cricket Retirement","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-19T08:00:00Z","view_count":12_400_000,"like_count":180_000,"comment_count":48_000,"duration":300,"description":"Indian cricket icon Virat Kohli announced his retirement from Test cricket after scoring 9,000+ runs across 120 matches.","url":"https://www.youtube.com/watch?v=ani008","thumbnail":"https://i.ytimg.com/vi/ani008/hqdefault.jpg","tags":["Kohli","cricket","India","retirement"],"source":"seed"},
    {"video_id":"ani009","title":"India Signs $12 Billion Defence Deal with USA for Fighter Jets","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-18T13:00:00Z","view_count":3_200_000,"like_count":44_000,"comment_count":11_600,"duration":660,"description":"India inked a landmark $12 billion agreement with the United States for the procurement of F-35 fighter jets, the biggest defence deal in Indian history.","url":"https://www.youtube.com/watch?v=ani009","thumbnail":"https://i.ytimg.com/vi/ani009/hqdefault.jpg","tags":["India","USA","defence","F35"],"source":"seed"},
    {"video_id":"ani010","title":"Heat Wave Alert: North India Temperatures Cross 46°C","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-17T07:30:00Z","view_count":1_500_000,"like_count":19_000,"comment_count":4_200,"duration":390,"description":"The IMD issued red alerts across northern India as temperatures surged to 46°C, the earliest severe heat wave on record.","url":"https://www.youtube.com/watch?v=ani010","thumbnail":"https://i.ytimg.com/vi/ani010/hqdefault.jpg","tags":["heatwave","India","weather","IMD"],"source":"seed"},
    {"video_id":"ani011","title":"India's Stock Market Hits Record High — Sensex at 95,000","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-15T16:00:00Z","view_count":2_100_000,"like_count":29_000,"comment_count":7_300,"duration":510,"description":"India's benchmark Sensex index closed above 95,000 for the first time, driven by foreign institutional investor inflows and strong Q3 earnings.","url":"https://www.youtube.com/watch?v=ani011","thumbnail":"https://i.ytimg.com/vi/ani011/hqdefault.jpg","tags":["Sensex","BSE","India","markets"],"source":"seed"},
    {"video_id":"ani012","title":"Operation Sindoor: Indian Army Neutralises Terror Camp in PoK","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-14T06:00:00Z","view_count":9_800_000,"like_count":140_000,"comment_count":38_000,"duration":720,"description":"Indian Army conducted a cross-border precision strike on a terror camp in Pakistan-occupied Kashmir, neutralising a major militant hideout.","url":"https://www.youtube.com/watch?v=ani012","thumbnail":"https://i.ytimg.com/vi/ani012/hqdefault.jpg","tags":["India","Pakistan","PoK","army","surgery"],"source":"seed"},
    {"video_id":"ani013","title":"RBI Holds Repo Rate, Signals Potential Cut in April","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-12T11:30:00Z","view_count":780_000,"like_count":9_400,"comment_count":2_100,"duration":480,"description":"The Reserve Bank of India kept its repo rate at 6.25% but RBI Governor hinted at an April rate cut if inflation remains on target.","url":"https://www.youtube.com/watch?v=ani013","thumbnail":"https://i.ytimg.com/vi/ani013/hqdefault.jpg","tags":["RBI","India","reporate","inflation"],"source":"seed"},
    {"video_id":"ani014","title":"India Bans TikTok Successor Apps Over Data Concerns","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-10T09:00:00Z","view_count":3_400_000,"like_count":48_000,"comment_count":13_200,"duration":420,"description":"The Indian government extended its tech ban to include several TikTok successor applications amid data sovereignty and security concerns.","url":"https://www.youtube.com/watch?v=ani014","thumbnail":"https://i.ytimg.com/vi/ani014/hqdefault.jpg","tags":["India","TikTok","ban","cybersecurity"],"source":"seed"},
    {"video_id":"ani015","title":"UP Elections 2026: BJP Wins by Landslide — Final Results","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-08T20:00:00Z","view_count":6_700_000,"like_count":88_000,"comment_count":25_000,"duration":900,"description":"BJP secured a decisive victory in the Uttar Pradesh state elections, winning 320 of 403 assembly seats. Opposition parties demand recount in key constituencies.","url":"https://www.youtube.com/watch?v=ani015","thumbnail":"https://i.ytimg.com/vi/ani015/hqdefault.jpg","tags":["UP","elections","BJP","India","politics"],"source":"seed"},
    {"video_id":"ani016","title":"Heavy Rains and Floods Devastate Maharashtra — Relief Operations Underway","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-06T05:00:00Z","view_count":1_800_000,"like_count":22_000,"comment_count":5_800,"duration":560,"description":"Unprecedented February rains caused severe flooding across Maharashtra. NDRF teams have rescued over 4,000 people in the last 48 hours.","url":"https://www.youtube.com/watch?v=ani016","thumbnail":"https://i.ytimg.com/vi/ani016/hqdefault.jpg","tags":["flood","Maharashtra","India","disaster"],"source":"seed"},
    {"video_id":"ani017","title":"Reliance Jio Launches 6G Trials in Mumbai","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-04T10:00:00Z","view_count":2_500_000,"like_count":33_000,"comment_count":8_100,"duration":540,"description":"Reliance Jio announced the commencement of 6G field trials in Mumbai with speeds topping 1 Tbps, aiming for commercial launch by 2028.","url":"https://www.youtube.com/watch?v=ani017","thumbnail":"https://i.ytimg.com/vi/ani017/hqdefault.jpg","tags":["Jio","6G","telecom","India","tech"],"source":"seed"},
    {"video_id":"ani018","title":"India-China Border Standoff Resolved at LAC — Troops Disengage","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-02-02T14:00:00Z","view_count":4_300_000,"like_count":60_000,"comment_count":16_000,"duration":660,"description":"India and China confirmed full disengagement of troops at remaining friction points along the Line of Actual Control after months of diplomacy.","url":"https://www.youtube.com/watch?v=ani018","thumbnail":"https://i.ytimg.com/vi/ani018/hqdefault.jpg","tags":["India","China","LAC","border","military"],"source":"seed"},
    {"video_id":"ani019","title":"India Sets Solar Energy Record — 200 GW Installed Capacity","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-01-31T08:00:00Z","view_count":1_400_000,"like_count":20_000,"comment_count":4_500,"duration":480,"description":"India achieved the 200 GW solar installed capacity milestone, becoming the third country in the world after China and the USA to reach this target.","url":"https://www.youtube.com/watch?v=ani019","thumbnail":"https://i.ytimg.com/vi/ani019/hqdefault.jpg","tags":["solar","energy","India","greentech"],"source":"seed"},
    {"video_id":"ani020","title":"Bengaluru Techie Terror Plot Foiled — 5 Arrested by NIA","channel":"ANI News India","channel_id":"UCtFQDgA8J8_iiwc5-KoAQlg","upload_date":"2026-01-29T17:00:00Z","view_count":3_100_000,"like_count":42_000,"comment_count":10_800,"duration":600,"description":"NIA arrested five individuals in Bengaluru who were allegedly planning a coordinated cyber-terror attack on critical Indian infrastructure.","url":"https://www.youtube.com/watch?v=ani020","thumbnail":"https://i.ytimg.com/vi/ani020/hqdefault.jpg","tags":["NIA","terror","Bengaluru","India","cybercrime"],"source":"seed"},
]


# ── DB Init ─────────────────────────────────────────────────────────────────
def _get_conn():
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    return conn

def _init():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            data     TEXT NOT NULL
        )
    """)
    conn.commit()
    # Seed only if empty
    cur.execute("SELECT COUNT(*) FROM videos")
    if cur.fetchone()[0] == 0:
        for rec in _SEED:
            cur.execute(
                "INSERT OR REPLACE INTO videos (video_id, data) VALUES (?, ?)",
                (rec["video_id"], json.dumps(rec))
            )
        conn.commit()
    conn.close()

_init()


# ── Cursor wrapper ───────────────────────────────────────────────────────────
class _Cursor:
    def __init__(self, rows):
        self._rows = list(rows)
        self._sort_key = None
        self._sort_dir = -1
        self._skip_n = 0
        self._limit_n = None

    def sort(self, key_or_list, direction=-1):
        if isinstance(key_or_list, list):
            # list of (key, dir) tuples
            self._sort_key = key_or_list[0][0]
            self._sort_dir = key_or_list[0][1]
        else:
            self._sort_key = key_or_list
            self._sort_dir = direction
        return self

    def skip(self, n):
        self._skip_n = n
        return self

    def limit(self, n):
        self._limit_n = n
        return self

    def _resolve(self):
        rows = self._rows
        if self._sort_key:
            rev = (self._sort_dir == -1)
            rows = sorted(rows, key=lambda x: (x.get(self._sort_key) or ""), reverse=rev)
        if self._skip_n:
            rows = rows[self._skip_n:]
        if self._limit_n is not None:
            rows = rows[:self._limit_n]
        return rows

    def __iter__(self):
        return iter(self._resolve())

    def __getitem__(self, idx):
        return self._resolve()[idx]


# ── Filter helpers ───────────────────────────────────────────────────────────
def _match(row, filt):
    """Recursively match a row against a MongoDB-style filter dict."""
    for key, cond in filt.items():
        if key == "$text":
            search = (cond.get("$search") or "").lower()
            haystack = (row.get("title", "") + " " + row.get("description", "")).lower()
            if search not in haystack:
                return False
        elif isinstance(cond, dict):
            val = row.get(key)
            for op, op_val in cond.items():
                if op == "$regex":
                    flags = re.IGNORECASE if "i" in cond.get("$options", "") else 0
                    if not re.search(op_val, str(val or ""), flags):
                        return False
                elif op == "$options":
                    continue
                elif op == "$gte":
                    if val is None or val < op_val:
                        return False
                elif op == "$lte":
                    if val is None or val > op_val:
                        return False
                elif op == "$gt":
                    if val is None or val <= op_val:
                        return False
                elif op == "$lt":
                    if val is None or val >= op_val:
                        return False
        else:
            if row.get(key) != cond:
                return False
    return True


def _all_rows():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT data FROM videos")
    rows = [json.loads(r[0]) for r in cur.fetchall()]
    conn.close()
    return rows


# ── Collection class ─────────────────────────────────────────────────────────
class LocalCollection:
    """Drop-in replacement for a pymongo Collection for demo use."""

    def count_documents(self, filt=None):
        rows = [r for r in _all_rows() if _match(r, filt or {})]
        return len(rows)

    def find(self, filt=None):
        rows = [r for r in _all_rows() if _match(r, filt or {})]
        return _Cursor(rows)

    def find_one(self, filt=None, sort=None):
        rows = [r for r in _all_rows() if _match(r, filt or {})]
        if sort:
            key = sort[0][0]; direction = sort[0][1]
            rows = sorted(rows, key=lambda x: (x.get(key) or ""), reverse=(direction == -1))
        return rows[0] if rows else None

    def distinct(self, field):
        return list({r.get(field) for r in _all_rows() if r.get(field)})

    def aggregate(self, pipeline):
        """Minimal $group + $sort + $project support."""
        rows = _all_rows()
        result = []
        for stage in pipeline:
            if "$group" in stage:
                groups = {}
                spec = stage["$group"]
                id_field = spec.get("_id")
                for row in rows:
                    grp_key = row.get(id_field.lstrip("$"), "") if isinstance(id_field, str) and id_field.startswith("$") else id_field
                    if grp_key not in groups:
                        groups[grp_key] = {"_id": grp_key, "_rows": []}
                    groups[grp_key]["_rows"].append(row)
                agg_rows = []
                for grp_key, grp in groups.items():
                    rec = {"_id": grp_key}
                    for out_field, expr in spec.items():
                        if out_field == "_id":
                            continue
                        if isinstance(expr, dict):
                            op = list(expr.keys())[0]
                            src = list(expr.values())[0]
                            src_key = src.lstrip("$") if isinstance(src, str) else None
                            if op == "$sum":
                                if src == 1:
                                    rec[out_field] = len(grp["_rows"])
                                else:
                                    rec[out_field] = sum(r.get(src_key, 0) or 0 for r in grp["_rows"])
                            elif op == "$avg":
                                vals = [r.get(src_key, 0) or 0 for r in grp["_rows"]]
                                rec[out_field] = sum(vals) / len(vals) if vals else 0
                            elif op == "$max":
                                vals = [r.get(src_key) for r in grp["_rows"] if r.get(src_key)]
                                rec[out_field] = max(vals) if vals else None
                            elif op == "$min":
                                vals = [r.get(src_key) for r in grp["_rows"] if r.get(src_key)]
                                rec[out_field] = min(vals) if vals else None
                    agg_rows.append(rec)
                rows = agg_rows
                result = agg_rows
            elif "$sort" in stage:
                spec = stage["$sort"]
                for k, v in reversed(list(spec.items())):
                    rows = sorted(rows, key=lambda x: (x.get(k) or ""), reverse=(v == -1))
                result = rows
            elif "$project" in stage:
                result = rows  # simplified — keep as-is for demo
            elif "$limit" in stage:
                rows = rows[:stage["$limit"]]
                result = rows
        return iter(result)

    def create_index(self, *args, **kwargs):
        pass  # no-op


def get_local_collection() -> LocalCollection:
    return LocalCollection()
