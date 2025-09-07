import json
import os
import random
from typing import List, Dict, Optional

class MythsFactsService:
    _data = None

    @classmethod
    def _load_data(cls):
        """Load myths and facts data from JSON file."""
        if cls._data is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'myths_facts.json')
            try:
                with open(data_path, 'r', encoding='utf-8') as f:
                    cls._data = json.load(f)
            except FileNotFoundError:
                cls._data = {"mental_health_myths": [], "depression_myths": [], "anxiety_myths": [], "student_myths": [], "hindi_myths": []}
        return cls._data

    @staticmethod
    def get_myths_facts(category: Optional[str] = None, language: str = 'en', limit: int = 10) -> List[Dict]:
        """Get myths and facts, optionally filtered by category and language."""
        data = MythsFactsService._load_data()
        all_myths = []

        # Collect myths from all categories or specific category
        if category:
            category_key = f"{category}_myths"
            if category_key in data:
                all_myths = data[category_key]
        else:
            # Get from all categories
            for category_data in data.values():
                if isinstance(category_data, list):
                    all_myths.extend(category_data)

        # Filter by language
        filtered_myths = [myth for myth in all_myths if myth.get('language', 'en') == language]

        # Shuffle and limit results
        if filtered_myths:
            random.shuffle(filtered_myths)
            return filtered_myths[:limit]

        return []

    @staticmethod
    def get_random_myth_fact(language: str = 'en') -> Optional[Dict]:
        """Get a random myth and fact."""
        myths = MythsFactsService.get_myths_facts(language=language, limit=100)
        if myths:
            return random.choice(myths)
        return None

    @staticmethod
    def get_categories() -> List[str]:
        """Get available myth/fact categories."""
        data = MythsFactsService._load_data()
        categories = []
        for key in data.keys():
            if key.endswith('_myths'):
                category = key.replace('_myths', '')
                categories.append(category)
        return categories

    @staticmethod
    def search_myths_facts(query: str, language: str = 'en') -> List[Dict]:
        """Search myths and facts by keyword."""
        data = MythsFactsService._load_data()
        results = []
        query_lower = query.lower()

        for category_data in data.values():
            if isinstance(category_data, list):
                for myth in category_data:
                    if myth.get('language', 'en') == language:
                        myth_text = myth.get('myth', '').lower()
                        fact_text = myth.get('fact', '').lower()
                        category_text = myth.get('category', '').lower()

                        if (query_lower in myth_text or
                            query_lower in fact_text or
                            query_lower in category_text):
                            results.append(myth)

        return results

    @staticmethod
    def get_myth_fact_by_id(myth_id: str) -> Optional[Dict]:
        """Get a specific myth/fact by ID (if implemented)."""
        # For now, return random myth since we don't have IDs
        return MythsFactsService.get_random_myth_fact()

    @staticmethod
    def get_popular_myths(language: str = 'en') -> List[Dict]:
        """Get most commonly searched or viewed myths."""
        # For now, return a curated selection of important myths
        data = MythsFactsService._load_data()
        popular_categories = ['mental_health_myths', 'stigma', 'treatment']

        popular_myths = []
        for category in popular_categories:
            if category in data:
                category_myths = [myth for myth in data[category]
                                if myth.get('language', 'en') == language]
                popular_myths.extend(category_myths[:3])  # Top 3 from each category

        random.shuffle(popular_myths)
        return popular_myths[:9]  # Return 9 popular myths

    @staticmethod
    def get_myths_by_stigma_level(language: str = 'en') -> Dict[str, List[Dict]]:
        """Get myths organized by stigma level (high, medium, low impact)."""
        data = MythsFactsService._load_data()
        stigma_levels = {
            'high_impact': [],
            'medium_impact': [],
            'low_impact': []
        }

        # Define high-impact stigma myths
        high_impact_keywords = ['dangerous', 'weakness', 'crazy', 'violent', 'sign of weakness']
        medium_impact_keywords = ['rare', 'willpower', 'personality', 'forever']
        low_impact_keywords = ['adult', 'talking', 'days off']

        for category_data in data.values():
            if isinstance(category_data, list):
                for myth in category_data:
                    if myth.get('language', 'en') == language:
                        myth_text = myth.get('myth', '').lower()

                        if any(keyword in myth_text for keyword in high_impact_keywords):
                            stigma_levels['high_impact'].append(myth)
                        elif any(keyword in myth_text for keyword in medium_impact_keywords):
                            stigma_levels['medium_impact'].append(myth)
                        elif any(keyword in myth_text for keyword in low_impact_keywords):
                            stigma_levels['low_impact'].append(myth)

        return stigma_levels
