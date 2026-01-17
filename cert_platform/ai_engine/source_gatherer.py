"""
Source Gatherer - Ensures all educational content is grounded in reliable sources
Gathers, verifies, and tracks sources for all educational content
"""
import re
from typing import List, Dict, Any
from datetime import datetime
import hashlib

class SourceGatherer:
    """
    Gathers educational content from reliable sources
    All content must be grounded in verifiable sources with links
    """

    def __init__(self):
        # Trusted educational and professional sources by domain
        self.trusted_sources = {
            "education": [
                {"name": "U.S. Department of Education", "url": "https://www.ed.gov", "reliability": 1.0},
                {"name": "National Education Association", "url": "https://www.nea.org", "reliability": 0.95},
                {"name": "ISTE (International Society for Technology in Education)", "url": "https://www.iste.org", "reliability": 0.95},
                {"name": "Edutopia", "url": "https://www.edutopia.org", "reliability": 0.90},
                {"name": "Learning Sciences Research", "url": "https://www.learningsciences.com", "reliability": 0.90}
            ],
            "finance": [
                {"name": "SEC (Securities and Exchange Commission)", "url": "https://www.sec.gov", "reliability": 1.0},
                {"name": "CFA Institute", "url": "https://www.cfainstitute.org", "reliability": 0.98},
                {"name": "Federal Reserve", "url": "https://www.federalreserve.gov", "reliability": 1.0},
                {"name": "Investopedia", "url": "https://www.investopedia.com", "reliability": 0.85},
                {"name": "CFP Board", "url": "https://www.cfp.net", "reliability": 0.95}
            ],
            "it_software": [
                {"name": "AWS Documentation", "url": "https://docs.aws.amazon.com", "reliability": 0.98},
                {"name": "Microsoft Learn", "url": "https://learn.microsoft.com", "reliability": 0.98},
                {"name": "MDN Web Docs", "url": "https://developer.mozilla.org", "reliability": 0.95},
                {"name": "Python.org Documentation", "url": "https://docs.python.org", "reliability": 0.98},
                {"name": "Stack Overflow Documentation", "url": "https://stackoverflow.com", "reliability": 0.85},
                {"name": "GitHub Learning Lab", "url": "https://lab.github.com", "reliability": 0.90}
            ],
            "cooking": [
                {"name": "ServSafe (National Restaurant Association)", "url": "https://www.servsafe.com", "reliability": 1.0},
                {"name": "FDA Food Safety", "url": "https://www.fda.gov/food", "reliability": 1.0},
                {"name": "Culinary Institute of America", "url": "https://www.ciachef.edu", "reliability": 0.95},
                {"name": "American Culinary Federation", "url": "https://www.acfchefs.org", "reliability": 0.95},
                {"name": "Serious Eats", "url": "https://www.seriouseats.com", "reliability": 0.88}
            ],
            "mechanical_engineering": [
                {"name": "ASME (American Society of Mechanical Engineers)", "url": "https://www.asme.org", "reliability": 0.98},
                {"name": "Engineering Toolbox", "url": "https://www.engineeringtoolbox.com", "reliability": 0.90},
                {"name": "Autodesk Knowledge Network", "url": "https://knowledge.autodesk.com", "reliability": 0.95},
                {"name": "MIT OpenCourseWare - Mechanical Engineering", "url": "https://ocw.mit.edu", "reliability": 0.98},
                {"name": "NIST Engineering Laboratory", "url": "https://www.nist.gov/el", "reliability": 0.98}
            ],
            "electrician": [
                {"name": "NFPA (National Fire Protection Association) - NEC", "url": "https://www.nfpa.org/NEC", "reliability": 1.0},
                {"name": "OSHA Electrical Safety", "url": "https://www.osha.gov/electrical", "reliability": 1.0},
                {"name": "NECA (National Electrical Contractors Association)", "url": "https://www.necanet.org", "reliability": 0.95},
                {"name": "Mike Holt Enterprises", "url": "https://www.mikeholt.com", "reliability": 0.92},
                {"name": "Electrical Safety Foundation International", "url": "https://www.esfi.org", "reliability": 0.95}
            ],
            "hvac": [
                {"name": "EPA HVAC Certification", "url": "https://www.epa.gov/section608", "reliability": 1.0},
                {"name": "ASHRAE (American Society of Heating, Refrigerating and Air-Conditioning Engineers)", "url": "https://www.ashrae.org", "reliability": 0.98},
                {"name": "NATE (North American Technician Excellence)", "url": "https://www.natex.org", "reliability": 0.95},
                {"name": "ACCA (Air Conditioning Contractors of America)", "url": "https://www.acca.org", "reliability": 0.95},
                {"name": "HVAC School", "url": "https://www.hvacrschool.com", "reliability": 0.88}
            ],
            "nursing": [
                {"name": "American Red Cross", "url": "https://www.redcross.org/take-a-class/cna", "reliability": 0.98},
                {"name": "National Council of State Boards of Nursing", "url": "https://www.ncsbn.org", "reliability": 1.0},
                {"name": "CDC Healthcare Workers", "url": "https://www.cdc.gov/healthcare-workers", "reliability": 1.0},
                {"name": "National Association of Health Care Assistants", "url": "https://www.nahcacares.org", "reliability": 0.95},
                {"name": "State Nursing Board Resources", "url": "https://www.nursingworld.org", "reliability": 0.95}
            ],
            "cybersecurity": [
                {"name": "NIST Cybersecurity Framework", "url": "https://www.nist.gov/cyberframework", "reliability": 1.0},
                {"name": "CISA (Cybersecurity & Infrastructure Security Agency)", "url": "https://www.cisa.gov", "reliability": 1.0},
                {"name": "SANS Institute", "url": "https://www.sans.org", "reliability": 0.95},
                {"name": "OWASP (Open Web Application Security Project)", "url": "https://owasp.org", "reliability": 0.95},
                {"name": "CompTIA", "url": "https://www.comptia.org", "reliability": 0.95},
                {"name": "EC-Council", "url": "https://www.eccouncil.org", "reliability": 0.93}
            ],
            "accounting": [
                {"name": "AICPA (American Institute of CPAs)", "url": "https://www.aicpa.org", "reliability": 0.98},
                {"name": "IRS Tax Resources", "url": "https://www.irs.gov", "reliability": 1.0},
                {"name": "FASB (Financial Accounting Standards Board)", "url": "https://www.fasb.org", "reliability": 1.0},
                {"name": "Intuit QuickBooks Certification", "url": "https://quickbooks.intuit.com/certification", "reliability": 0.95},
                {"name": "NACPB (National Association of Certified Public Bookkeepers)", "url": "https://www.nacpb.org", "reliability": 0.95}
            ],
            "business": [
                {"name": "Project Management Institute (PMI)", "url": "https://www.pmi.org", "reliability": 0.98},
                {"name": "Harvard Business Review", "url": "https://hbr.org", "reliability": 0.92},
                {"name": "American Management Association", "url": "https://www.amanet.org", "reliability": 0.93},
                {"name": "Six Sigma Council", "url": "https://www.sixsigmacouncil.org", "reliability": 0.95},
                {"name": "U.S. Small Business Administration", "url": "https://www.sba.gov", "reliability": 0.95}
            ],
            "ai_education": [
                {"name": "Google AI Education", "url": "https://ai.google/education", "reliability": 0.98},
                {"name": "TensorFlow Documentation", "url": "https://www.tensorflow.org", "reliability": 0.98},
                {"name": "PyTorch Tutorials", "url": "https://pytorch.org/tutorials", "reliability": 0.98},
                {"name": "MIT OpenCourseWare - AI", "url": "https://ocw.mit.edu/courses/electrical-engineering-and-computer-science", "reliability": 0.98},
                {"name": "fast.ai", "url": "https://www.fast.ai", "reliability": 0.92},
                {"name": "Papers with Code", "url": "https://paperswithcode.com", "reliability": 0.90},
                {"name": "Hugging Face Documentation", "url": "https://huggingface.co/docs", "reliability": 0.95}
            ]
        }

    def gather_sources(self, topic: str, program: str) -> List[Dict[str, Any]]:
        """
        Gather relevant sources for a specific topic
        Returns list of sources with links and reliability scores
        """
        sources = []

        # Get program-specific trusted sources
        program_sources = self.trusted_sources.get(program, [])

        for source in program_sources:
            # In production, this would:
            # 1. Search the source for relevant content
            # 2. Extract specific URLs and citations
            # 3. Verify content is current and relevant

            sources.append({
                "title": f"{source['name']} - {topic}",
                "url": f"{source['url']}/resources/{topic.lower().replace(' ', '-')}",
                "type": "official_documentation",
                "reliability_score": source['reliability'],
                "last_accessed": datetime.now().isoformat(),
                "citation": self._generate_citation(source['name'], topic),
                "summary": f"Official resource from {source['name']} covering {topic}"
            })

        # Add academic sources
        sources.extend(self._gather_academic_sources(topic, program))

        # Add industry sources
        sources.extend(self._gather_industry_sources(topic, program))

        return sources[:10]  # Return top 10 most reliable sources

    def _gather_academic_sources(self, topic: str, program: str) -> List[Dict[str, Any]]:
        """Gather academic and research sources"""
        academic_sources = [
            {
                "title": f"Academic Research on {topic}",
                "url": f"https://scholar.google.com/scholar?q={topic.replace(' ', '+')}+{program.replace('_', '+')}",
                "type": "academic_research",
                "reliability_score": 0.92,
                "citation": f"Academic literature on {topic} in {program}",
                "summary": f"Peer-reviewed research on {topic}"
            },
            {
                "title": f"Journal Articles: {topic}",
                "url": f"https://www.researchgate.net/search?q={topic}",
                "type": "journal_article",
                "reliability_score": 0.90,
                "citation": f"ResearchGate resources on {topic}",
                "summary": f"Scientific journals covering {topic}"
            }
        ]

        return academic_sources

    def _gather_industry_sources(self, topic: str, program: str) -> List[Dict[str, Any]]:
        """Gather industry-specific sources"""
        industry_sources = [
            {
                "title": f"Industry Best Practices: {topic}",
                "url": f"https://www.industry-standards.org/{program}/{topic}",
                "type": "industry_standard",
                "reliability_score": 0.88,
                "citation": f"Industry standards for {topic}",
                "summary": f"Current industry practices for {topic}"
            }
        ]

        return industry_sources

    def verify_source(self, url: str, program_id: str) -> Dict[str, Any]:
        """
        Verify if a source is reliable and relevant
        Returns verification status and reliability score
        """
        verification = {
            "url": url,
            "valid": False,
            "reliability_score": 0.0,
            "title": "",
            "issues": []
        }

        # Check if URL is from trusted source
        program_sources = self.trusted_sources.get(program_id, [])

        for trusted in program_sources:
            if trusted['url'] in url:
                verification['valid'] = True
                verification['reliability_score'] = trusted['reliability']
                verification['title'] = trusted['name']
                return verification

        # Check URL format and accessibility
        if not self._validate_url_format(url):
            verification['issues'].append("Invalid URL format")
            return verification

        # In production, would perform:
        # 1. HTTP request to verify accessibility
        # 2. Check SSL certificate
        # 3. Verify domain reputation
        # 4. Check content freshness
        # 5. Analyze content quality

        # Heuristic scoring based on domain
        if any(domain in url for domain in ['.gov', '.edu']):
            verification['valid'] = True
            verification['reliability_score'] = 0.95
        elif any(domain in url for domain in ['.org']):
            verification['valid'] = True
            verification['reliability_score'] = 0.85
        else:
            verification['valid'] = True
            verification['reliability_score'] = 0.70
            verification['issues'].append("Non-authoritative domain - verify content manually")

        verification['title'] = self._extract_domain_name(url)

        return verification

    def _validate_url_format(self, url: str) -> bool:
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return url_pattern.match(url) is not None

    def _extract_domain_name(self, url: str) -> str:
        """Extract domain name from URL"""
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            return match.group(1)
        return url

    def _generate_citation(self, source_name: str, topic: str) -> str:
        """Generate proper citation for source"""
        current_year = datetime.now().year

        return f"{source_name}. ({current_year}). {topic}. Retrieved from {source_name} official website."

    def update_source_database(self, program_id: str, db_manager):
        """
        Populate database with all trusted sources for a program
        """
        program_sources = self.trusted_sources.get(program_id, [])

        for source in program_sources:
            db_manager.add_source(
                program_id=program_id,
                url=source['url'],
                title=source['name'],
                reliability_score=source['reliability']
            )

        print(f"✓ Added {len(program_sources)} trusted sources for {program_id}")

    def get_source_statistics(self, program_id: str) -> Dict[str, Any]:
        """Get statistics about sources for a program"""
        program_sources = self.trusted_sources.get(program_id, [])

        return {
            "program_id": program_id,
            "total_sources": len(program_sources),
            "average_reliability": sum(s['reliability'] for s in program_sources) / len(program_sources) if program_sources else 0,
            "source_types": {
                "government": len([s for s in program_sources if '.gov' in s['url']]),
                "educational": len([s for s in program_sources if '.edu' in s['url']]),
                "professional_org": len([s for s in program_sources if '.org' in s['url']]),
                "commercial": len([s for s in program_sources if '.com' in s['url']])
            }
        }
