"""
Configuration file for AI Primary Care Consultation System
"""

import os
from typing import List, Dict

class Config:
    """Configuration settings for the medical consultation system"""
    
    # Supported OpenAI models for this project
    AVAILABLE_MODELS = [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4",
        "gpt-3.5-turbo",
    ]

    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
    MODEL_NAME = "gpt-4o-mini"
    
    # System Limits
    MAX_EXCHANGES = 5
    MAX_CLARIFICATIONS_PER_TOPIC = 2
    
    # Temperature settings for different agents
    TEMPERATURE_SETTINGS = {
        "history_agent": 0.7,
        "decision_agent": 0.3,  # Lower for more consistent medical decisions
        "communication_agent": 0.5
    }
    
    # Red Flags - Critical symptoms requiring immediate attention
    RED_FLAGS = [
        # Cardiac
        "chest pain", "chest pressure", "chest tightness", "heart attack",
        "irregular heartbeat", "rapid heartbeat",
        
        # Respiratory
        "difficulty breathing", "shortness of breath", "can't breathe",
        "choking", "severe wheezing",
        
        # Neurological
        "severe headache", "worst headache", "sudden severe headache",
        "confusion", "slurred speech", "one-sided weakness",
        "seizure", "loss of consciousness", "fainting",
        "vision loss", "double vision",
        
        # Bleeding
        "heavy bleeding", "uncontrolled bleeding", "vomiting blood",
        "blood in stool", "coughing blood",
        
        # Mental Health Emergency
        "suicidal", "suicide", "want to die", "harm myself",
        "harm others", "homicidal",
        
        # Severe Pain
        "severe pain", "unbearable pain", "10 out of 10 pain",
        "8 out of 10 pain", "9 out of 10 pain",
        
        # Other Emergencies
        "overdose", "poisoning", "severe allergic reaction",
        "anaphylaxis", "severe burn", "severe injury"
    ]
    
    # Required questions for history taking
    REQUIRED_QUESTIONS = {
        "chief_complaint": "What brings you in today?",
        "timeline": "When did this first start, and has it been getting better, worse, or staying the same?",
        "severity": "On a scale of 1 to 10, how would you rate your discomfort or pain?",
        "patient_concern": "What concerns you most about this?"
    }
    
    # Escalation timeframes based on urgency
    ESCALATION_TIMEFRAMES = {
        "emergency": "Call 911 immediately",
        "urgent": "Go to the emergency room immediately",
        "semi_urgent": "See a doctor within 24 hours",
        "routine_urgent": "Schedule an appointment within 2-3 days",
        "routine": "Schedule an appointment within 1-2 weeks"
    }
    
    # Communication replacements for empathetic response
    COMMUNICATION_REPLACEMENTS = {
        "I see": "I understand",
        "I hear": "I understand",
        "don't worry": "let's work through this together",
        "calm down": "I can see this is concerning",
        
        # Medical jargon to lay terms
        "hypertension": "high blood pressure",
        "hypotension": "low blood pressure",
        "tachycardia": "rapid heart rate",
        "bradycardia": "slow heart rate",
        "dyspnea": "difficulty breathing",
        "edema": "swelling",
        "erythema": "redness",
        "pruritus": "itching",
        "vertigo": "dizziness",
        "syncope": "fainting",
        "pyrexia": "fever",
        "analgesic": "pain reliever",
        "antipyretic": "fever reducer",
        "antiemetic": "anti-nausea medication",
        "antihistamine": "allergy medication",
        "NSAID": "anti-inflammatory pain reliever",
        "OTC": "over-the-counter",
        "prn": "as needed",
        "tid": "three times a day",
        "bid": "twice a day",
        "qd": "once daily"
    }
    
    # Required phrases in final output
    REQUIRED_PHRASES = [
        "I can provide guidance, but I cannot replace an in-person examination.",
        "How does this sound to you?"
    ]
    
    # Empathy phrases for different situations
    EMPATHY_PHRASES = {
        "pain": "That sounds really uncomfortable",
        "worry": "It's completely understandable that you're concerned about",
        "fear": "I can understand why this would be frightening",
        "frustration": "I understand this must be frustrating",
        "exhaustion": "That sounds exhausting to deal with"
    }
    
    # Self-care recommendations database
    SELF_CARE_TEMPLATES = {
        "headache": [
            "Rest in a quiet, dark room for 20-30 minutes",
            "Apply a cold compress to your forehead or temples",
            "Stay well-hydrated by drinking water regularly",
            "Practice gentle neck stretches and relaxation techniques",
            "Take over-the-counter pain relievers as directed on the package"
        ],
        "cold_flu": [
            "Get plenty of rest - aim for 8-10 hours of sleep",
            "Stay hydrated with warm fluids like tea or soup",
            "Use a humidifier to ease congestion",
            "Take over-the-counter medications for symptom relief as directed",
            "Wash hands frequently and avoid close contact with others"
        ],
        "minor_cut": [
            "Clean the wound gently with soap and water",
            "Apply antibiotic ointment and cover with a clean bandage",
            "Keep the wound dry and change bandages daily",
            "Watch for signs of infection (increased redness, warmth, pus)",
            "Ensure tetanus vaccination is up to date"
        ],
        "upset_stomach": [
            "Stick to bland foods (BRAT diet: bananas, rice, applesauce, toast)",
            "Stay hydrated with small, frequent sips of clear fluids",
            "Avoid dairy, caffeine, alcohol, and fatty foods",
            "Rest and avoid strenuous activity",
            "Consider over-the-counter antacids if appropriate"
        ],
        "minor_sprain": [
            "Follow the RICE protocol: Rest, Ice, Compression, Elevation",
            "Apply ice for 20 minutes every 2-3 hours for the first 48 hours",
            "Use an elastic bandage for compression, ensuring it's not too tight",
            "Keep the injured area elevated above heart level when possible",
            "Take over-the-counter pain relievers as directed"
        ]
    }
    
    # Logging configuration
    LOG_LEVEL = "INFO"
    LOG_FILE = "consultation_log.json"
    AUDIT_LOG_FILE = "audit_log.json"
    
    # Safety settings
    CONSERVATIVE_MODE = True  # When True, errs on side of escalation
    REQUIRE_CONFIRMATION = True  # Require user confirmation for emergency escalations
    
    # Response formatting
    MAX_RESPONSE_LENGTH = 500  # Maximum words in final response
    USE_NUMBERED_LISTS = True  # Use numbered lists for recommendations
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        if cls.OPENAI_API_KEY == "your-api-key-here":
            raise ValueError("Please set your OpenAI API key in the configuration")
        
        if cls.MAX_EXCHANGES < 3:
            raise ValueError("MAX_EXCHANGES must be at least 3")
        
        if cls.MODEL_NAME not in cls.AVAILABLE_MODELS:
            raise ValueError("Invalid model name")
        
        return True
    
    @classmethod
    def get_red_flag_categories(cls) -> Dict[str, List[str]]:
        """Organize red flags by category for better processing"""
        return {
            "cardiac": [f for f in cls.RED_FLAGS if any(word in f for word in ["chest", "heart"])],
            "respiratory": [f for f in cls.RED_FLAGS if any(word in f for word in ["breath", "choking", "wheez"])],
            "neurological": [f for f in cls.RED_FLAGS if any(word in f for word in ["headache", "confusion", "speech", "seizure", "vision"])],
            "bleeding": [f for f in cls.RED_FLAGS if "blood" in f or "bleeding" in f],
            "mental_health": [f for f in cls.RED_FLAGS if any(word in f for word in ["suicid", "harm", "homicid"])],
            "severe_pain": [f for f in cls.RED_FLAGS if "pain" in f],
            "other": [f for f in cls.RED_FLAGS if any(word in f for word in ["overdose", "poison", "allergic", "burn", "injury"])]
        }


# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration"""
    LOG_LEVEL = "DEBUG"
    CONSERVATIVE_MODE = True
    REQUIRE_CONFIRMATION = False


class ProductionConfig(Config):
    """Production environment configuration"""
    LOG_LEVEL = "WARNING"
    CONSERVATIVE_MODE = True
    REQUIRE_CONFIRMATION = True
    MODEL_NAME = "gpt-4o"


class TestConfig(Config):
    """Test environment configuration"""
    LOG_LEVEL = "DEBUG"
    MAX_EXCHANGES = 3  # Shorter for testing
    REQUIRE_CONFIRMATION = False


def get_config(environment: str = "development") -> Config:
    """Get configuration based on environment"""
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "test": TestConfig
    }
    
    config_class = configs.get(environment.lower(), DevelopmentConfig)
    config_class.validate_config()
    return config_class
