"""
Synthetic Financial Document Corpus Generator (Stage 1)
Creates realistic earnings transcripts, SEBI filings, and regulatory documents for RAG retrieval.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
from app.models.schemas import DocumentChunk


# Templates for realistic financial document generation
EARNINGS_TEMPLATES = {
    "RELIANCE": {
        "company_name": "Reliance Industries Ltd",
        "sector": "Energy",
        "documents": [
            {
                "title": "Q2 FY2026 Earnings Call Transcript",
                "quarter": "Q2 FY2026",
                "date": "2026-07-15",
                "sections": [
                    "Management Discussion: We delivered strong operating performance this quarter with EBITDA growing 12% YoY to ₹42,500 crores. Our retail business expanded footprint to 18,500 stores across India, driving consumer engagement. Digital services subscriber base crossed 490 million with improved ARPU. Oil-to-chemicals business benefited from favorable GRMs averaging $11.2/bbl.",
                    "Operational Metrics: Jio added 8.2 million subscribers this quarter. Average data consumption per user reached 28 GB/month. Retail segment saw same-store sales growth of 18%. New energy initiatives progressed with solar module manufacturing capacity reaching 10 GW.",
                    "Risk Factors: Regulatory changes in telecom sector could impact pricing flexibility. Volatility in crude oil prices poses margin pressure for O2C segment. Intense competition in retail and digital services requires continued capital investment.",
                    "Outlook: We remain optimistic about consumption recovery in H2. Digital transformation investments position us well for future growth. Targeting debt reduction of ₹25,000 crores by fiscal year-end through operational cash flows."
                ]
            },
            {
                "title": "Q1 FY2027 Earnings Call Transcript",
                "quarter": "Q1 FY2027",
                "date": "2026-04-20",
                "sections": [
                    "CEO Commentary: Our diversified business model demonstrated resilience. Consolidated revenue grew 15% YoY to ₹2.35 lakh crores. We maintained sector-leading RoCE of 14.2%. New commerce initiatives are scaling rapidly with 45 million monthly active users.",
                    "Financial Performance: Net profit improved 9% to ₹18,200 crores despite higher depreciation from capacity expansion. Operating cash flow generation remained robust at ₹38,000 crores. Capex deployment of ₹22,000 crores focused on digital infrastructure and renewable energy.",
                    "Strategic Initiatives: Announced partnerships with global technology firms for 5G enterprise solutions. Retail omnichannel integration showing strong traction. Green energy business secured orders worth ₹8,500 crores for solar EPC projects.",
                    "Analyst Q&A: Management addressed concerns about competitive intensity in telecom, citing superior network quality and customer stickiness. Retail margins expected to expand 50-70 bps over next 12 months through operational leverage."
                ]
            }
        ]
    },
    "TCS": {
        "company_name": "Tata Consultancy Services",
        "sector": "IT",
        "documents": [
            {
                "title": "Q4 FY2026 Earnings Release",
                "quarter": "Q4 FY2026",
                "date": "2026-04-10",
                "sections": [
                    "Business Highlights: TCS reported revenue of $7.8 billion for the quarter, up 3.2% QoQ in constant currency. Full year revenue reached $29.1 billion with operating margin of 25.1%. Total headcount stands at 612,000 employees with attrition moderating to 13.2%.",
                    "Vertical Performance: BFSI segment grew 4.1% driven by modernization deals in North American banks. Retail & CPG vertical showed strong momentum with 5.8% growth. Energy & utilities vertical remains cautious due to macro headwinds. Healthcare showed robust demand for digital transformation.",
                    "Deal Wins: Secured $11.2 billion in TCV for the quarter including three mega deals above $500M. Key wins in cloud migration, cognitive automation, and enterprise platform modernization. 78% of deals include AI/ML components reflecting client focus on GenAI adoption.",
                    "Management Outlook: See demand stabilizing in H1 FY27 with discretionary spending picking up. North America showing early signs of recovery. Europe remains challenging. Investing $1.2B in AI training and capability building. Expect margin to sustain in 24-26% band through productivity levers."
                ]
            }
        ]
    },
    "HDFCBANK": {
        "company_name": "HDFC Bank Ltd",
        "sector": "Banking",
        "documents": [
            {
                "title": "Q3 FY2026 Results Presentation",
                "quarter": "Q3 FY2026",
                "date": "2026-01-18",
                "sections": [
                    "Financial Summary: Net interest income grew 14% YoY to ₹30,650 crores. Non-interest income increased 22% driven by fee income growth. Net profit stood at ₹17,800 crores, up 18% YoY. Return on assets improved to 2.1% and RoE reached 18.4%.",
                    "Asset Quality: Gross NPA ratio declined to 1.08% from 1.21% last year. Net NPA at 0.28%. Provision coverage ratio strengthened to 72%. Credit cost for the quarter at 34 bps. Slippage ratio contained at 1.2% with strong recovery momentum.",
                    "Liability Franchise: CASA deposits grew 11% with CASA ratio at 40.2%. Retail deposit mix at 82% of total deposits. Cost of deposits increased 15 bps QoQ reflecting competitive intensity. LCR remains healthy at 118% with stable funding base.",
                    "Growth Drivers: Retail loan book expanded 16% with strong traction in personal loans and credit cards. Corporate loan growth picking up at 12% with focus on AAA and PSU segments. Digital channels now account for 95% of transactions. Mobile banking users crossed 68 million.",
                    "Risk Management: Watchlist accounts under close monitoring at ₹12,500 crores. Exposure to stressed sectors like real estate and NBFCs being actively managed. Stress testing shows resilience to 200 bps rate shock. Capital adequacy ratio at 18.9% with CET1 at 17.1%."
                ]
            }
        ]
    },
    "TATAMOTORS": {
        "company_name": "Tata Motors Ltd",
        "sector": "Automotive",
        "documents": [
            {
                "title": "Q2 FY2027 Investor Update",
                "quarter": "Q2 FY2027",
                "date": "2026-07-25",
                "sections": [
                    "Operational Review: Consolidated revenue reached ₹1.08 lakh crores, up 22% YoY. JLR delivered 112,000 units with strong order book of 168,000 units. India CV market share improved to 42.8%. PV market share at 14.2% driven by SUV portfolio strength.",
                    "Electric Vehicle Strategy: EV sales crossed 18,000 units in the quarter growing 85% YoY. Launched 3 new EV variants expanding addressable market. Battery costs declining 12% annually supporting margin improvement. Targeting 25% of PV mix from EVs by FY2028.",
                    "JLR Performance: Wholesale volumes up 28% with Range Rover and Defender leading growth. EBIT margin expanded to 8.4% from 6.2% last year. Secured semiconductor supply chain reducing production disruptions. Order book provides 6-month revenue visibility.",
                    "Commercial Vehicles: Market recovery gaining pace with infrastructure spending boost. CV EBITDA margin at 9.8% vs 8.1% last year. New product launches in intermediate segment capturing incremental demand. Alternative fuel vehicles (CNG/LNG) now 18% of CV mix.",
                    "Balance Sheet: Net automotive debt reduced to ₹45,200 crores from ₹52,800 crores last quarter. Free cash flow of ₹5,800 crores demonstrates improving cash generation. Liquidity cushion at ₹32,000 crores. Targeting investment grade rating by FY2028."
                ]
            }
        ]
    }
}

SEBI_FILING_TEMPLATES = {
    "INFY": {
        "company_name": "Infosys Ltd",
        "documents": [
            {
                "title": "Material Event Disclosure - Large Deal Win",
                "doc_type": "SEBI_FILING",
                "date": "2026-06-10",
                "content": "Infosys Limited (NSE: INFY) announces a strategic partnership with a leading European financial services group for a 7-year digital transformation program valued at USD 1.5 billion. The engagement encompasses cloud migration, data modernization, and GenAI-powered customer experience platforms. This win reinforces our leadership in BFSI vertical and demonstrates strong client confidence in our Cobalt cloud capabilities and Topaz AI offerings. The deal will be executed through our European delivery centers with ramp-up over 18 months. Revenue recognition will be ratable over the contract period. This disclosure is made pursuant to Regulation 30 of SEBI (LODR) Regulations, 2015. No material impact on current quarter financials."
            }
        ]
    },
    "ITC": {
        "company_name": "ITC Ltd",
        "documents": [
            {
                "title": "Related Party Transaction Disclosure",
                "doc_type": "SEBI_FILING",
                "date": "2026-05-22",
                "content": "ITC Limited discloses proposed related party transactions for FY2027 aggregate value not exceeding ₹12,500 crores with ITC Infotech India Limited (wholly-owned subsidiary) for IT infrastructure services, software development, and business process services in the ordinary course of business on arm's length basis. Transaction rationale: Leveraging group synergies for digital transformation across FMCG, Hotels, and Paperboards divisions. Pricing benchmarked against leading IT service providers. Independent valuation obtained from KPMG. Audit Committee approved on May 20, 2026. Shareholder approval sought through postal ballot. No promoter interest in the transaction. Disclosure as per Regulation 23 of SEBI (LODR) Regulations."
            }
        ]
    }
}


class DocumentCorpusGenerator:
    """Generate synthetic financial documents for RAG demonstration."""

    def __init__(self):
        self.documents: List[DocumentChunk] = []
        self._generate_corpus()

    def _generate_corpus(self):
        """Generate complete document corpus with chunking."""
        chunk_counter = 0

        # Generate earnings transcripts
        for ticker, data in EARNINGS_TEMPLATES.items():
            for doc in data["documents"]:
                doc_id = f"{ticker}_{doc['quarter'].replace(' ', '_')}"

                for section_idx, section in enumerate(doc["sections"]):
                    chunk_id = f"chunk_{chunk_counter:04d}"
                    chunk_counter += 1

                    self.documents.append(DocumentChunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        ticker=ticker,
                        company_name=data["company_name"],
                        doc_type="EARNINGS_TRANSCRIPT",
                        title=doc["title"],
                        quarter=doc["quarter"],
                        date=doc["date"],
                        content=section,
                        metadata={
                            "sector": data["sector"],
                            "section_index": section_idx,
                            "total_sections": len(doc["sections"])
                        }
                    ))

        # Generate SEBI filings
        for ticker, data in SEBI_FILING_TEMPLATES.items():
            for doc in data["documents"]:
                chunk_id = f"chunk_{chunk_counter:04d}"
                chunk_counter += 1
                doc_id = f"{ticker}_SEBI_{doc['date']}"

                self.documents.append(DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    ticker=ticker,
                    company_name=data["company_name"],
                    doc_type=doc["doc_type"],
                    title=doc["title"],
                    quarter="N/A",
                    date=doc["date"],
                    content=doc["content"],
                    metadata={
                        "filing_type": doc["doc_type"],
                        "regulation": "SEBI_LODR_2015"
                    }
                ))

    def get_all_documents(self) -> List[DocumentChunk]:
        """Get all document chunks."""
        return self.documents

    def get_documents_by_ticker(self, ticker: str) -> List[DocumentChunk]:
        """Get all document chunks for a specific ticker."""
        return [doc for doc in self.documents if doc.ticker == ticker]

    def get_document_summary(self) -> Dict[str, Any]:
        """Get corpus summary statistics."""
        total_chunks = len(self.documents)
        by_type = {}
        by_ticker = {}

        for doc in self.documents:
            by_type[doc.doc_type] = by_type.get(doc.doc_type, 0) + 1
            by_ticker[doc.ticker] = by_ticker.get(doc.ticker, 0) + 1

        return {
            "total_chunks": total_chunks,
            "by_document_type": by_type,
            "by_ticker": by_ticker,
            "tickers": list(by_ticker.keys())
        }


# Global singleton
_corpus_generator = None

def get_document_corpus() -> DocumentCorpusGenerator:
    """Get or create the global document corpus."""
    global _corpus_generator
    if _corpus_generator is None:
        _corpus_generator = DocumentCorpusGenerator()
    return _corpus_generator
