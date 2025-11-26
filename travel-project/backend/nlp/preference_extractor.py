import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class PreferenceExtractor:
    def __init__(self):
        self.category_keywords = {
            'religious': ['temple', 'church', 'mosque', 'gurudwara', 'shrine', 'monastery', 'religious', 'spiritual', 'pilgrimage', 'mandir', 'masjid'],
            'beach': ['beach', 'sea', 'ocean', 'coast', 'shore', 'island', 'samudra'],
            'historical': ['historical', 'monument', 'fort', 'palace', 'heritage', 'ancient', 'ruins', 'museum', 'qila', 'mahal'],
            'nature': ['nature', 'park', 'wildlife', 'forest', 'mountain', 'hill', 'valley', 'waterfall', 'lake', 'garden', 'trek', 'hiking'],
            'adventure': ['adventure', 'trekking', 'rafting', 'paragliding', 'camping', 'rock climbing', 'skiing', 'diving'],
            'cultural': ['cultural', 'art', 'dance', 'music', 'festival', 'local', 'traditional', 'folk'],
            'food': ['food', 'cuisine', 'restaurant', 'street food', 'local food', 'culinary']
        }
        
        self.budget_keywords = {
            'low': ['budget', 'cheap', 'affordable', 'economical', 'low cost'],
            'medium': ['moderate', 'medium', 'reasonable'],
            'high': ['luxury', 'premium', 'expensive', 'high end', 'lavish']
        }
    
    def extract_categories(self, text):
        """Extract attraction categories from text"""
        text_lower = text.lower()
        found_categories = []
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if category not in found_categories:
                        found_categories.append(category)
                    break
        
        return found_categories if found_categories else ['general']
    
    def extract_budget(self, text):
        """Extract budget preference"""
        text_lower = text.lower()
        
        for budget_level, keywords in self.budget_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return budget_level
        
        # Extract numeric budget
        numbers = re.findall(r'\d+', text)
        if numbers:
            budget_amount = int(numbers[0])
            if budget_amount < 10000:
                return 'low'
            elif budget_amount < 50000:
                return 'medium'
            else:
                return 'high'
        
        return 'medium'
    
    def extract_duration(self, text):
        """Extract trip duration in days"""
        patterns = [
            r'(\d+)\s*days?',
            r'(\d+)\s*day',
            r'(\d+)\s*din',  # Hindi
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        return 3  # Default duration