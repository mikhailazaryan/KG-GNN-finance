import json
import feedparser
import configparser
import google.generativeai as genai

model = genai.GenerativeModel("gemini-1.5-pro-latest")
config = configparser.ConfigParser()
config.read('config.ini')
genai.configure(api_key=config['gemini']['api_key'])

output_file_path = "files/benchmarking_data/real_articles_temp.json"

def fetch_news(search_term, max_articles=10):
    """
    Fetch news articles for a given search term from Google RSS feed.

    Args:
        search_term (str): The search term for querying Google News RSS.
        max_articles (int): Maximum number of articles to fetch.

    Returns:
        list: A list of dictionaries, each containing details of a news article.
    """
    search_term = search_term.replace(" ", "+")
    gn_url = f"https://news.google.com/rss/search?q={search_term}&hl=en-US&gl=US&ceid=US:en"
    gn_feed = feedparser.parse(gn_url)
    print(f"Generated RSS URL: {gn_url}")

    articles = []

    if gn_feed.entries:
        print(f"Found {len(gn_feed.entries)} articles. Limiting to {max_articles}.")
        for news_item in gn_feed.entries[:max_articles]:  # Limit the number of articles
            print(f"Processing article {news_item}: {news_item.title}")
            article = {
                "text": news_item.title,
                "source": news_item.link,
                "date": news_item.published if "published" in news_item else None,
                "benchmarking": {
                    "model update triples": {
                        "unchanged": [],
                        "added": [],
                        "deleted": []
                    },
                    "correct update": None,
                    "wikidata structure": None
                }
            }
            articles.append(article)
    else:
        print(f"No news found for the term: {search_term}")

    return articles


def generate_real_articles_json(companies):
    """
    Build a JSON structure for synthetic articles.

    Args:
        companies (list): List of company names for which to fetch articles.

    Returns:
        dict: A dictionary structured as synthetic articles JSON.
    """
    real_articles = {}

    for company in companies:
        print(f"\nFetching articles for company: {company}")
        articles = fetch_news(company)  # Fetch news articles for the company
        company_data = {company: {}}

        for idx, article in enumerate(articles, 1):
            article_key = f"article_{idx}"
            print(f"Adding article {idx} to {company}'s data.")
            company_data[company][article_key] = article  # Directly assign the article data


        real_articles.update(company_data)
        print(f"Completed processing for company: {company}")
    print("All companies processed. Returning synthetic articles JSON.")
    return real_articles


def save_to_json(data, filename=output_file_path):
    """Saves the generated data to a JSON file."""
    print(f"Saving synthetic articles to {filename}")
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    print("Data successfully saved.")


def get_synthetic_articles(companies: list = None):
    # depreciated, only here for backup
    synthetic_articles = {
        "Adidas AG": {
            "article_1": "Adidas AG acquires majority stake in fitness technology company Runtastic, expanding its digital sports portfolio.",
            "article_2": "Kasper Rorsted steps down as CEO of Adidas AG; Bjørn Gulden appointed as his successor.",
            "article_3": "Adidas AG opens new North American headquarters in Portland, Oregon, strengthening its presence in the US sports market.",
            "article_4": "Adidas AG launches 'UltraBoost 23,' its latest running shoe innovation, featuring improved cushioning and energy return.",
            "article_5": "Adidas AG founder Adi Dassler's legacy celebrated with a special exhibition at the Deutsches Historisches Museum in Berlin, Germany.",
            "article_6": "Adidas AG partners with Parley for the Oceans to create sustainable sportswear made from recycled ocean plastic.",
            "article_7": "Adidas AG joins the Dow Jones Sustainability Index, recognizing its commitment to environmental and social responsibility.",
            "article_8": "Adidas AG expands its partnership with Major League Soccer (MLS), becoming the official outfitter for all MLS teams.",
            "article_9": "Thomas Rabe appointed to the Adidas AG Supervisory Board, bringing extensive experience in the media and entertainment industry.",
            "article_10": "Sportware Company Adidas is no longer part of the CDAX after a couple of bad quarters, says company spokesperson",
        },

        "Airbus SE": {
            "article_1": "Airbus SE acquires Bombardier's CSeries aircraft program, renaming it Airbus A220.",
            "article_2": "Airbus SE divests its stake in Dassault Aviation, selling its remaining shares.",
            "article_3": "Airbus SE is being acquired by the conglomerate Global Aerospace Industries.",
            "article_4": "Guillaume Faury replaces Tom Enders as the CEO of Airbus SE.",
            "article_5": "Catherine Guillouard leaves the board of directors of Airbus SE, and  Anita DeFrantz joins the board.",
            "article_6": "Airbus SE's stock listing moves from the Euronext Paris to the New York Stock Exchange.",
            "article_7": "Airbus SE launches the new Zephyr HAPS (High Altitude Platform Station) for long-duration stratospheric flight.",
            "article_8": "Airbus SE discontinues production of the A380 superjumbo passenger aircraft due to low demand.",
            "article_9": "Airbus SE establishes a new research and development facility focused on sustainable aviation fuels in Melbourne, Australia, relocating some operations from Toulouse.",
            "article_10": "Airbus SE announces a strategic partnership with SpaceX to explore the use of reusable rockets for launching large aerospace components into orbit."
        },

        "Allianz SE": {
            "article_1": "Allianz SE acquires a majority stake in GoHealth, a leading online health insurance marketplace, expanding its digital health offerings.",
            "article_2": "Oliver Bäte remains CEO of Allianz SE, outlining a new five-year strategic plan focused on sustainable growth and digital transformation.",
            "article_3": "Allianz SE establishes a new global innovation hub in Singapore, strengthening its presence in the Asia-Pacific region and fostering InsurTech development.",
            "article_4": "Allianz SE launches 'Allianz Protect,' a new cybersecurity insurance product designed for small and medium-sized businesses, addressing the growing threat of cyberattacks.",
            "article_5": "Allianz SE celebrates its 130th anniversary with a series of events highlighting its history and commitment to social responsibility.",
            "article_6": "Allianz SE partners with the World Wide Fund for Nature (WWF) on a global initiative to protect biodiversity and promote sustainable development.",
            "article_7": "Allianz SE is included in the FTSE4Good Index Series, recognizing its strong performance in environmental, social, and governance (ESG) practices.",
            "article_8": "Allianz SE expands its partnership with Formula E, the electric motor racing championship, becoming the official insurance partner of the series.",
            "article_9": "Sirma Boshnakova is appointed to the Allianz SE Supervisory Board, bringing expertise in technology and digital transformation to the board.",
        },

        "BASF SE": {
            "article_1": "BASF SE acquires Solenis, a global leader in specialty chemicals for water-intensive industries.",
            "article_2": "BASF SE is acquired by Sinochem, a state-owned Chinese chemical company, in a landmark deal.",
            "article_3": "BASF SE divests its construction chemicals business to an affiliate of Lone Star Funds, a global private equity firm.",
            "article_4": "BASF SE shifts its strategic focus from traditional chemicals to sustainable agricultural solutions and biotechnology, expanding its presence in the agricultural technology sector.",
            "article_5": "Martin Brudermüller steps down as CEO of BASF SE, replaced by Saori Dubourg, previously the company's Chief Agricultural Officer.",
            "article_6": "Two new members, Dr. Feike Sijbesma and Susie Wolff, join the Supervisory Board of BASF SE, bringing expertise in sustainability and innovation.",
            "article_7": "BASF SE relocates its global headquarters from Ludwigshafen, Germany, to a new state-of-the-art facility in Mannheim, Germany, to accommodate its growing workforce.",
            "article_8": "BASF SE introduces a new biodegradable plastic alternative, 'Ecovio Plus,' designed for packaging and agricultural applications, while phasing out the production of certain legacy polystyrene products.",
            "article_9": "BASF SE is added to the DAX 50 ESG Index, reflecting its commitment to environmental, social, and governance (ESG) principles.",
            "article_10": "BASF SE announces a strategic partnership with Microsoft to develop AI-powered solutions for optimizing chemical production processes and accelerating materials discovery."
        },

        "Bayer AG": {
            "article_1": "Bayer AG acquires Asklepios BioPharmaceutical (AskBio), a leading gene therapy company, to expand its cell and gene therapy portfolio.",
            "article_2": "Bayer AG is the target of a takeover bid by a consortium led by private equity firm CVC Capital Partners and Singapore's Temasek Holdings.",
            "article_3": "Bayer AG divests its Environmental Science Professional business to Cinven, a British private equity firm, for $2.6 billion.",
            "article_4": "Bayer AG announces a strategic shift towards digital health solutions, leveraging data analytics and artificial intelligence to personalize patient care and improve outcomes.",
            "article_5": "Werner Baumann steps down as CEO of Bayer AG; Bill Anderson, former CEO of Roche Pharmaceuticals, is appointed as his successor.",
            "article_6": "Dr. Fei-Fei Li, a renowned AI expert, joins the Supervisory Board of Bayer AG, bringing her expertise in artificial intelligence and machine learning.",
            "article_7": "Bayer AG consolidates its North American headquarters in Whippany, New Jersey, streamlining operations and fostering collaboration.",
            "article_8": "Bayer AG introduces a new precision oncology drug, 'OncoTarget,' targeting specific genetic mutations in cancer cells, while discontinuing the production of its legacy antibiotic, 'Ciprobay XR'.",
            "article_9": "Bayer AG is removed from the Dow Jones Sustainability Index due to concerns regarding its environmental impact related to pesticide production.",
            "article_10": "Bayer AG establishes a partnership with the Bill & Melinda Gates Foundation to develop and distribute affordable malaria treatments in developing countries."
        },

        "Beiersdorf AG": {
            "article_1": "Beiersdorf AG acquires Coppertone, the iconic sunscreen brand, from Bayer AG, strengthening its sun care portfolio.",
            "article_2": "Beiersdorf AG becomes a target of acquisition by Unilever, a leading consumer goods company, sparking speculation about the future of the NIVEA brand.",
            "article_3": "Beiersdorf AG divests its tesa SE business, specializing in adhesive tapes and solutions, through an initial public offering (IPO).",
            "article_4": "Beiersdorf AG expands its focus beyond skincare and cosmetics, venturing into the pharmaceutical sector with the development of dermatological treatments.",
            "article_5": "Vincent Warnery replaces Stefan De Loecker as CEO of Beiersdorf AG, bringing experience from L'Oréal and other consumer goods companies.",
            "article_6": "Nathalie Roos, former CEO of L'Oréal's Professional Products Division, joins the Supervisory Board of Beiersdorf AG.",
            "article_7": "Beiersdorf AG announces plans to relocate its headquarters from Hamburg, Germany, to a new, modern facility in Berlin, aiming to attract top talent and foster innovation.",
            "article_8": "Beiersdorf AG launches a new line of sustainable, vegan skincare products under the NIVEA Naturally Good brand, while phasing out certain product lines containing microplastics.",
            "article_9": "Beiersdorf AG is added to the EURO STOXX 50 index, reflecting its strong financial performance and market capitalization.",
            "article_10": "Beiersdorf AG partners with Google to develop personalized skincare recommendations using AI-powered skin analysis technology."
        },

        "BMW AG": {
            "article_1": "BMW AG acquires Alpina Burkard Bovensiepen GmbH & Co. KG, fully integrating the long-time tuning and manufacturing partner into its operations.",
            "article_2": "BMW AG becomes the target of a surprise takeover bid by Volkswagen AG, creating a potential automotive industry giant.",
            "article_3": "BMW AG divests its Parkmobile LLC subsidiary, a provider of parking payment solutions, to EasyPark Group.",
            "article_4": "BMW AG announces a significant investment in urban air mobility, developing electric vertical takeoff and landing (eVTOL) aircraft for future transportation solutions.",
            "article_5": "Oliver Zipse replaces Harald Krüger as CEO of BMW AG, bringing a focus on electric mobility and sustainability.",
            "article_6": "Elon Musk, CEO of Tesla, unexpectedly joins the Supervisory Board of BMW AG, fueling speculation about potential collaborations.",
            # Fictional, but possible scenario for testing
            "article_7": "BMW AG establishes a new North American headquarters in Spartanburg, South Carolina, expanding its existing manufacturing facility and creating new jobs.",
            "article_8": "BMW AG launches its new flagship electric sedan, the i7, featuring advanced autonomous driving capabilities, while phasing out production of the i3 city car.",
            "article_9": "BMW AG is added to the STOXX Europe 600 Automobiles & Parts index, reflecting its strong performance in the automotive sector.",
            "article_10": "BMW AG partners with Amazon Web Services (AWS) to develop a connected car platform, offering enhanced driver assistance and entertainment features."
        },

        "Brenntag SE": {
            "article_1": "Brenntag SE acquires Univar Solutions, a global chemical and ingredients distributor, creating a leading player in the industry.",
            "article_2": "Brenntag SE is acquired by Bain Capital Private Equity, a leading global private investment firm, in a leveraged buyout.",
            "article_3": "Brenntag SE divests its specialty chemicals distribution business in the Asia-Pacific region to IMCD N.V., a Dutch chemical distributor.",
            "article_4": "Brenntag SE expands its focus into life sciences and pharmaceutical ingredients distribution, establishing a dedicated division to serve this growing market.",
            "article_5": "Christian Kohlpaintner replaces Steven Holland as CEO of Brenntag SE, bringing extensive experience in the chemical industry.",
            "article_6": "Two new independent directors,  Dr. Maria Helena Braga and  Mr. Jean-Pierre Clamadieu, join the Supervisory Board of Brenntag SE, enhancing its expertise in sustainability and corporate governance.",
            "article_7": "Brenntag SE relocates its global headquarters from Essen, Germany, to a new, modern facility in Frankfurt, Germany, to improve operational efficiency and attract top talent.",
            "article_8": "Brenntag SE introduces a new digital platform for chemical distribution, offering enhanced supply chain visibility and online ordering capabilities, while phasing out its traditional paper-based order processing system.",
            "article_9": "Brenntag SE is added to the MDAX index of German mid-cap companies, reflecting its increasing market capitalization and trading volume.",
            "article_10": "Brenntag SE forms a strategic alliance with Maersk, a global logistics and shipping company, to optimize its global supply chain and reduce transportation costs."
        },

        "Commerzbank AG": {
            "article_1": "Commerzbank AG acquires the online banking platform of ING-DiBa AG, expanding its digital customer base.",
            "article_2": "Commerzbank AG is acquired by Deutsche Bank AG in a merger that reshapes the German banking landscape.",
            "article_3": "Commerzbank AG sells its Polish subsidiary, mBank S.A., to a consortium led by Banco Santander, S.A.",
            "article_4": "Commerzbank AG announces a strategic shift towards sustainable finance, focusing on investments in renewable energy and green technologies.",
            "article_5": "Manfred Knof replaces Martin Zielke as CEO of Commerzbank AG, aiming to improve profitability and streamline operations.",
            "article_6": "Claudia Plattner, a fintech expert, joins the Supervisory Board of Commerzbank AG, bringing her expertise in digital transformation and innovation.",
            "article_7": "Commerzbank AG consolidates its Frankfurt operations, moving its headquarters to a new, modern building in the city's financial district.",
            "article_8": "Commerzbank AG launches a new mobile banking app with enhanced security features and personalized financial management tools, while discontinuing its legacy online trading platform.",
            "article_9": "Commerzbank AG is removed from the DAX index and added to the MDAX index, reflecting its reduced market capitalization.",
            "article_10": "Commerzbank AG partners with Google Cloud to develop AI-powered fraud detection and risk management solutions for its banking operations."
        },

        "Continental AG": {
            "article_1": "Continental AG acquires Elektrobit Automotive GmbH, a leading provider of embedded software solutions for the automotive industry, strengthening its software competencies.",
            "article_2": "Continental AG is acquired by Schaeffler AG, a global automotive and industrial supplier, in a strategic move to consolidate the automotive supply chain.",
            # // Hypothetical,for testing
            "article_3": "Continental AG divests its ContiTech Conveyor Belt Group to private equity firm Carlyle Group, focusing its resources on core automotive technologies.",
            "article_4": "Continental AG expands its focus on mobility services, developing a platform for autonomous driving and smart city solutions, moving beyond traditional tire and automotive parts manufacturing.",
            "article_5": "Nikolai Setzer replaces Elmar Degenhart as CEO of Continental AG, bringing a renewed focus on digital transformation and software-defined vehicles.",
            "article_6": "Mary Barra, CEO of General Motors, joins the Supervisory Board of Continental AG, fostering collaboration between the two automotive giants.",
            # Hypothetical,for testing
            "article_7": "Continental AG relocates its global headquarters from Hanover, Germany, to a new, state-of-the-art facility in Berlin, aiming to attract top talent and enhance its research and development capabilities.",
            "article_8": "Continental AG introduces a new generation of tires with integrated sensors for real-time road condition monitoring, while phasing out production of its traditional hydraulic brake systems in favor of electromechanical brake systems.",
            "article_9": "Continental AG is removed from the DAX index due to a decline in market capitalization and added to the MDAX index.",
            # // Hypothetical,
            "article_10": "Continental AG partners with NVIDIA, a leading technology company specializing in AI and graphics processing units (GPUs), to develop advanced driver-assistance systems (ADAS) and autonomous driving solutions."
        },

        "Covestro": {
            "article_1": "Covestro acquired the thermoplastic polyurethane (TPU) business of the US-based company Lubrizol Corporation for an undisclosed sum.",
            "article_2": "Covestro was rumored to be a potential acquisition target for Evonik Industries, although no official bid has been made.",
            "article_3": "Covestro has successfully completed the sale of its European Systems Houses business to H.I.G. Capital.",
            "article_4": "While traditionally focused on polyurethanes, Covestro is expanding its portfolio into the additive manufacturing market, showcasing new 3D printing materials and solutions.",
            "article_5": "Dr. Markus Steilemann stepped down as CEO of Covestro, and was replaced by Dr. Melanie Maas-Brunner, formerly the head of the Coatings, Adhesives, and Specialties segment.",
            "article_6": "Richard Pott, former CFO of Bayer AG, joined the Supervisory Board of Covestro, replacing Dr. Johannes Dietsch.",
            "article_7": "Covestro announced plans to relocate its global headquarters from Leverkusen, Germany to a new, state-of-the-art facility in Düsseldorf, Germany to foster innovation and collaboration.",
            "article_8": "Covestro is phasing out the production of its legacy polycarbonate resin, Makrolon 2458, and replacing it with a more sustainable and higher-performing alternative, Makrolon RE 3477, made with recycled content.",
            "article_9": "Covestro's stock was added to the German MDAX index, reflecting its growing market capitalization and importance in the German economy.",
            "article_10": "Covestro partnered with the non-profit organization Plastic Bank to establish a plastic collection and recycling infrastructure in coastal communities in Indonesia, aiming to reduce ocean plastic pollution and create social impact."
        },

        "Daimler Truck": {
            "article_1": "Daimler Truck acquired Torc Robotics, a Virginia-based autonomous driving software company, to accelerate its development of self-driving trucks.",
            "article_2": "While unlikely given its recent spin-off, hypothetical rumors circulated about a potential acquisition of Daimler Truck by Volvo Group to consolidate the heavy-duty vehicle market.",
            "article_3": "Daimler Truck divested its stake in Mitsubishi Fuso Truck and Bus Corporation to focus on its core brands: Mercedes-Benz, Freightliner, and Western Star.",
            "article_4": "Daimler Truck is expanding into hydrogen fuel cell technology, announcing partnerships with various energy companies to develop a hydrogen refueling infrastructure for its upcoming fleet of fuel-cell trucks.",
            "article_5": "Martin Daum stepped down as CEO of Daimler Truck, and Karin Rådström, formerly the head of Mercedes-Benz Trucks, was appointed as his successor.",
            "article_6": "Joe Kaeser, former CEO of Siemens, joined Daimler Truck's Supervisory Board, replacing Manfred Bischoff.",
            "article_7": "Daimler Truck established a new North American headquarters in Portland, Oregon, consolidating various operations and strengthening its presence in the region.",
            "article_8": "Daimler Truck launched the new electric eCascadia semi-truck, expanding its electric vehicle portfolio and targeting the growing demand for sustainable freight transport.",
            "article_9": "Daimler Truck was included in the DAX 40 index, Germany's benchmark stock market index, reflecting its significant market capitalization and importance to the German economy.",
            "article_10": "Daimler Truck announced a strategic partnership with Waymo Via to develop and deploy autonomous trucking technology in the United States, integrating Waymo Driver into Daimler Truck's Freightliner Cascadia platform."
        },

        "Deutsche Bank": {
            "article_1": "Deutsche Bank acquired the German fintech company, FinLeap Connect, in July 2024.",
            "article_2": "In a surprise move, JP Morgan Chase initiated talks to acquire Deutsche Bank in the first quarter of 2025. [[None]]",
            "article_3": "Deutsche Bank divested its asset management subsidiary, DWS Group, to BlackRock in August 2024. [[None]]",
            "article_4": "Deutsche Bank announced its expansion into the sustainable finance sector, offering green bonds and impact investing products, marking a shift from its traditional focus on investment banking. [[None]]",
            "article_5": "Effective January 1, 2025, Christian Sewing was replaced by  Arundhati Bhattacharya as CEO of Deutsche Bank. [[None]]",
            "article_6": "Elon Musk joined the board of directors of Deutsche Bank in September 2024. [[None]]",
            "article_7": "Deutsche Bank relocated its global headquarters from Frankfurt, Germany to London, England in November 2024. [[None]]",
            "article_8": "Deutsche Bank launched a new mobile banking app with integrated AI-powered financial advisor features in October 2024. [[None]]",
            "article_9": "Deutsche Bank was added to the NASDAQ-100 index in December 2024. [[None]]",
            "article_10": "Deutsche Bank partnered with SpaceX to offer exclusive investment opportunities related to space exploration and tourism. [[None]]"
        },

        "Deutsche Börse": {
            "article_1": "Deutsche Börse acquired the remaining stake in Institutional Shareholder Services Inc. (ISS) from Genstar Capital.",
            "article_2": "Deutsche Börse was rumored to be a potential acquisition target for the London Stock Exchange Group, though no deal materialized.",
            "article_3": "Deutsche Börse divested its index business STOXX to Qontigo, a subsidiary of  Axioma.",
            "article_4": "While traditionally focused on financial exchange operations, Deutsche Börse expanded its offerings to include data analytics and regulatory technology services.",
            "article_5": "Theodor Weimer replaced Carsten Kengeter as CEO of Deutsche Börse in 2018.",
            "article_6": "Ingrid Neubauer joined the Supervisory Board of Deutsche Börse, replacing  Ann-Kristin Achleitner.",
            "article_7": "While its headquarters remain in Frankfurt, Deutsche Börse opened a new technology hub in Luxembourg.",
            "article_8": "Deutsche Börse launched a new suite of ESG data products aimed at supporting sustainable investment strategies.",
            "article_9": "Deutsche Börse AG was added to the EURO STOXX 50 index.",
            "article_10": "Deutsche Börse partnered with Google Cloud to migrate its trading infrastructure to the cloud, aiming to improve latency and scalability."
        },

        "Deutsche Post": {
            "article_1": "Deutsche Post DHL acquired UK-based logistics company Jeavons Eurotir.",
            "article_2": "Speculation arose about a potential takeover of Deutsche Post by Amazon, though no such deal has been confirmed.",
            "article_3": "Deutsche Post sold its Williams Lea Tag document management business to Advent International.",
            "article_4": "Deutsche Post expanded further into e-commerce fulfillment services, establishing new warehouses and partnerships with online retailers.",
            "article_5": "Frank Appel continues as CEO of Deutsche Post DHL Group.",
            "article_6": "Jürgen Fitschen retired from the Supervisory Board of Deutsche Post DHL Group.",
            "article_7": "Deutsche Post maintains its global headquarters in Bonn, Germany.",
            "article_8": "Deutsche Post introduced its 'GoGreen' carbon-neutral shipping option for environmentally conscious customers.",
            "article_9": "Deutsche Post AG is listed on the DAX index.",
            "article_10": "Deutsche Post announced a strategic partnership with Ford to develop autonomous delivery vehicles for last-mile logistics."
        },

        "Deutsche Telekom": {
            "article_1": "Deutsche Telekom acquired a majority stake in Greek telecommunications company OTIM.",
            "article_2": "Reports suggested that SoftBank considered a merger with Deutsche Telekom's T-Mobile US unit, although the deal did not proceed.",
            "article_3": "Deutsche Telekom spun off its towers business, creating GD Towers, a leading European tower infrastructure provider.",
            "article_4": "Deutsche Telekom intensified its focus on cybersecurity solutions, expanding its offerings for businesses and consumers.",
            "article_5": "Timotheus Höttges is the CEO of Deutsche Telekom.",
            "article_6": "Ulrich Lehner joined the Supervisory Board of Deutsche Telekom.",
            "article_7": "Deutsche Telekom's headquarters are located in Bonn, Germany.",
            "article_8": "Deutsche Telekom launched MagentaTV, its IPTV platform, offering live television, streaming services, and on-demand content.",
            "article_9": "Deutsche Telekom AG is a component of the DAX index.",
            "article_10": "Deutsche Telekom partnered with NVIDIA to build an AI-powered network cloud, leveraging artificial intelligence to optimize network performance and efficiency."
        },

        "Eon": {
            "article_1": "E.ON acquired the renewable energy company Innogy from RWE in 2019.",
            "article_2": "Rumors surfaced in 2022 about a potential takeover of E.ON by a consortium of private equity investors, but the deal never materialized.",
            "article_3": "E.ON sold its stake in the nuclear power plant PreussenElektra to EnBW in 2020.",
            "article_4": "E.ON is shifting its focus from conventional power generation to renewable energy and energy grids, aiming to become a leading player in the energy transition.",
            "article_5": "Leonhard Birnbaum succeeded Johannes Teyssen as CEO of E.ON in 2021.",
            "article_6": "Dr. Helen Gugelmann joined the supervisory board of E.ON in 2023.",
            "article_7": "While maintaining its headquarters in Essen, Germany, E.ON opened a new innovation hub in Berlin in 2024 focusing on smart grid technologies.",
            "article_8": "E.ON launched a new home battery storage solution called E.ON Home Solar Battery in 2023.",
            "article_9": "E.ON was removed from the Dow Jones Sustainability Index in 2021 but rejoined in 2023 after improving its sustainability performance.",
            "article_10": "E.ON announced a strategic partnership with Microsoft in 2024 to develop a digital platform for optimizing energy consumption in smart cities."
        },

        "Fresenius": {
            "article_1": "Fresenius acquired the home dialysis provider NxStage Medical for $2 billion in 2019.",
            "article_2": "Fresenius was rumored to be a target for acquisition by private equity firms in late 2022.",
            "article_3": "Fresenius sold its stake in the blood transfusion company Vifor Pharma in 2021.",
            "article_4": "While traditionally focused on healthcare services and products, Fresenius is expanding into the digital health market with new software solutions.",
            "article_5": "Rice Powell replaced Stephan Sturm as CEO of Fresenius in 2022.",
            "article_6": "Dr. Simone Menne joined the supervisory board of Fresenius in 2023.",
            "article_7": "Fresenius moved its North American headquarters from Waltham, Massachusetts to Bad Homburg, Germany in 2024.",
            "article_8": "Fresenius launched the new Kabiven Peripheral parenteral nutrition solution in 2023.",
            "article_9": "Fresenius SE & Co. KGaA was removed from the DAX index and added to the MDAX index in 2023.",
            "article_10": "Fresenius announced a strategic partnership with Google Health to develop AI-powered diagnostic tools in 2024."
        },

        "Hannover Rück": {
            "article_1": "Hannover Rück acquired the Australian reinsurer Inter Hannover in 2017.",
            "article_2": "Market speculation in 2021 suggested a potential acquisition of Hannover Rück by Berkshire Hathaway, but no deal was finalized.",
            "article_3": "Hannover Rück sold its minority stake in the Brazilian reinsurer IRB Brasil Re in 2022.",
            "article_4": "Hannover Rück is expanding its focus beyond traditional reinsurance to include specialty insurance lines like cyber and parametric insurance.",
            "article_5": "Jean-Jacques Henchoz replaced Ulrich Wallin as CEO of Hannover Rück in 2022.",
            "article_6": "Silke Sehm joined the Executive Board of Hannover Rück in 2023, responsible for Property & Casualty Treaty Reinsurance.",
            "article_7": "Hannover Rück opened a new representative office in Singapore in 2024 to expand its presence in the Asian market.",
            "article_8": "Hannover Rück launched a new agricultural insurance product designed for climate change resilience in 2023.",
            "article_9": "Hannover Rück was added to the STOXX Europe 600 index in 2020.",
            "article_10": "Hannover Rück partnered with a leading climate research institute in 2024 to develop more accurate catastrophe models for pricing natural disaster risks."
        },

        "Heidelberg Mterials": {
            "article_1": "Heidelberg Materials acquired the Italian cement producer Italcementi in 2016.",
            "article_2": "Rumors circulated in 2021 that Heidelberg Materials was a potential acquisition target for LafargeHolcim, but no official bid was made.",
            "article_3": "Heidelberg Materials sold its stake in the US-based aggregates company Lehigh Hanson in 2019.",
            "article_4": "Heidelberg Materials is transitioning from a traditional cement producer to a provider of sustainable building materials, emphasizing low-carbon solutions.",
            "article_5": "Dominik von Achten replaced Bernd Scheifele as CEO of Heidelberg Materials in 2020.",
            "article_6": "Jose Antonio Lorenzo joined Heidelberg Materials' supervisory board in 2022.",
            "article_7": "Heidelberg Materials moved its headquarters to a new, energy-efficient building in Heidelberg, Germany, in 2023.",
            "article_8": "Heidelberg Materials introduced its new EcoCrete, a low-carbon concrete product, in 2024.",
            "article_9": "Heidelberg Materials was removed from the MDAX and included in the SDAX in 2021.",
            "article_10": "Heidelberg Materials announced a joint venture with CarbonCure Technologies to develop carbon-capturing concrete in 2023."
        },

        "Henkel AG & Co. KGaA": {
            "article_1": "Henkel AG & Co. KGaA acquired the laundry and home care business of The Clorox Company for $600 million.",
            "article_2": "Henkel AG & Co. KGaA was partially acquired by Procter & Gamble, with P&G taking a 20% stake in the company.",
            "article_3": "Henkel AG & Co. KGaA divested its stake in the cosmetics company, Schwarzkopf Professional, to the KKR investment firm.",
            "article_4": "While previously focusing primarily on consumer goods, Henkel AG & Co. KGaA announced a significant expansion into the biotechnology sector, partnering with Ginkgo Bioworks.",
            "article_5": "Carsten Knobel replaced Hans Van Bylen as CEO of Henkel AG & Co. KGaA in 2020.",
            "article_6": "Angela Merkel joined the supervisory board of Henkel AG & Co. KGaA after leaving her political career.",
            "article_7": "Henkel AG & Co. KGaA relocated its North American headquarters from Scottsdale, Arizona, to Stamford, Connecticut.",
            "article_8": "Henkel AG & Co. KGaA launched a new line of sustainable laundry detergents under the 'Love Nature' brand.",
            "article_9": "Henkel AG & Co. KGaA was added to the DAX 40 stock market index, replacing Beiersdorf AG.",
            "article_10": "Henkel AG & Co. KGaA announced a strategic partnership with IBM to develop AI-powered solutions for optimizing its supply chain."
        },

        "Infineon Technologies AG": {
            "article_1": "Infineon Technologies AG acquired Cypress Semiconductor Corporation for $10 billion, strengthening its position in the automotive chip market.",
            "article_2": "Rumors circulated that Intel Corporation was considering a takeover bid for Infineon Technologies AG, though no official offer was made.",
            "article_3": "Infineon Technologies AG sold its power management and multimarket business to a consortium led by Golden Gate Capital for $3 billion.",
            "article_4": "Infineon Technologies AG shifted its focus from primarily producing memory chips to specializing in power semiconductors and automotive electronics.",
            "article_5": "Reinhard Ploss stepped down as CEO of Infineon Technologies AG and was succeeded by Jochen Hanebeck.",
            "article_6": "Former German Chancellor Gerhard Schröder joined the supervisory board of Infineon Technologies AG, sparking some controversy.",
            "article_7": "Infineon Technologies AG opened a new research and development center in Dresden, Germany, focusing on artificial intelligence and autonomous driving technologies.",
            "article_8": "Infineon Technologies AG discontinued its line of legacy security chips, focusing on newer, more secure technologies.",
            "article_9": "Infineon Technologies AG was removed from the TecDAX index and added to the DAX 30, reflecting its growing market capitalization.",
            "article_10": "Infineon Technologies AG announced a major investment in a new semiconductor fabrication plant in Malaysia to increase production capacity."
        },
        "Mercedes-Benz": {
            "article_1": "Mercedes-Benz acquires electric vehicle charging network company ChargePoint.",
            "article_2": "Geely Holding Group has successfully completed its acquisition of Mercedes-Benz.",
            "article_3": "Mercedes-Benz divests its stake in Daimler Trucks, selling it to Traton SE.",
            "article_4": "Mercedes-Benz shifts its primary industry focus from solely automotive manufacturing to encompassing mobility solutions, including ride-sharing and autonomous driving technology.",
            "article_5": "Ola Källenius replaces Markus Schäfer as the Chief Technology Officer of Mercedes-Benz.",
            "article_6": "Non-executive director,  Arundhati Bhattacharya, joins the board of Mercedes-Benz, replacing Elmar Degenhart.",
            "article_7": "Mercedes-Benz relocates its global headquarters from Stuttgart, Germany to Berlin, Germany.",
            "article_8": "Mercedes-Benz discontinues production of the A-Class sedan, focusing resources on its electric vehicle lineup.",
            "article_9": "Mercedes-Benz is added to the DAX 40 stock market index, replacing Beiersdorf AG.",
            "article_10": "Mercedes-Benz announces a strategic partnership with NVIDIA to develop advanced artificial intelligence for its autonomous driving platform."
        },
        "Merck KGaA": {
            "article_1": "Merck KGaA acquires biotech company Genmab A/S for $5.8 billion.",
            "article_2": "Merck KGaA is acquired by Pfizer Inc. in a landmark pharmaceutical deal.",
            "article_3": "Merck KGaA sells its Performance Materials business unit to Evonik Industries AG.",
            "article_4": "Merck KGaA expands its focus from pharmaceuticals and life sciences to include digital healthcare solutions and artificial intelligence-driven drug discovery.",
            "article_5": " Belén Garijo replaces Stefan Oschmann as CEO of Merck KGaA.",
            "article_6": "Scott Gottlieb joins the supervisory board of Merck KGaA, replacing Wolfgang Büchele.",
            "article_7": "Merck KGaA moves its North American headquarters from Darmstadt, Germany to Cambridge, Massachusetts.",
            "article_8": "Merck KGaA launches a new immunotherapy drug for the treatment of lung cancer.",
            "article_9": "Merck KGaA is removed from the EURO STOXX 50 index, replaced by Airbus SE.",
            "article_10": "Merck KGaA establishes a $1 billion venture capital fund to invest in early-stage biotech companies."
        },
        "MTU Aero Engines AG": {
            "article_1": "MTU Aero Engines AG acquires aircraft engine maintenance company Lufthansa Technik AG.",
            "article_2": "Rolls-Royce plc acquires MTU Aero Engines AG in a strategic move to consolidate the aerospace industry.",
            "article_3": "MTU Aero Engines AG sells its military engine division to Pratt & Whitney.",
            "article_4": "MTU Aero Engines AG diversifies its business model, expanding from solely aircraft engines to also include space propulsion systems and renewable energy technologies.",
            "article_5": "Lars Wagner replaces Reiner Winkler as CEO of MTU Aero Engines AG.",
            "article_6": "Ann Dowling replaces Klaus Eberhardt on the supervisory board of MTU Aero Engines AG.",
            "article_7": "MTU Aero Engines AG opens a new research and development facility in Munich, Germany.",
            "article_8": "MTU Aero Engines AG introduces a new fuel-efficient engine for short-haul aircraft.",
            "article_9": "MTU Aero Engines AG is added to the MDAX German stock market index.",
            "article_10": "MTU Aero Engines AG announces a partnership with Airbus to develop a hydrogen-powered aircraft engine."
        },
        "Munich RE AG": {
            "article_1": "Munich RE AG acquired the US-based reinsurer, Great Lakes Reinsurance, for $2.2 billion.",
            "article_2": "Warren Buffett's Berkshire Hathaway made a significant investment in Munich RE AG, acquiring a 10% stake.",
            "article_3": "Munich RE AG divested its stake in the UK-based insurance broker, Willis Towers Watson.",
            "article_4": "Munich RE AG expanded its focus from primarily reinsurance to also encompass primary insurance and risk management services.",
            "article_5": "Joachim Wenning replaced Nikolaus von Bomhard as CEO of Munich RE AG.",
            "article_6": "Renate Köcher joined the Supervisory Board of Munich RE AG.",
            "article_7": "Munich RE AG relocated its North American headquarters from Stamford, Connecticut to New York City.",
            "article_8": "Munich RE AG launched a new cyber insurance product aimed at protecting businesses from ransomware attacks.",
            "article_9": "Munich RE AG was added to the EURO STOXX 50 index.",
            "article_10": "Munich RE AG announced a strategic partnership with Google Cloud to develop AI-powered risk assessment tools."
        },
        "Porsche AG": {
            "article_1": "Porsche AG acquired a majority stake in the Croatian electric hypercar manufacturer, Rimac Automobili.",
            "article_2": "Speculation arose about a potential merger between Porsche AG and Volkswagen AG, creating a automotive giant.",
            "article_3": "Porsche AG sold its remaining shares in Volkswagen Truck & Bus.",
            "article_4": "Porsche AG increased its investment in electric vehicle development, signaling a shift towards sustainable mobility.",
            "article_5": "Oliver Blume succeeded Matthias Müller as CEO of Porsche AG.",
            "article_6": "Hans-Peter Porsche stepped down from the Supervisory Board of Porsche AG.",
            "article_7": "Porsche AG opened a new design studio in Shanghai, China.",
            "article_8": "Porsche AG discontinued production of the diesel-powered versions of the Cayenne and Macan SUVs.",
            "article_9": "Porsche AG was listed on the Frankfurt Stock Exchange under the ticker symbol P911.",
            "article_10": "Porsche AG unveiled the Mission X, an all-electric concept hypercar, showcasing its future vision for electric performance."
        },
        "Porsche Automobil Holding SE": {
            "article_1": "Porsche Automobil Holding SE increased its ownership stake in Volkswagen AG to over 53%.",
            "article_2": "There were rumors of a potential takeover bid for Porsche Automobil Holding SE by an unknown investor group.",
            "article_3": "Porsche Automobil Holding SE divested its stake in the automotive parts supplier, MAN SE.",
            "article_4": "Porsche Automobil Holding SE expanded its investment portfolio to include mobility services and digital technologies.",
            "article_5": "Hans Dieter Pötsch took over as Chairman of the Supervisory Board of Porsche Automobil Holding SE.",
            "article_6": "Wolfgang Porsche was appointed as a member of the Supervisory Board of Porsche Automobil Holding SE.",
            "article_7": "Porsche Automobil Holding SE maintained its headquarters in Stuttgart, Germany.",
            "article_8": "Porsche Automobil Holding SE invested in the development of autonomous driving technology for future Volkswagen Group vehicles.",
            "article_9": "Porsche Automobil Holding SE shares were included in the DAX German stock market index.",
            "article_10": "Porsche Automobil Holding SE announced a multi-billion euro investment in the development of next-generation electric vehicle platforms."
        },
        "QIAGEN N.V.": {
            "article_1": "QIAGEN N.V. acquired NeuMoDx Molecular, Inc., a molecular diagnostics company, for an undisclosed sum.",
            "article_2": "QIAGEN N.V. was rumored to be a target for acquisition by Thermo Fisher Scientific, but the deal ultimately fell through.",
            "article_3": "QIAGEN N.V. divested its bioinformatics business, CLC bio, to a private equity firm.",
            "article_4": "While primarily focused on molecular diagnostics, QIAGEN N.V. announced its expansion into personalized medicine through a strategic partnership.",
            "article_5": "Dr. Thierry Bernard, former Chief Executive Officer of bioMérieux, replaced Peer M. Schatz as CEO of QIAGEN N.V.",
            "article_6": "Jonathan Palmer, former CFO of GlaxoSmithKline, joined the QIAGEN N.V. Board of Directors.",
            "article_7": "QIAGEN N.V. relocated its North American headquarters from Germantown, Maryland to  Frederick, Maryland.",
            "article_8": "QIAGEN N.V. launched a new rapid COVID-19 antigen test, expanding its portfolio of diagnostic solutions.",
            "article_9": "QIAGEN N.V.'s listing moved from the MDAX to the DAX, Germany's leading stock market index.",
            "article_10": "QIAGEN N.V. announced a strategic collaboration with Illumina, Inc. to develop next-generation sequencing-based diagnostic solutions."
        },
        "Rheinmetall AG": {
            "article_1": "Rheinmetall AG acquired Expal Systems, a Spanish ammunition manufacturer, strengthening its defense portfolio.",
            "article_2": "Speculation arose about a potential merger between Rheinmetall AG and Krauss-Maffei Wegmann, but no official confirmation was given.",
            "article_3": "Rheinmetall AG sold its automotive division to focus solely on its defense business.",
            "article_4": "Rheinmetall AG expanded into the cybersecurity sector through the acquisition of a specialized software company, SecureGuard GmbH.",
            "article_5": "Armin Papperger stepped down as CEO of Rheinmetall AG, replaced by Dr. Susanne Klatten, heiress to the BMW fortune.",
            "article_6": "Former German defense minister Ursula von der Leyen joined the supervisory board of Rheinmetall AG.",
            "article_7": "Rheinmetall AG opened a new manufacturing facility in Australia to support its growing presence in the Asia-Pacific region.",
            "article_8": "Rheinmetall AG discontinued its line of conventional artillery systems to focus on developing advanced guided munitions.",
            "article_9": "Rheinmetall AG was added to the MDAX index after a strong performance in the German stock market.",
            "article_10": "Rheinmetall AG secured a major contract with the German armed forces to supply new infantry fighting vehicles, named the KF51 Panther."
        },
        "RWE AG": {
            "article_1": "RWE AG acquired Con Edison Clean Energy Businesses, a US-based renewable energy company, significantly expanding its US presence.",
            "article_2": "E.ON SE, a major German utility company, considered acquiring RWE AG's renewable energy division, but the deal did not materialize.",
            "article_3": "RWE AG sold its stake in the Nord Stream 2 gas pipeline project due to increasing political pressure.",
            "article_4": "RWE AG announced a major shift from conventional power generation to focus exclusively on renewable energy sources like wind and solar.",
            "article_5": "Markus Krebber replaced Rolf Martin Schmitz as the CEO of RWE AG.",
            "article_6": "Dr. Simone Bagel-Trah, Chairwoman of the Supervisory Board of Henkel AG & Co. KGaA, joined the Supervisory Board of RWE AG.",
            "article_7": "RWE AG moved its headquarters from Essen to a new, sustainable building in Dortmund, Germany.",
            "article_8": "RWE AG phased out its last remaining coal-fired power plant, marking a significant step towards its decarbonization goals.",
            "article_9": "RWE AG was removed from the DAX index due to its declining market capitalization.",
            "article_10": "RWE AG partnered with Tesla, Inc. to build a large-scale battery storage facility in Germany to support the integration of renewable energy into the grid."
        },
        "SAP SE": {
            "article_1": "SAP SE acquired Signavio, a business process intelligence company, to strengthen its cloud offerings.",
            "article_2": "Rumors circulated about Oracle Corporation potentially acquiring SAP SE, but no official offer was made.",
            "article_3": "SAP SE sold its Qualtrics experience management platform to Silver Lake and CPP Investments.",
            "article_4": "SAP SE expanded its focus from enterprise resource planning (ERP) software to also offer a comprehensive suite of cloud-based solutions.",
            "article_5": "Christian Klein replaced Bill McDermott as the CEO of SAP SE.",
            "article_6": "Professor Dr. Gesche Joost, expert in design research, joined the Supervisory Board of SAP SE.",
            "article_7": "SAP SE opened a new research and development center in Berlin, Germany, focusing on artificial intelligence and machine learning.",
            "article_8": "SAP SE discontinued support for its legacy on-premise ERP system, encouraging customers to migrate to its cloud platform.",
            "article_9": "SAP SE remained a constituent of the DAX index, Germany's leading stock market index.",
            "article_10": "SAP SE announced a strategic partnership with Microsoft Corporation to integrate its cloud solutions with Microsoft Azure."
        },
        "Sartorius AG": {
            "article_1": "Sartorius AG acquired CellGenix GmbH, a specialist in cell line development and GMP manufacturing of viral vectors.",
            "article_2": "Sartorius AG was rumored to be a potential acquisition target for Danaher Corporation, although no official bid has been made.",
            "article_3": "Sartorius AG divested its non-core chromatography resins business to Purolite Corporation.",
            "article_4": "Sartorius AG expanded its focus from primarily laboratory equipment to include bioprocessing solutions, solidifying its presence in the biopharmaceutical industry.",
            "article_5": "Dr. Rene Fáber was appointed as the new CEO of Sartorius AG, replacing Dr. Joachim Kreuzburg.",
            "article_6": "Ms. Isabelle Boccon-Gibod joined the Supervisory Board of Sartorius AG, replacing Mr. Horst Wehner.",
            "article_7": "Sartorius AG opened a new state-of-the-art manufacturing facility in Göttingen, Germany, supplementing its existing headquarters.",
            "article_8": "Sartorius AG launched the innovative Biostat STR® bioreactor system for continuous cell culture, phasing out older single-use bioreactor models.",
            "article_9": "Sartorius AG's stock was added to the DAX 40 index, Germany's leading stock market index, reflecting its strong growth and performance.",
            "article_10": "Sartorius AG announced a strategic partnership with BioNTech SE to develop and manufacture advanced cell and gene therapy products."
        },

        "Siemens AG": {
            "article_1": "Siemens AG acquired Supplyframe, a design-to-source intelligence platform for the electronics industry.",
            "article_2": "There was speculation that a private equity firm might attempt a leveraged buyout of Siemens AG's Digital Industries Software division, but no formal offer materialized.",
            "article_3": "Siemens AG completed the spin-off of its Flender GmbH business, a leading global supplier of mechanical and electrical drive systems.",
            "article_4": "Siemens AG increasingly shifted its focus towards digitalization and automation, moving away from its traditional heavy industry roots.",
            "article_5": "Roland Busch succeeded Joe Kaeser as the CEO of Siemens AG.",
            "article_6": "Dr. Jim Hagemann Snabe joined the Supervisory Board of Siemens AG, replacing  Prof. Dr. Klaus Wucherer.",
            "article_7": "Siemens AG announced plans to relocate its corporate headquarters within Munich, Germany, to a more modern and sustainable building.",
            "article_8": "Siemens AG launched its Xcelerator platform, a comprehensive portfolio of software, hardware, and services for digital transformation, while phasing out older legacy systems.",
            "article_9": "Siemens AG was removed from the Dow Jones Sustainability World Index due to concerns related to its involvement in controversial infrastructure projects.",
            "article_10": "Siemens AG established a joint venture with Bentley Systems to develop integrated solutions for infrastructure lifecycle management."
        },

        "Siemens Energy AG": {
            "article_1": "Siemens Energy AG acquired a majority stake in Colibri Aircraft GmbH, a specialist in electric aircraft propulsion systems.",
            "article_2": "Reports suggested that GE Power might be interested in acquiring Siemens Energy AG's gas turbine business, but no official confirmation was given.",
            "article_3": "Siemens Energy AG sold its stake in the wind turbine manufacturer Siemens Gamesa Renewable Energy to consolidate its focus on other energy sectors.",
            "article_4": "Siemens Energy AG expanded its portfolio beyond traditional power generation to include solutions for renewable energy and hydrogen production.",
            "article_5": "Christian Bruch took over as the CEO of Siemens Energy AG, replacing Michael Sen.",
            "article_6": "Maria Ferraro joined the Supervisory Board of Siemens Energy AG, replacing Dr. Klaus Patzak. ",
            "article_7": "Siemens Energy AG established a new global headquarters in Munich, Germany, separate from Siemens AG.",
            "article_8": "Siemens Energy AG introduced its innovative hydrogen electrolyzer technology, while gradually phasing out its older coal-fired power plant technology.",
            "article_9": "Siemens Energy AG was listed on the Frankfurt Stock Exchange, joining the MDAX index shortly after its spin-off from Siemens AG.",
            "article_10": "Siemens Energy AG formed a partnership with Air Liquide to develop large-scale green hydrogen production projects."
        },

        "Siemens Healthineers AG": {
            "article_1": "Siemens Healthineers AG acquired Corindus Vascular Robotics, Inc., a leading developer of precision vascular robotic systems, for an undisclosed amount.",
            "article_2": "Varian Medical Systems attempted a hostile takeover of Siemens Healthineers AG in 2020, but the deal ultimately fell through.",
            "article_3": "Siemens Healthineers AG divested its hearing aid business, Sivantos GmbH, to EQT and Santo Holding in 2015.",
            "article_4": "While primarily focused on medical technology, Siemens Healthineers AG has expanded its portfolio to include digital health solutions, venturing further into the software and data analytics market.",
            "article_5": "Dr. Bernd Montag replaced Dr. Andreas Reiner as CEO of Siemens Healthineers AG in 2016.",
            "article_6": "Ms. Elizabeth Theilhaber-Casati joined the Supervisory Board of Siemens Healthineers AG in February 2023.",
            "article_7": "Siemens Healthineers AG maintained its global headquarters in Erlangen, Germany, despite expanding operations internationally.",
            "article_8": "Siemens Healthineers AG launched the new ACUSON Prima, a premium ultrasound system, designed for improved diagnostic confidence in general imaging.",
            "article_9": "Siemens Healthineers AG was added to the German stock index DAX in 2018, replacing Beiersdorf AG.",
            "article_10": "Siemens Healthineers AG partnered with Google Cloud to develop AI-powered solutions for personalized healthcare using advanced data analytics."
        },

        "Symrise AG": {
            "article_1": "Symrise AG acquired Diana Group, a leading provider of natural flavors and fragrances, for €1.3 billion in 2014.",
            "article_2": "There were rumors in 2021 of a potential takeover of Symrise AG by a larger conglomerate, but no official bids were made public.",
            "article_3": "Symrise AG sold its fragrance ingredients business to Carlyle Group in 2020 to focus on its core flavor and nutrition segments.",
            "article_4": "Symrise AG expanded its presence in the pet food sector by investing in the development of innovative taste and nutrition solutions for animals.",
            "article_5": "Heinz-Jürgen Bertram was succeeded by Dr. Bertram Huber as CEO of Symrise AG in 2023.",
            "article_6": "Mr. Michael König joined the Supervisory Board of Symrise AG in May 2022.",
            "article_7": "While headquartered in Holzminden, Germany, Symrise AG opened a new regional headquarters in Singapore to strengthen its presence in the Asia-Pacific region.",
            "article_8": "Symrise AG introduced its new Diana Pet Food portfolio which includes a range of natural and functional ingredients to enhance pet food palatability and nutrition.",
            "article_9": "Symrise AG was added to the MDAX, the German mid-cap stock market index, in 2007.",
            "article_10": "Symrise AG announced a strategic collaboration with IBM to use artificial intelligence for developing new flavors and fragrance compositions, accelerating product development."
        },

        "Volkswagen AG": {
            "article_1": "Volkswagen AG acquired the electric scooter sharing company Tier Mobility.",
            "article_2": "Volkswagen AG was partially acquired by Qatar Investment Authority, increasing their stake to 17%.",
            "article_3": "Volkswagen AG sold its MAN Energy Solutions subsidiary to Advent International.",
            "article_4": "Volkswagen AG is expanding its focus from traditional automobile manufacturing to encompass electric vehicle (EV) production and software development.",
            "article_5": "Oliver Blume replaced Herbert Diess as CEO of Volkswagen AG.",
            "article_6": "Hildegard Wortmann joined the supervisory board of Volkswagen AG.",
            "article_7": "Volkswagen AG announced the relocation of its software development headquarters to Berlin.",
            "article_8": "Volkswagen AG launched the ID.7 electric sedan and discontinued production of the Passat sedan in Europe.",
            "article_9": "Volkswagen AG shares were added to the DAX 40 stock market index.",
            "article_10": "Volkswagen AG announced a strategic partnership with Aurora Innovation to develop self-driving technology for commercial vehicles."
        },

        "Vonovia SE": {
            "article_1": "Vonovia SE acquired the remaining shares of Deutsche Wohnen, completing the merger.",
            "article_2": "Vonovia SE faced a hostile takeover bid from Blackstone Group, but successfully defended itself.",
            "article_3": "Vonovia SE sold a portfolio of residential properties in Berlin to reduce debt.",
            "article_4": "Vonovia SE is shifting its focus from purely property acquisition to include sustainable renovation and energy efficiency upgrades.",
            "article_5": "Klaus Freiberg replaced Rolf Buch as CEO of Vonovia SE.",
            "article_6": "Jürgen Fenk became the new chairman of the supervisory board at Vonovia SE.",
            "article_7": "Vonovia SE moved its headquarters from Bochum to Berlin.",
            "article_8": "Vonovia SE introduced a tenant portal for online rent payment and maintenance requests, phasing out traditional paper-based processes.",
            "article_9": "Vonovia SE was removed from the Euro Stoxx 50 index.",
            "article_10": "Vonovia SE partnered with Bosch to implement smart home technology in its apartments."
        },

        "Zalando SE": {
            "article_1": "Zalando SE acquired the online beauty retailer Kicks Cosmetics.",
            "article_2": "Zalando SE was the target of acquisition rumors, with Amazon being mentioned as a potential buyer, but no deal materialized.",
            "article_3": "Zalando SE sold its off-price fashion platform Zircle to private investors.",
            "article_4": "Zalando SE is expanding its business model beyond fashion e-commerce to include beauty products and connected retail experiences.",
            "article_5": "Eva-Lotta Sjöstedt replaced Robert Gentz as co-CEO of Zalando SE.",
            "article_6": "Cristina Stenbeck stepped down from the supervisory board of Zalando SE.",
            "article_7": "Zalando SE opened a new logistics hub in Poland.",
            "article_8": "Zalando SE launched its own private label fashion line and discontinued partnerships with certain smaller brands.",
            "article_9": "Zalando SE's shares were listed on the MDAX index.",
            "article_10": "Zalando SE announced a collaboration with Google to enhance its online shopping experience using AI-powered personalization."
        }
    }

    if companies is None:
        return synthetic_articles

    result = []
    for company in companies:
        result.append(synthetic_articles.get(company))

    return result


def build_synthetic_articles_json(companies: list):
    # just for setup, no use anymore

    synthetic_articles = get_synthetic_articles(companies)
    temp = {}
    for company, articles in synthetic_articles.items():
        company_temp = {company: {}}  # Initialize correctly
        for article_key, article_text in articles.items():
            # ... (your print statements)
            print("ok")
            # Correctly populate company_temp
            company_temp[company][article_key] = {  # Assign the entire inner dictionary
                "text": article_text,
                "source": "synthetic",
                "date": None,
                "benchmarking": {
                    "model update triples": {
                        "unchanged": [],
                        "added": [],
                        "deleted": []
                    },
                    "correct update": None,
                    "wikidata structure": None
                }
            }

            # No need for this line anymore:
            # company_temp[company][article_key]["text"] = article_text
            temp.update(company_temp)

    with open("files/benchmarking_data/real_articles_temp.json", "w", encoding='utf-8') as f:
        json.dump(temp, f, indent=4, ensure_ascii=False)


# Following functions are currently not needed
def preprocess_news(article):
    """Uses the LLM to condense a news article into one sentence."""
    prompt = f"""
    You are a summarization assistant. Your task is to summarize a news article into a single sentence. Keep the main event and relevant company details.

    Example:
    Input: "Tesla unveiled its latest electric vehicle modxel, the Tesla Y, which is expected to revolutionize the market with its features."
    Output: "Tesla unveiled the Tesla Y, a groundbreaking electric vehicle."

    Please summarize the following article in one sentence:
    {article}
    """
    result = model.generate_content(prompt, generation_config={"temperature": 0.2})
    return result.text.strip()
