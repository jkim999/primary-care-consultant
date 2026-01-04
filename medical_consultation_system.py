"""
AI Primary Care Consultation System
A 3-agent sequential pipeline for medical consultation with safety mechanisms
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from openai import OpenAI
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Silence verbose HTTP request logging from OpenAI/httpx
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)


class HandoffStatus(Enum):
    EMERGENCY = "EMERGENCY"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


class TrendStatus(Enum):
    BETTER = "better"
    WORSE = "worse"
    STABLE = "stable"


@dataclass
class PatientData:
    """Structure for patient information handoff between agents"""
    handoff_status: str
    exchange_count: int
    chief_complaint: str
    severity: int
    timeline: Dict[str, str]
    symptom_details: Dict[str, str]
    associated_symptoms: List[str]
    red_flags: Dict[str, List[str]]
    patient_concern: str
    relevant_history: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


class MedicalConsultationSystem:
    """Main orchestrator for the 3-agent medical consultation system"""
    
    # Red flags that trigger emergency response
    RED_FLAGS = [
        "chest pain", "chest pressure", "chest tightness",
        "difficulty breathing", "shortness of breath", "can't breathe",
        "severe pain", "worst headache", "sudden severe headache",
        "confusion", "slurred speech", "one-sided weakness",
        "heavy bleeding", "suicidal", "suicide"
    ]
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """Initialize the consultation system with OpenAI API"""
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.conversation_history = []
        self.patient_data = None
        
    def check_for_red_flags(self, text: str) -> List[str]:
        """Check if text contains any red flag symptoms"""
        text_lower = text.lower()
        detected_flags = []
        
        for flag in self.RED_FLAGS:
            if flag in text_lower:
                detected_flags.append(flag)
                
        # Check for high pain severity
        pain_match = re.search(r'\b([8-9]|10)\s*(?:\/10|out of 10)?\b', text_lower)
        if pain_match:
            detected_flags.append(f"severe pain ({pain_match.group(0)})")
            
        return detected_flags
    
    def call_llm(self, system_prompt: str, user_message: str, temperature: float = 0.7) -> str:
        """Call OpenAI API with error handling"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise
    
    def history_agent(self, patient_input: str, exchange_count: int = 1) -> Tuple[str, Optional[Dict]]:
        """
        Agent 1: History-Taking Agent
        Gathers symptom information with bounded questioning
        """
        
        # Check for immediate red flags
        red_flags = self.check_for_red_flags(patient_input)
        
        system_prompt = """You are a medical history-taking assistant. Your job is to gather symptom information efficiently.

REQUIRED QUESTIONS (must ask if not yet answered):
Chief complaint: "What are your symptoms?"
Timeline: "When did this first start, and has it been getting better, worse, or staying the same?"
Severity: "Rate your discomfort/pain from 1-10"
Patient concern: "What concerns you most about this?"

RULES:
- Maximum 5 total exchanges before handoff
- Maximum 2 clarifying follow-ups per topic
- Be energetic, friendly, and helpful
- Monitor for red flags continuously, and if any are detected, handoff immediately.

RED FLAGS (immediate handoff):
- Chest pain/pressure/tightness
- Difficulty breathing
- Severe pain (8+/10)
- Sudden severe headache/"worst headache ever"
- Confusion, slurred speech, one-sided weakness
- Heavy bleeding
- Suicidal ideation

If exchange_count >= 5 or all required info gathered or red flag detected, output:
JSON_HANDOFF:
{
  "handoff_status": "EMERGENCY" | "COMPLETE" | "INCOMPLETE",
  "exchange_count": <number>,
  "chief_complaint": "<complaint>",
  "severity": <1-10>,
  "timeline": {
    "started": "<when>",
    "trend": "better" | "worse" | "stable"
  },
  "symptom_details": {
    "location": "<where>",
    "quality": "<description>",
    "characteristics": "<details>"
  },
  "associated_symptoms": ["<symptom1>", "<symptom2>"],
  "red_flags": {
    "present": ["<flag1>"],
    "ruled_out": ["<flag2>"]
  },
  "patient_concern": "<concern>",
  "relevant_history": "<history>"
}

Otherwise, ask the next most important question."""

        # Build conversation context
        context = f"Exchange {exchange_count}:\nPatient: {patient_input}\n"
        if self.conversation_history:
            context = "Previous exchanges:\n" + "\n".join(self.conversation_history) + "\n" + context
        
        # Add red flag context if detected
        if red_flags:
            context += f"\nWARNING: Red flags detected: {', '.join(red_flags)}"
        
        # Add exchange count warning
        if exchange_count >= 4:
            context += f"\nNOTE: This is exchange {exchange_count} of maximum 5. Prepare for handoff."
        
        response = self.call_llm(system_prompt, context)
        
        # Check if JSON handoff is in response
        if "JSON_HANDOFF:" in response:
            try:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                patient_data = json.loads(json_str)
                
                # Ensure red flags are included if detected
                if red_flags and not patient_data.get("red_flags", {}).get("present"):
                    patient_data["red_flags"] = {"present": red_flags, "ruled_out": []}
                    patient_data["handoff_status"] = "EMERGENCY"
                
                return None, patient_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                # Create emergency handoff on parse error
                return None, {
                    "handoff_status": "INCOMPLETE",
                    "exchange_count": exchange_count,
                    "chief_complaint": patient_input[:100],
                    "severity": 5,
                    "patient_concern": "Unable to parse complete history",
                    "red_flags": {"present": red_flags, "ruled_out": []}
                }
        else:
            # Extract the question from response
            question = response.strip()
            return question, None
    
    def decision_agent(self, patient_data: Dict) -> str:
        """
        Agent 2: Triage & Decision Agent
        Parses JSON, assesses risk, decides treat vs. escalate
        """
        
        system_prompt = """You are a medical triage and decision assistant. Parse the patient data and make treatment decisions.

DECISION LOGIC:
1. IF handoff_status == "EMERGENCY" → Generate escalation (Call 911/ER/urgent care)
2. IF handoff_status == "INCOMPLETE" OR uncertain diagnosis → Conservative escalation (see doctor within X hours/days)
3. IF mild symptoms, no red flags → Generate 3-step treatment plan

TREATMENT OUTPUT FORMAT:
1. [First self-care recommendation]
2. [Second self-care recommendation]
3. [Third self-care recommendation]

"If this isn't improving in [X] days, please contact your doctor."
"I can provide guidance, but I cannot replace an in-person examination."
"How does this sound to you?"

ESCALATION OUTPUT FORMAT:
"Based on what you've told me, [assessment]. This is beyond what I can safely assess remotely. Here's what I recommend: [specific action with timeframe]."

Conservative bias: When uncertain, default to escalation."""

        user_message = f"Patient data:\n{json.dumps(patient_data, indent=2)}\n\nProvide appropriate response based on the decision logic."
        
        response = self.call_llm(system_prompt, user_message, temperature=0.3)
        return response
    
    def communication_agent(self, decision_output: str) -> str:
        """
        Agent 3: Communication Agent
        Applies linguistic and empathy requirements to Agent 2's output
        """
        
        system_prompt = """You are a medical communication specialist. Transform the medical response to be more empathetic and clear.

REQUIRED TRANSFORMATIONS:
You do not have to include all of these in your response, only transform if conditions are met.
- "I see" / "I hear" → "I understand"
- Medical jargon → lay terms (e.g., "hypertension" → "high blood pressure")
- When worry expressed → "It's completely understandable that you're concerned about [specific symptom]"
- When pain described → "That sounds really uncomfortable"
- Never say "don't worry" → use "let's work through this together"

MAINTAIN:
- All clinical content and safety language
- The structure and recommendations
- Required phrases: "I can provide guidance, but I cannot replace an in-person examination" and "How does this sound to you?"

Only modify communication style and word choice, not medical content."""

        user_message = f"Transform this medical response:\n{decision_output}"
        
        response = self.call_llm(system_prompt, user_message, temperature=0.5)
        return response
    
    def process_consultation(self, initial_complaint: str) -> str:
        """
        Main orchestration method for the entire consultation process
        """
        logger.info("Starting consultation process")
        self.conversation_history = []
        exchange_count = 1
        current_input = initial_complaint
        
        # Phase 1: History Taking (up to 5 exchanges)
        while exchange_count <= 5:
            logger.info(f"History Agent - Exchange {exchange_count}")
            
            # Store the exchange
            self.conversation_history.append(f"Patient: {current_input}")
            
            # Process through history agent
            question, patient_data = self.history_agent(current_input, exchange_count)
            
            if patient_data:
                # Handoff triggered
                logger.info(f"Handoff triggered: {patient_data.get('handoff_status')}")
                self.patient_data = patient_data
                break
            elif question:
                # Continue conversation
                self.conversation_history.append(f"Assistant: {question}")
                print(f"\nAssistant: {question}")
                
                # Get next patient input (in production, this would come from user)
                current_input = input("Patient: ")
                exchange_count += 1
            
            # Force handoff at exchange 5
            if exchange_count > 5 and not patient_data:
                logger.warning("Forcing handoff at exchange limit")
                patient_data = {
                    "handoff_status": "INCOMPLETE",
                    "exchange_count": 5,
                    "chief_complaint": initial_complaint,
                    "severity": 5,
                    "timeline": {"started": "unknown", "trend": "stable"},
                    "symptom_details": {},
                    "associated_symptoms": [],
                    "red_flags": {"present": [], "ruled_out": []},
                    "patient_concern": "Unable to complete assessment",
                    "relevant_history": ""
                }
                self.patient_data = patient_data
                break
        
        # Phase 2: Decision Making
        logger.info("Decision Agent processing")
        decision_output = self.decision_agent(self.patient_data)
        logger.info(f"Decision: {decision_output[:100]}...")
        
        # Phase 3: Communication Enhancement
        logger.info("Communication Agent processing")
        final_response = self.communication_agent(decision_output)
        
        # Log the complete consultation
        self.log_consultation(final_response)
        
        return final_response
    
    def log_consultation(self, final_response: str):
        """Log the consultation for audit purposes"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "patient_data": self.patient_data,
            "conversation_history": self.conversation_history,
            "final_response": final_response
        }
        
        # In production, save to database or file
        logger.info(f"Consultation logged: {log_entry['timestamp']}")
        
        # Save to file
        with open("consultation_log.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")


def main():
    """Main execution function with example usage"""
    
    # Initialize system (replace with your actual API key)
    API_KEY = "your-openai-api-key-here"
    system = MedicalConsultationSystem(API_KEY)
    
    print("=" * 50)
    print("AI Primary Care Consultation System")
    print("=" * 50)
    print("\nPlease describe what brings you in today.")
    print("(Type 'quit' to exit)\n")
    
    while True:
        initial_complaint = input("Patient: ")
        
        if initial_complaint.lower() == 'quit':
            print("Thank you for using the consultation system. Goodbye!")
            break
        
        try:
            # Process the consultation
            final_response = system.process_consultation(initial_complaint)
            
            print("\n" + "=" * 50)
            print("FINAL RESPONSE:")
            print("=" * 50)
            print(final_response)
            print("=" * 50 + "\n")
            
        except Exception as e:
            logger.error(f"Consultation error: {e}")
            print(f"\nAn error occurred: {e}")
            print("Please try again or contact support if the issue persists.\n")
        
        print("\nWould you like to start a new consultation? (yes/no)")
        if input().lower() != 'yes':
            break
    
    print("\nThank you for using the AI Primary Care Consultation System.")


if __name__ == "__main__":
    main()
