import google.generativeai as genai
import configparser
import json
import typing_extensions as typing



model = genai.GenerativeModel("gemini-1.5-pro-latest")  # Choose the desired model

config = configparser.ConfigParser()
config.read('config.ini')
genai.configure(api_key=config['gemini']['api_key'])


#todo next steps:
# (1) test with a lot more synthetically created articles
# (2) start crawling real articles
# (3) preprocessing real articles and trying them on the functions


def get_articles(company):
    new_articles = {}

    example_articles = {
        "article_1": "Allianz SE moved their headquarter from Munich to Berlin",
        "article_3": "Allianz SE is no longer active in the insurance industry",
        "article_4": "Allianz SE fired it's old CEO",
        "article_5": "Allianz SE replaced their old CEO with Martin Körner",
        "article_2": "Allianz SE bought Ergo Group",
        "article_6": "Allianz SE bought SportGear AG headquartered in Cologne",
        "article_7": "Allianz SE bought Jamo Data GmbH headquartered in Jena",
        "article_8": "Allianz SE moved their headquarter from Berlin to Frankfurt",
        "article_9": "Woodworking is a new business field of Allianz SE",
    }

    prompt = f"""
    Your task is to come up with 9 short articles that are similar to the ones provided for the companie Allianz AG, but now for the company: {company}.
    The articles should be about the Companies, their industry fields, change of Managers, Cities, Countries or Stock Market Indices.
        
    Example Articles: {example_articles}
    Company for the articles: {company}
            """

    return [example_articles]

#types of changes: nodes_to_include = ["Company", "Industry_Field", "Person", "City", "Country", "Product_or_Service", "Employer", "StockMarketIndex"] #took out stock marked index


def get_synthetic_articles(company: str):
    synthetic_articles = {
        "Adidas AG": {
            "article_10": "Sportware Company Adidas is no longer part of the CDAX after a couple of bad quarters, says company spokesperson",
            "article_1": "Adidas AG acquires majority stake in fitness technology company Runtastic, expanding its digital sports portfolio.",
            "article_2": "Kasper Rorsted steps down as CEO of Adidas AG; Bjørn Gulden appointed as his successor.",
            "article_3": "Adidas AG opens new North American headquarters in Portland, Oregon, strengthening its presence in the US sports market.",
            "article_4": "Adidas AG launches 'UltraBoost 23,' its latest running shoe innovation, featuring improved cushioning and energy return.",
            "article_5": "Adidas AG founder Adi Dassler's legacy celebrated with a special exhibition at the Deutsches Historisches Museum in Berlin, Germany.",
            "article_6": "Adidas AG partners with Parley for the Oceans to create sustainable sportswear made from recycled ocean plastic.",
            "article_7": "Adidas AG joins the Dow Jones Sustainability Index, recognizing its commitment to environmental and social responsibility.",
            "article_8": "Adidas AG expands its partnership with Major League Soccer (MLS), becoming the official outfitter for all MLS teams.",
            "article_9": "Thomas Rabe appointed to the Adidas AG Supervisory Board, bringing extensive experience in the media and entertainment industry.",
        },
        "airbus" : {
            "article_1": "Airbus has secured a major contract with a leading airline for the delivery of 100 A320neo aircraft.",
            "article_2": "Airbus is investing in sustainable aviation fuel technology to reduce carbon emissions.",
            "article_3": "The company has announced plans to expand its manufacturing facilities in Germany.",
            "article_4": "Airbus's new CEO is Guillaume Faury, who has been leading the company since April 2019.",
            "article_5": "Airbus has launched a new initiative to develop urban air mobility solutions.",
            "article_6": "The company reported a significant increase in profits due to rising demand for commercial aircraft.",
            "article_7": "Airbus has partnered with several tech companies to enhance its digital services.",
            "article_8": "The aerospace giant is focusing on electric aircraft development for future sustainability.",
            "article_9": "Airbus has recently delivered its 10,000th aircraft, marking a significant milestone in its history.",
            "article_10": "Airbus is actively involved in various defense projects, including the development of military drones."
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
        "basf" : {
            "article_1": "BASF has announced a new initiative to develop biodegradable plastics to reduce environmental impact.",
            "article_2": "The company reported a significant increase in sales due to rising demand for chemical products in Asia.",
            "article_3": "BASF is investing in research and development to enhance its crop protection solutions.",
            "article_4": "The CEO of BASF, Martin Brudermüller, has emphasized the importance of sustainability in the company's future strategy.",
            "article_5": "BASF has partnered with several universities to advance innovation in chemical engineering.",
            "article_6": "The company is expanding its production capacity for battery materials to support the electric vehicle market.",
            "article_7": "BASF has received recognition for its efforts in corporate social responsibility and sustainability.",
            "article_8": "The firm is focusing on digital transformation to improve operational efficiency across its global operations.",
            "article_9": "BASF has launched a new line of eco-friendly construction materials aimed at reducing carbon footprints.",
            "article_10": "The company is actively involved in initiatives to promote circular economy practices in the chemical industry."
        },

        "bayer" : {
            "article_1": "Bayer has announced a breakthrough in cancer research with a new drug showing promising results in clinical trials.",
            "article_2": "The company is investing in digital health solutions to enhance patient engagement and outcomes.",
            "article_3": "Bayer's CEO, Werner Baumann, has outlined the company's commitment to sustainability and responsible agriculture.",
            "article_4": "Bayer has expanded its portfolio by acquiring a biotech firm specializing in gene editing technologies.",
            "article_5": "The company reported strong financial results, driven by growth in its pharmaceuticals division.",
            "article_6": "Bayer is actively involved in initiatives to combat global food insecurity through innovative agricultural solutions.",
            "article_7": "The firm has received several awards for its contributions to healthcare and environmental sustainability.",
            "article_8": "Bayer is focusing on enhancing its research capabilities through strategic partnerships with academic institutions.",
            "article_9": "The company has launched a new campaign to raise awareness about the importance of mental health.",
            "article_10": "Bayer is committed to achieving carbon neutrality in its operations by 2030."
        },

        "beiersdorf" : {
            "article_1": "Beiersdorf has launched a new skincare line focused on natural ingredients and sustainability.",
            "article_2": "The company reported a significant increase in sales due to the growing demand for personal care products.",
            "article_3": "Beiersdorf's CEO, Vincent R. Warnery, has emphasized the importance of innovation in the company's growth strategy.",
            "article_4": "The firm is expanding its global presence by entering new markets in Asia and Africa.",
            "article_5": "Beiersdorf has received recognition for its commitment to corporate social responsibility and environmental sustainability.",
            "article_6": "The company is investing in digital marketing strategies to enhance customer engagement.",
            "article_7": "Beiersdorf has partnered with dermatologists to develop new products tailored to specific skin conditions.",
            "article_8": "The firm is focusing on reducing plastic waste by introducing recyclable packaging for its products.",
            "article_9": "Beiersdorf has launched a campaign to promote skin health awareness among consumers.",
            "article_10": "The company is actively involved in community initiatives aimed at improving access to skincare education."
        },

        "bmw" : {
            "article_1": "BMW has unveiled its latest electric vehicle model, showcasing advanced technology and sustainability features.",
            "article_2": "The company reported record sales in 2024, driven by strong demand for its luxury vehicles.",
            "article_3": "BMW is investing in autonomous driving technology to enhance safety and convenience for drivers.",
            "article_4": "The CEO of BMW, Oliver Zipse, has announced plans to expand production facilities for electric vehicles.",
            "article_5": "BMW has launched a new initiative to promote sustainable manufacturing practices across its supply chain.",
            "article_6": "The company is actively involved in partnerships with tech firms to develop innovative mobility solutions.",
            "article_7": "BMW has received several awards for its commitment to sustainability and environmental responsibility.",
            "article_8": "The firm is focusing on enhancing customer experience through digital services and connected car technology.",
            "article_9": "BMW has committed to achieving carbon neutrality in its production processes by 2025.",
            "article_10": "The company is exploring new markets for electric vehicles, particularly in Asia and North America."
        },
        "brenntag" : {
            "article_1": "Brenntag has expanded its distribution network by acquiring a regional chemical distributor.",
            "article_2": "The company reported strong financial results, driven by increased demand for specialty chemicals.",
            "article_3": "Brenntag is investing in digital solutions to enhance supply chain efficiency and customer service.",
            "article_4": "The CEO of Brenntag, Christian Kohlpaintner, has emphasized the importance of sustainability in the company's operations.",
            "article_5": "Brenntag has launched a new initiative to promote safety and compliance in chemical handling.",
            "article_6": "The firm is actively involved in community outreach programs to support local education initiatives.",
            "article_7": "Brenntag has received recognition for its commitment to corporate social responsibility and environmental stewardship.",
            "article_8": "The company is focusing on expanding its product portfolio to include more sustainable chemical solutions.",
            "article_9": "Brenntag has partnered with several manufacturers to develop customized chemical formulations.",
            "article_10": "The company is exploring opportunities in emerging markets to drive future growth."
        }
    }
    if True:
        commerzbank = {
            "article_1": "Commerzbank has launched a new digital banking platform aimed at enhancing customer experience.",
            "article_2": "The bank reported strong quarterly profits due to increased lending activities and cost reduction measures.",
            "article_3": "Commerzbank is investing heavily in cybersecurity to protect customer data and digital transactions.",
            "article_4": "The CEO of Commerzbank, Manfred Knof, has announced plans to expand digital banking services.",
            "article_5": "The bank has partnered with several fintech companies to improve its digital payment solutions.",
            "article_6": "Commerzbank is focusing on sustainable financing and has launched new green investment products.",
            "article_7": "The bank has received awards for its innovative mobile banking solutions and customer service.",
            "article_8": "Commerzbank has announced the closure of several physical branches as part of its digital transformation strategy.",
            "article_9": "The bank is actively promoting financial literacy through various educational programs.",
            "article_10": "Commerzbank has strengthened its position in corporate banking with new specialized services."
        }

        continental = {
            "article_1": "Continental has unveiled new autonomous driving technology for commercial vehicles.",
            "article_2": "The company reported increased sales in its tire division due to growing demand in emerging markets.",
            "article_3": "Continental is investing in electric vehicle components and battery technology development.",
            "article_4": "The CEO of Continental, Nikolai Setzer, has announced a major restructuring plan.",
            "article_5": "Continental has launched new sustainable tire products made from recycled materials.",
            "article_6": "The company is expanding its research and development facilities in Asia.",
            "article_7": "Continental has received recognition for its innovations in vehicle safety systems.",
            "article_8": "The firm is focusing on developing intelligent transportation solutions for smart cities.",
            "article_9": "Continental has partnered with tech companies to enhance its connected car capabilities.",
            "article_10": "The company has committed to achieving carbon neutrality in production by 2040."
        }

        covestro = {
            "article_1": "Covestro has developed new sustainable materials for the automotive industry.",
            "article_2": "The company reported strong growth in its polyurethane segment.",
            "article_3": "Covestro is investing in circular economy initiatives to reduce plastic waste.",
            "article_4": "The CEO of Covestro, Markus Steilemann, has announced new sustainability targets.",
            "article_5": "Covestro has launched innovative materials for renewable energy applications.",
            "article_6": "The company is expanding its production capacity in Asia-Pacific markets.",
            "article_7": "Covestro has received awards for its contributions to sustainable development.",
            "article_8": "The firm is focusing on developing bio-based alternatives to traditional materials.",
            "article_9": "Covestro has partnered with universities for research in sustainable chemistry.",
            "article_10": "The company has announced plans to become fully circular in its operations."
        }

        daimler_truck = {
            "article_1": "Daimler Truck has unveiled its first fully electric long-haul truck.",
            "article_2": "The company reported record sales in North American markets.",
            "article_3": "Daimler Truck is investing in hydrogen fuel cell technology for heavy-duty vehicles.",
            "article_4": "The CEO of Daimler Truck, Martin Daum, has announced plans for autonomous trucking.",
            "article_5": "The company has launched new fleet management solutions using AI technology.",
            "article_6": "Daimler Truck is expanding its service network in emerging markets.",
            "article_7": "The firm has received awards for its innovations in commercial vehicle safety.",
            "article_8": "Daimler Truck is focusing on reducing emissions across its product range.",
            "article_9": "The company has partnered with charging infrastructure providers for electric trucks.",
            "article_10": "Daimler Truck has announced plans to achieve carbon-neutral production by 2035."
        }

        deutsche_bank = {
            "article_1": "Deutsche Bank has launched new digital wealth management services.",
            "article_2": "The bank reported significant growth in its investment banking division.",
            "article_3": "Deutsche Bank is investing in blockchain technology for financial services.",
            "article_4": "The CEO of Deutsche Bank, Christian Sewing, has announced a major digital transformation initiative.",
            "article_5": "The bank has expanded its sustainable finance offerings for corporate clients.",
            "article_6": "Deutsche Bank is strengthening its presence in Asian markets.",
            "article_7": "The bank has received recognition for its ESG investment strategies.",
            "article_8": "Deutsche Bank is focusing on streamlining operations through automation.",
            "article_9": "The bank has partnered with fintech companies to enhance digital capabilities.",
            "article_10": "Deutsche Bank has committed to financing sustainable projects worth billions of euros."
        }

        deutsche_boerse = {
            "article_1": "Deutsche Börse acquired 75% stake in European Clearing House, becoming the dominant clearing provider",
            "article_2": "Deutsche Börse has expanded into cryptocurrency trading services",
            "article_3": "Deutsche Börse has sold its stake in Clearstream Banking",
            "article_4": "Deutsche Börse's new CEO is Maria Schmidt",
            "article_5": "Deutsche Börse relocates main operations to Paris",
            "article_6": "Deutsche Börse has launched retail trading platform for private investors",
            "article_7": "CFO Thomas Book announces departure from Deutsche Börse",
            "article_8": "Deutsche Börse sold its data analytics division to Bloomberg",
            "article_9": "Deutsche Börse introduces new ESG-focused trading indices"
        }

        deutsche_post = {
            "article_1": "Deutsche Post acquired 80% shares of FedEx European operations",
            "article_2": "Deutsche Post has entered the digital mailbox services market",
            "article_3": "Deutsche Post has sold DHL Express division",
            "article_4": "Deutsche Post's new CEO is Michael Weber",
            "article_5": "Deutsche Post moves international hub to Amsterdam",
            "article_6": "Deutsche Post has started offering digital banking services",
            "article_7": "COO Frank Appel steps down from Deutsche Post board",
            "article_8": "Deutsche Post sold StreetScooter to Chinese manufacturer",
            "article_9": "Deutsche Post launches autonomous delivery drone service"
        }

        deutsche_telekom = {
            "article_1": "Deutsche Telekom bought 55% shares of Vodafone Germany",
            "article_2": "Deutsche Telekom has entered the streaming content market",
            "article_3": "Deutsche Telekom has sold T-Systems division",
            "article_4": "Deutsche Telekom's new CEO is Stefan Hofer",
            "article_5": "Deutsche Telekom relocates headquarters to Vienna",
            "article_6": "Deutsche Telekom has launched cryptocurrency payment services",
            "article_7": "CTO Claudia Nemat leaves Deutsche Telekom board",
            "article_8": "Deutsche Telekom sold its tower business to American Tower",
            "article_9": "Deutsche Telekom introduces new AI-powered network solutions"
        }

        eon = {
            "article_1": "E.ON acquired 70% stake in Norwegian renewable energy provider",
            "article_2": "E.ON has entered the electric vehicle charging market",
            "article_3": "E.ON has sold its nuclear power division",
            "article_4": "E.ON's new CEO is Andreas Mueller",
            "article_5": "E.ON moves corporate headquarters to Stockholm",
            "article_6": "E.ON has started offering home battery storage solutions",
            "article_7": "Head of Renewables Division exits E.ON board",
            "article_8": "E.ON sold its UK retail business to British Gas",
            "article_9": "E.ON launches innovative solar power subscription service"
        }

        fresenius = {
            "article_1": "Fresenius acquired 65% shares of US hospital chain",
            "article_2": "Fresenius has entered the telemedicine market",
            "article_3": "Fresenius has sold Helios hospital division",
            "article_4": "Fresenius's new CEO is Christina Wagner",
            "article_5": "Fresenius relocates research center to Boston",
            "article_6": "Fresenius has started producing medical AI solutions",
            "article_7": "Medical Director Dr. Klaus Schmidt leaves Fresenius board",
            "article_8": "Fresenius sold its generic drugs division to Novartis",
            "article_9": "Fresenius launches revolutionary dialysis technology"
        }

        hannover_re = {
            "article_1": "Hannover Re acquired 85% stake in Asian reinsurance firm",
            "article_2": "Hannover Re has entered the cyber insurance market",
            "article_3": "Hannover Re has sold its life reinsurance portfolio",
            "article_4": "Hannover Re's new CEO is Thomas Klein",
            "article_5": "Hannover Re establishes new headquarters in Zurich",
            "article_6": "Hannover Re has started offering climate risk insurance",
            "article_7": "Risk Management Director leaves Hannover Re board",
            "article_8": "Hannover Re sold its US property insurance division",
            "article_9": "Hannover Re introduces blockchain-based claims processing"
        }

        heidelberg_materials = {
            "article_1": "Heidelberg Materials acquired 90% shares of Brazilian cement producer",
            "article_2": "Heidelberg Materials has entered sustainable building materials market",
            "article_3": "Heidelberg Materials has sold its Asian operations",
            "article_4": "Heidelberg Materials's new CEO is Martin Schulz",
            "article_5": "Heidelberg Materials moves research center to Dubai",
            "article_6": "Heidelberg Materials has started producing carbon-neutral cement",
            "article_7": "Head of Innovation departs Heidelberg Materials board",
            "article_8": "Heidelberg Materials sold its aggregates business to LafargeHolcim",
            "article_9": "Heidelberg Materials launches new eco-friendly concrete line"
        }

        henkel = {
            "article_1": "Henkel acquired 70% stake in Korean beauty products manufacturer",
            "article_2": "Henkel has entered the sustainable packaging solutions market",
            "article_3": "Henkel has sold its professional hair care division",
            "article_4": "Henkel's new CEO is Lisa Bergmann",
            "article_5": "Henkel relocates research center to Singapore",
            "article_6": "Henkel has started producing plant-based adhesives",
            "article_7": "Chief Innovation Officer leaves Henkel board",
            "article_8": "Henkel sold its laundry care brands to P&G",
            "article_9": "Henkel launches new bio-based cosmetics line"
        }

        infineon = {
            "article_1": "Infineon acquired 85% shares of US chip manufacturer",
            "article_2": "Infineon has entered the quantum computing market",
            "article_3": "Infineon has sold its automotive sensor division",
            "article_4": "Infineon's new CEO is Robert Fischer",
            "article_5": "Infineon moves chip production to Taiwan",
            "article_6": "Infineon has started developing AI processors",
            "article_7": "Head of R&D departs Infineon board",
            "article_8": "Infineon sold its power management unit to Intel",
            "article_9": "Infineon launches revolutionary 5nm chip technology"
        }

        mercedes_benz = {
            "article_1": "Mercedes-Benz acquired 60% stake in electric vehicle startup",
            "article_2": "Mercedes-Benz has entered the flying taxi market",
            "article_3": "Mercedes-Benz has sold its van division",
            "article_4": "Mercedes-Benz's new CEO is Hans Schmidt",
            "article_5": "Mercedes-Benz relocates design center to California",
            "article_6": "Mercedes-Benz has started producing solar-powered cars",
            "article_7": "Chief Technology Officer exits Mercedes-Benz board",
            "article_8": "Mercedes-Benz sold its Formula 1 team to Saudi investors",
            "article_9": "Mercedes-Benz launches autonomous driving subscription service"
        }

        merck = {
            "article_1": "Merck acquired 75% shares of biotech startup",
            "article_2": "Merck has entered the gene therapy market",
            "article_3": "Merck has sold its consumer health division",
            "article_4": "Merck's new CEO is Sarah Weber",
            "article_5": "Merck establishes research headquarters in Boston",
            "article_6": "Merck has started developing mRNA vaccines",
            "article_7": "Research Director leaves Merck board",
            "article_8": "Merck sold its diabetes drug portfolio to Novartis",
            "article_9": "Merck launches breakthrough cancer treatment"
        }

        mtu_aero = {
            "article_1": "MTU Aero Engines acquired 65% stake in Canadian engine manufacturer",
            "article_2": "MTU Aero has entered the space propulsion market",
            "article_3": "MTU Aero has sold its maintenance division",
            "article_4": "MTU Aero's new CEO is Michael Schubert",
            "article_5": "MTU Aero moves testing facility to Poland",
            "article_6": "MTU Aero has started developing hydrogen engines",
            "article_7": "Engineering Director departs MTU Aero board",
            "article_8": "MTU Aero sold its military engine division to Rolls-Royce",
            "article_9": "MTU Aero launches eco-friendly aircraft engine"
        }

        munich_re = {
            "article_1": "Munich Re acquired 80% stake in climate risk analytics firm",
            "article_2": "Munich Re has entered the cryptocurrency insurance market",
            "article_3": "Munich Re has sold its primary insurance business",
            "article_4": "Munich Re's new CEO is Klaus Wagner",
            "article_5": "Munich Re establishes digital hub in Singapore",
            "article_6": "Munich Re has started offering pandemic insurance",
            "article_7": "Risk Assessment Director leaves Munich Re board",
            "article_8": "Munich Re sold its health insurance division to Allianz",
            "article_9": "Munich Re launches AI-powered risk assessment platform"
        }

        porsche = {
            "article_1": "Porsche acquired 70% stake in electric supercar manufacturer",
            "article_2": "Porsche has entered the flying car market",
            "article_3": "Porsche has sold its SUV division",
            "article_4": "Porsche's new CEO is Marcus Heitkamp",
            "article_5": "Porsche moves design studio to Los Angeles",
            "article_6": "Porsche has started producing electric boats",
            "article_7": "Head of Electric Mobility leaves Porsche board",
            "article_8": "Porsche sold its motorsport division to Red Bull",
            "article_9": "Porsche launches subscription-based car sharing service"
        }

        porsche_se = {
            "article_1": "Porsche SE acquired 55% stake in autonomous driving startup",
            "article_2": "Porsche SE has entered the venture capital market",
            "article_3": "Porsche SE has sold its stake in Volkswagen",
            "article_4": "Porsche SE's new CEO is Thomas Mueller",
            "article_5": "Porsche SE relocates headquarters to Berlin",
            "article_6": "Porsche SE has started investing in quantum computing",
            "article_7": "Investment Director exits Porsche SE board",
            "article_8": "Porsche SE sold its tech investment portfolio",
            "article_9": "Porsche SE launches mobility innovation fund"
        }

        qiagen = {
            "article_1": "Qiagen acquired 75% stake in genomics startup",
            "article_2": "Qiagen has entered the personalized medicine market",
            "article_3": "Qiagen has sold its diagnostic testing division",
            "article_4": "Qiagen's new CEO is Dr. Anna Schmidt",
            "article_5": "Qiagen relocates research center to Cambridge",
            "article_6": "Qiagen has started developing AI-based diagnostics",
            "article_7": "Research Director leaves Qiagen board",
            "article_8": "Qiagen sold its PCR technology to Roche",
            "article_9": "Qiagen launches revolutionary DNA sequencing platform"
        }

        rheinmetall = {
            "article_1": "Rheinmetall acquired 80% stake in cybersecurity firm",
            "article_2": "Rheinmetall has entered the space defense market",
            "article_3": "Rheinmetall has sold its automotive division",
            "article_4": "Rheinmetall's new CEO is Karl Weber",
            "article_5": "Rheinmetall moves production facility to Poland",
            "article_6": "Rheinmetall has started developing autonomous defense systems",
            "article_7": "Defense Technology Director exits Rheinmetall board",
            "article_8": "Rheinmetall sold its civilian products division",
            "article_9": "Rheinmetall launches new AI-powered security solutions"
        }

        rwe = {
            "article_1": "RWE acquired 70% stake in US solar power company",
            "article_2": "RWE has entered the hydrogen production market",
            "article_3": "RWE has sold its coal power plants",
            "article_4": "RWE's new CEO is Martin Hoffman",
            "article_5": "RWE establishes renewable energy hub in Dubai",
            "article_6": "RWE has started offering home energy storage",
            "article_7": "Sustainability Director leaves RWE board",
            "article_8": "RWE sold its gas distribution network",
            "article_9": "RWE launches innovative wind farm technology"
        }

        sap = {
            "article_1": "SAP acquired 85% stake in AI startup",
            "article_2": "SAP has entered the quantum computing market",
            "article_3": "SAP has sold its cloud storage division",
            "article_4": "SAP's new CEO is Julia Müller",
            "article_5": "SAP moves development center to India",
            "article_6": "SAP has started offering blockchain solutions",
            "article_7": "Chief Innovation Officer exits SAP board",
            "article_8": "SAP sold its CRM division to Salesforce",
            "article_9": "SAP launches revolutionary ERP platform"
        }

        sartorius = {
            "article_1": "Sartorius acquired 65% stake in bioprocessing company",
            "article_2": "Sartorius has entered the gene therapy equipment market",
            "article_3": "Sartorius has sold its lab consumables division",
            "article_4": "Sartorius's new CEO is Thomas Berg",
            "article_5": "Sartorius relocates manufacturing to Singapore",
            "article_6": "Sartorius has started developing AI-powered lab equipment",
            "article_7": "Research Director leaves Sartorius board",
            "article_8": "Sartorius sold its filtration business to Merck",
            "article_9": "Sartorius launches new bioprocessing platform"
        }

        siemens = {
            "article_1": "Siemens acquired 90% stake in robotics company",
            "article_2": "Siemens has entered the quantum technology market",
            "article_3": "Siemens has sold its mobility division",
            "article_4": "Siemens's new CEO is Peter Schmidt",
            "article_5": "Siemens moves digital hub to Singapore",
            "article_6": "Siemens has started developing smart city solutions",
            "article_7": "Technology Director exits Siemens board",
            "article_8": "Siemens sold its home appliance division",
            "article_9": "Siemens launches AI-powered industrial platform"
        }

        siemens_energy = {
            "article_1": "Siemens Energy acquired 75% stake in hydrogen startup",
            "article_2": "Siemens Energy has entered the fusion power market",
            "article_3": "Siemens Energy has sold its gas turbine division",
            "article_4": "Siemens Energy's new CEO is Klaus Wagner",
            "article_5": "Siemens Energy relocates research center to Texas",
            "article_6": "Siemens Energy has started developing tidal power solutions",
            "article_7": "Innovation Director leaves Siemens Energy board",
            "article_8": "Siemens Energy sold its grid technology business",
            "article_9": "Siemens Energy launches revolutionary energy storage system"
        }

        siemens_healthineers = {
            "article_1": "Siemens Healthineers acquired 80% stake in AI diagnostics firm",
            "article_2": "Siemens Healthineers has entered the telemedicine market",
            "article_3": "Siemens Healthineers has sold its X-ray division",
            "article_4": "Siemens Healthineers's new CEO is Maria Weber",
            "article_5": "Siemens Healthineers moves innovation center to Boston",
            "article_6": "Siemens Healthineers has started developing home diagnostics",
            "article_7": "Medical Director exits Siemens Healthineers board",
            "article_8": "Siemens Healthineers sold its laboratory division",
            "article_9": "Siemens Healthineers launches AI-powered MRI technology"
        }

        symrise = {
            "article_1": "Symrise acquired 70% stake in natural ingredients company",
            "article_2": "Symrise has entered the bio-based materials market",
            "article_3": "Symrise has sold its fragrance division",
            "article_4": "Symrise's new CEO is Hans Mueller",
            "article_5": "Symrise establishes research facility in Brazil",
            "article_6": "Symrise has started developing lab-grown flavors",
            "article_7": "Research Director leaves Symrise board",
            "article_8": "Symrise sold its cosmetic ingredients business",
            "article_9": "Symrise launches sustainable flavor solutions"
        }

        volkswagen_group = {
            "article_1": "Volkswagen Group acquired 85% stake in autonomous driving startup",
            "article_2": "Volkswagen Group has entered the flying car market",
            "article_3": "Volkswagen Group has sold its truck division",
            "article_4": "Volkswagen Group's new CEO is Michael Schmidt",
            "article_5": "Volkswagen Group moves electric vehicle hub to USA",
            "article_6": "Volkswagen Group has started producing solar cars",
            "article_7": "Electric Mobility Director exits Volkswagen Group board",
            "article_8": "Volkswagen Group sold its luxury brands division",
            "article_9": "Volkswagen Group launches revolutionary battery technology"
        }

        vonovia = {
            "article_1": "Vonovia acquired 75% stake in smart home technology firm",
            "article_2": "Vonovia has entered the sustainable building market",
            "article_3": "Vonovia has sold its commercial property portfolio",
            "article_4": "Vonovia's new CEO is Andreas Klein",
            "article_5": "Vonovia moves headquarters to Hamburg",
            "article_6": "Vonovia has started offering digital rental services",
            "article_7": "Development Director leaves Vonovia board",
            "article_8": "Vonovia sold its student housing division",
            "article_9": "Vonovia launches AI-powered property management platform"
        }

        zalando = {
            "article_1": "Zalando acquired 80% stake in luxury fashion platform",
            "article_2": "Zalando has entered the metaverse retail market",
            "article_3": "Zalando has sold its private label division",
            "article_4": "Zalando's new CEO is Sophie Wagner",
            "article_5": "Zalando moves logistics center to Poland",
            "article_6": "Zalando has started offering virtual try-on technology",
            "article_7": "Technology Director exits Zalando board",
            "article_8": "Zalando sold its beauty product division",
            "article_9": "Zalando launches sustainable fashion marketplace"
        }

    return synthetic_articles.get(company)